"""Application service layer: orchestrates domain logic, policy, persistence and evidence."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from .ai.explainer import Explainer
from .ai.guard import sanitize_untrusted
from .clock import Clock
from .config import Settings
from .domain import risk
from .domain.fx import RateTable, usd_equivalent
from .domain.money import MoneyError, check_currency, fmt, parse_amount
from .domain.planning import PlanRequest, build_plan
from .domain.providers import Provider, quote_for_target_receive
from .integrations.sandbox_provider import SandboxExecutionError, SandboxProviderAdapter
from .persistence.audit import AuditLog
from .persistence.db import Database, InsufficientFunds
from .security.permissions import Principal, Tier, require_account_access, require_tier


class NotFound(Exception):
    pass


class InvalidState(Exception):
    pass


EXECUTED = "EXECUTED_SIMULATED"


@dataclass
class Services:
    settings: Settings
    db: Database
    audit: AuditLog
    rates: RateTable
    providers: dict[str, Provider]
    explainer: Explainer
    sandbox: SandboxProviderAdapter
    clock: Clock

    # ---------------- helpers ----------------
    def _account(self, principal: Principal, account_id: str) -> dict:
        require_account_access(principal, account_id)
        acct = self.db.get_account(account_id)
        if acct is None:
            raise NotFound(f"Account {account_id} not found")
        return acct

    def _balances(self, account_id: str) -> dict[str, Decimal]:
        return {r["currency"]: Decimal(r["amount"]) for r in self.db.get_balances(account_id)}

    @staticmethod
    def _beneficiary_view(b: dict | None) -> dict | None:
        if b is None:
            return None
        return {"id": b["id"], "name": b["name"], "currency": b["currency"], "country": b["country"],
                "kind": b["kind"], "account_number_masked": b["account_number_masked"], "blocked": bool(b["blocked"])}

    def _transfer_view(self, t: dict, replayed: bool = False) -> dict:
        b = self.db.get_beneficiary(t["account_id"], t.get("beneficiary_id"))
        return {
            "id": t["id"], "account_id": t["account_id"], "status": t["status"], "provider_id": t["provider_id"],
            "beneficiary_id": t["beneficiary_id"], "beneficiary": self._beneficiary_view(b),
            "quote": json.loads(t["quote_json"]) if t["quote_json"] else None,
            "risk": json.loads(t["risk_json"]) if t["risk_json"] else None,
            "memo": t["memo"], "memo_flagged": bool(t["memo_flagged"]), "due_date": t["due_date"],
            "quote_expires_at": t["quote_expires_at"], "amount_usd_equiv": t["amount_usd_equiv"],
            "created_at": t["created_at"], "updated_at": t["updated_at"], "executed_at": t["executed_at"],
            "provider_reference": t["provider_reference"], "failure_reason": t["failure_reason"],
            "created_by": t["created_by"], "approved_by": t["approved_by"],
            "execution_label": SandboxProviderAdapter.LABEL, "replayed": replayed,
        }

    def _load_transfer(self, principal: Principal, transfer_id: str) -> dict:
        t = self.db.get_transfer(transfer_id)
        if t is None:
            raise NotFound(f"Transfer {transfer_id} not found")
        require_account_access(principal, t["account_id"])
        return t

    def _risk(self, *, acct: dict, provider: Provider, beneficiary: dict | None, send_amount: Decimal,
              amount_usd: Decimal, recv: str, send_ccy: str, due_date: date, expires_at: datetime | None,
              now: datetime, already_executed: bool) -> risk.RiskResult:
        balances = self._balances(acct["id"])
        ctx = risk.RiskContext(
            amount_usd_equiv=amount_usd, send_amount=send_amount, send_currency=send_ccy,
            balance_send_currency=balances.get(send_ccy, Decimal(0)), reserve_min=Decimal(acct["reserve_min"]),
            beneficiary=beneficiary, receive_currency=recv,
            provider_supports_corridor=provider.supports(send_ccy, recv),
            provider_max_amount_usd=provider.max_amount_usd,
            per_transfer_cap_usd=self.settings.per_transfer_cap_usd, daily_cap_usd=self.settings.daily_cap_usd,
            daily_executed_usd=self.db.daily_executed_usd(acct["id"], now.date().isoformat()),
            quote_expires_at=expires_at, now=now, already_executed=already_executed,
            settlement_days=provider.settlement_days, days_until_due=(due_date - now.date()).days,
        )
        return risk.evaluate(ctx)

    def _recheck(self, t: dict, now: datetime) -> risk.RiskResult:
        if not t["quote_json"]:
            raise InvalidState("Transfer has no quote and cannot progress")
        q = json.loads(t["quote_json"])
        acct = self.db.get_account(t["account_id"])
        provider = self.providers[t["provider_id"]]
        beneficiary = self.db.get_beneficiary(t["account_id"], t["beneficiary_id"])
        return self._risk(
            acct=acct, provider=provider, beneficiary=beneficiary, send_amount=Decimal(q["send_amount"]),
            amount_usd=Decimal(t["amount_usd_equiv"]), recv=q["receive_currency"], send_ccy=q["send_currency"],
            due_date=date.fromisoformat(t["due_date"]), expires_at=datetime.fromisoformat(t["quote_expires_at"]),
            now=now, already_executed=(t["status"] == EXECUTED))

    @staticmethod
    def _blocked_status(result: risk.RiskResult) -> str:
        return "EXPIRED" if any(f.code == "QUOTE_EXPIRED" for f in result.findings) else "BLOCKED"

    # ---------------- Tier 0: read ----------------
    def account_view(self, principal: Principal, account_id: str) -> dict:
        require_tier(principal, Tier.READ)
        acct = self._account(principal, account_id)
        return {
            "account": {"id": acct["id"], "holder_name": acct["holder_name"], "home_currency": acct["home_currency"],
                        "reserve_min": acct["reserve_min"], "institution": acct["institution"]},
            "balances": self.db.get_balances(account_id),
            "beneficiaries": [self._beneficiary_view(b) for b in self.db.list_beneficiaries(account_id)],
            "limits": {"per_transfer_cap_usd": fmt(self.settings.per_transfer_cap_usd),
                       "daily_cap_usd": fmt(self.settings.daily_cap_usd),
                       "daily_executed_usd": fmt(self.db.daily_executed_usd(account_id, self.clock.today().isoformat())),
                       "quote_ttl_seconds": self.settings.quote_ttl_seconds},
            "principal": {"role": principal.role, "max_tier": int(principal.max_tier), "key_id": principal.key_id},
            "data_label": "SYNTHETIC",
        }

    def rates_view(self, principal: Principal) -> list[dict]:
        require_tier(principal, Tier.READ)
        return [{"base": r.base, "quote": r.quote, "mid": fmt(r.mid), "as_of": r.as_of, "source": r.source}
                for r in self.rates.all()]

    def providers_view(self, principal: Principal) -> list[dict]:
        require_tier(principal, Tier.READ)
        return [p.to_dict() for p in self.providers.values()]

    def list_transfers(self, principal: Principal, account_id: str) -> list[dict]:
        require_tier(principal, Tier.READ)
        self._account(principal, account_id)
        return [self._transfer_view(t) for t in self.db.list_transfers(account_id)]

    def get_transfer(self, principal: Principal, transfer_id: str) -> dict:
        require_tier(principal, Tier.READ)
        return self._transfer_view(self._load_transfer(principal, transfer_id))

    def audit_entries(self, principal: Principal, account_id: str) -> list[dict]:
        require_tier(principal, Tier.READ)
        require_account_access(principal, account_id)
        return self.audit.entries(account_id)

    def audit_verify(self, principal: Principal) -> dict:
        require_tier(principal, Tier.READ)
        return self.audit.verify()

    # ---------------- Tier 1: analyse ----------------
    def compare(self, principal: Principal, *, account_id: str, target_receive_amount: str, receive_currency: str,
                send_currency: str | None, due_date: date, question: str | None) -> dict:
        require_tier(principal, Tier.ANALYZE)
        acct = self._account(principal, account_id)
        target = parse_amount(target_receive_amount)
        if target <= 0:
            raise MoneyError("target_receive_amount must be positive")
        send_ccy = check_currency(send_currency or acct["home_currency"])
        plan = build_plan(self.providers, self.rates, PlanRequest(
            balances=self._balances(account_id), reserve_min=Decimal(acct["reserve_min"]), target_receive=target,
            receive_currency=receive_currency, send_currency=send_ccy, due_date=due_date, today=self.clock.today()))
        q = sanitize_untrusted(question)
        explanation = self.explainer.explain(plan, q)
        self.audit.append(actor=principal.key_id, action="QUOTE_COMPARE", tier=Tier.ANALYZE, account_id=account_id,
                          entity_type="plan", entity_id=None,
                          payload={"target_receive_amount": plan["target_receive_amount"],
                                   "receive_currency": plan["receive_currency"],
                                   "recommended_provider_id": plan["recommended_provider_id"],
                                   "explanation_source": explanation.source, "question_flagged": q.flagged})
        return {"plan": plan, "explanation": explanation.to_dict(),
                "question_flagged": q.flagged, "question_flags": q.reasons}

    # ---------------- Tier 2: prepare / reject ----------------
    def prepare(self, principal: Principal, *, account_id: str, beneficiary_id: str, provider_id: str,
                target_receive_amount: str, receive_currency: str, send_currency: str | None, due_date: date,
                memo: str | None, idempotency_key: str) -> dict:
        require_tier(principal, Tier.PREPARE)
        acct = self._account(principal, account_id)
        existing = self.db.get_transfer_by_idempotency(account_id, idempotency_key)
        if existing is not None:
            return self._transfer_view(existing, replayed=True)
        provider = self.providers.get(provider_id)
        if provider is None:
            raise NotFound(f"Provider {provider_id} not found")
        target = parse_amount(target_receive_amount)
        if target <= 0:
            raise MoneyError("target_receive_amount must be positive")
        recv = check_currency(receive_currency)
        send_ccy = check_currency(send_currency or acct["home_currency"])
        beneficiary = self.db.get_beneficiary(account_id, beneficiary_id)
        now = self.clock.now()
        quote, quote_error = None, None
        if provider.supports(send_ccy, recv):
            try:
                quote = quote_for_target_receive(provider, target, send_ccy, recv, self.rates)
            except MoneyError as exc:
                quote_error = str(exc)
        expires = now + timedelta(seconds=self.settings.quote_ttl_seconds)
        amount_usd = usd_equivalent(target, recv, self.rates)
        result = self._risk(acct=acct, provider=provider, beneficiary=beneficiary,
                            send_amount=quote.send_amount if quote else Decimal(0), amount_usd=amount_usd,
                            recv=recv, send_ccy=send_ccy, due_date=due_date, expires_at=expires, now=now,
                            already_executed=False)
        if quote_error:
            result = result.with_finding(risk.Finding("QUOTE_ERROR", risk.BLOCK, quote_error))
        memo_s = sanitize_untrusted(memo)
        status = "PENDING_APPROVAL" if result.passed else "BLOCKED"
        row = {
            "id": "trf_" + uuid.uuid4().hex[:12], "account_id": account_id, "beneficiary_id": beneficiary_id,
            "provider_id": provider_id, "idempotency_key": idempotency_key, "status": status,
            "quote_json": json.dumps(quote.to_dict()) if quote else None, "risk_json": json.dumps(result.to_dict()),
            "memo": memo_s.text, "memo_flagged": int(memo_s.flagged), "due_date": due_date.isoformat(),
            "quote_expires_at": expires.isoformat(), "amount_usd_equiv": fmt(amount_usd),
            "created_at": now.isoformat(), "updated_at": now.isoformat(), "executed_at": None,
            "provider_reference": None, "failure_reason": None, "created_by": principal.key_id, "approved_by": None,
        }
        self.db.insert_transfer(row)
        self.audit.append(actor=principal.key_id, action="TRANSFER_PREPARED" if result.passed else "TRANSFER_BLOCKED",
                          tier=Tier.PREPARE, account_id=account_id, entity_type="transfer", entity_id=row["id"],
                          payload={"status": status, "provider_id": provider_id, "beneficiary_id": beneficiary_id,
                                   "target_receive_amount": fmt(target), "receive_currency": recv,
                                   "send_amount": fmt(quote.send_amount) if quote else None, "send_currency": send_ccy,
                                   "findings": [f.code for f in result.findings], "memo_flagged": memo_s.flagged})
        return self._transfer_view(row)

    def reject(self, principal: Principal, transfer_id: str, note: str | None = None) -> dict:
        require_tier(principal, Tier.PREPARE)
        t = self._load_transfer(principal, transfer_id)
        if t["status"] not in ("PENDING_APPROVAL", "APPROVED"):
            raise InvalidState(f"Transfer is {t['status']}; only PENDING_APPROVAL or APPROVED transfers can be rejected")
        now = self.clock.now()
        self.db.update_transfer(transfer_id, status="REJECTED", updated_at=now.isoformat())
        self.audit.append(actor=principal.key_id, action="TRANSFER_REJECTED", tier=Tier.PREPARE,
                          account_id=t["account_id"], entity_type="transfer", entity_id=transfer_id,
                          payload={"note": sanitize_untrusted(note).text})
        return self._transfer_view(self.db.get_transfer(transfer_id))

    # ---------------- Tier 3: approve / execute (sandbox) ----------------
    def approve(self, principal: Principal, transfer_id: str, note: str | None = None) -> dict:
        require_tier(principal, Tier.EXECUTE_SANDBOX)
        t = self._load_transfer(principal, transfer_id)
        if t["status"] != "PENDING_APPROVAL":
            raise InvalidState(f"Transfer is {t['status']}; only PENDING_APPROVAL transfers can be approved")
        now = self.clock.now()
        result = self._recheck(t, now)
        status = "APPROVED" if result.passed else self._blocked_status(result)
        self.db.update_transfer(transfer_id, status=status, risk_json=json.dumps(result.to_dict()),
                                approved_by=principal.key_id if result.passed else None, updated_at=now.isoformat())
        self.audit.append(actor=principal.key_id,
                          action="TRANSFER_APPROVED" if result.passed else "TRANSFER_APPROVAL_BLOCKED",
                          tier=Tier.EXECUTE_SANDBOX, account_id=t["account_id"], entity_type="transfer",
                          entity_id=transfer_id,
                          payload={"status": status, "findings": [f.code for f in result.findings],
                                   "note": sanitize_untrusted(note).text})
        return self._transfer_view(self.db.get_transfer(transfer_id))

    def execute(self, principal: Principal, transfer_id: str) -> dict:
        require_tier(principal, Tier.EXECUTE_SANDBOX)
        t = self._load_transfer(principal, transfer_id)
        if t["status"] == EXECUTED:
            return self._transfer_view(t, replayed=True)  # idempotent: never executes twice
        if t["status"] not in ("APPROVED", "FAILED"):
            raise InvalidState(f"Transfer is {t['status']}; only APPROVED (or FAILED, for retry) transfers can be executed")
        now = self.clock.now()
        result = self._recheck(t, now)
        if not result.passed:
            status = self._blocked_status(result)
            self.db.update_transfer(transfer_id, status=status, risk_json=json.dumps(result.to_dict()),
                                    updated_at=now.isoformat())
            self.audit.append(actor=principal.key_id, action="TRANSFER_EXECUTION_BLOCKED", tier=Tier.EXECUTE_SANDBOX,
                              account_id=t["account_id"], entity_type="transfer", entity_id=transfer_id,
                              payload={"status": status, "findings": [f.code for f in result.findings]})
            return self._transfer_view(self.db.get_transfer(transfer_id))
        q = json.loads(t["quote_json"])
        beneficiary = self.db.get_beneficiary(t["account_id"], t["beneficiary_id"])
        try:
            res = self.sandbox.execute(
                transfer_id=transfer_id, provider_id=t["provider_id"], send_amount=Decimal(q["send_amount"]),
                send_currency=q["send_currency"], receive_amount=Decimal(q["receive_amount"]),
                receive_currency=q["receive_currency"], beneficiary=beneficiary, now=now)
            self.db.debit_and_mark_executed(
                transfer_id, t["account_id"], q["send_currency"], Decimal(q["send_amount"]),
                status=EXECUTED, executed_at=res.executed_at, provider_reference=res.reference,
                failure_reason=None, risk_json=json.dumps(result.to_dict()), updated_at=now.isoformat())
        except (SandboxExecutionError, InsufficientFunds) as exc:
            self.db.update_transfer(transfer_id, status="FAILED", failure_reason=str(exc),
                                    risk_json=json.dumps(result.to_dict()), updated_at=now.isoformat())
            self.audit.append(actor=principal.key_id, action="TRANSFER_EXECUTION_FAILED", tier=Tier.EXECUTE_SANDBOX,
                              account_id=t["account_id"], entity_type="transfer", entity_id=transfer_id,
                              payload={"reason": str(exc), "balance_debited": False, "retryable": True})
            return self._transfer_view(self.db.get_transfer(transfer_id))
        self.audit.append(actor=principal.key_id, action="TRANSFER_EXECUTED_SIMULATED", tier=Tier.EXECUTE_SANDBOX,
                          account_id=t["account_id"], entity_type="transfer", entity_id=transfer_id,
                          payload={"provider_reference": res.reference, "send_amount": q["send_amount"],
                                   "send_currency": q["send_currency"], "receive_amount": q["receive_amount"],
                                   "receive_currency": q["receive_currency"], "label": res.label})
        return self._transfer_view(self.db.get_transfer(transfer_id))

    # ---------------- Tier 4: always refused ----------------
    def production_execute(self, principal: Principal, transfer_id: str) -> dict:
        require_tier(principal, Tier.PRODUCTION)  # raises unconditionally in this build
        raise AssertionError("unreachable")
