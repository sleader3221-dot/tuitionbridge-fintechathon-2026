"""Deterministic risk checks. Pure function of a RiskContext; the AI layer never touches this."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .money import fmt

BLOCK = "BLOCK"
WARN = "WARN"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class RiskResult:
    passed: bool
    findings: list[Finding]
    checked_at: str

    def to_dict(self) -> dict:
        return {"passed": self.passed, "checked_at": self.checked_at,
                "findings": [{"code": f.code, "severity": f.severity, "message": f.message} for f in self.findings]}

    def with_finding(self, f: Finding) -> "RiskResult":
        findings = [*self.findings, f]
        return RiskResult(not any(x.severity == BLOCK for x in findings), findings, self.checked_at)


@dataclass(frozen=True)
class RiskContext:
    amount_usd_equiv: Decimal
    send_amount: Decimal
    send_currency: str
    balance_send_currency: Decimal
    reserve_min: Decimal
    beneficiary: dict | None
    receive_currency: str
    provider_supports_corridor: bool
    provider_max_amount_usd: Decimal
    per_transfer_cap_usd: Decimal
    daily_cap_usd: Decimal
    daily_executed_usd: Decimal
    quote_expires_at: datetime | None
    now: datetime
    already_executed: bool
    settlement_days: int
    days_until_due: int


def evaluate(ctx: RiskContext) -> RiskResult:
    f: list[Finding] = []
    if ctx.already_executed:
        f.append(Finding("DUPLICATE_EXECUTION", BLOCK, "This transfer has already been executed; replay refused."))
    if ctx.beneficiary is None:
        f.append(Finding("BENEFICIARY_NOT_FOUND", BLOCK, "Beneficiary not found for this account."))
    else:
        if ctx.beneficiary.get("blocked"):
            f.append(Finding("BENEFICIARY_BLOCKED", BLOCK,
                             f"Beneficiary is on the (synthetic) blocked list: {ctx.beneficiary.get('blocked_reason')}"))
        if ctx.beneficiary.get("currency") != ctx.receive_currency:
            f.append(Finding("CURRENCY_MISMATCH", BLOCK,
                             f"Beneficiary accepts {ctx.beneficiary.get('currency')}, not {ctx.receive_currency}."))
    if not ctx.provider_supports_corridor:
        f.append(Finding("CORRIDOR_NOT_SUPPORTED", BLOCK,
                         f"Provider does not support {ctx.send_currency}->{ctx.receive_currency}."))
    if ctx.amount_usd_equiv > ctx.provider_max_amount_usd:
        f.append(Finding("PROVIDER_MAX_AMOUNT", BLOCK,
                         f"USD equivalent {fmt(ctx.amount_usd_equiv)} exceeds provider maximum {fmt(ctx.provider_max_amount_usd)}."))
    if ctx.amount_usd_equiv > ctx.per_transfer_cap_usd:
        f.append(Finding("PER_TRANSFER_CAP", BLOCK,
                         f"USD equivalent {fmt(ctx.amount_usd_equiv)} exceeds the per-transfer cap {fmt(ctx.per_transfer_cap_usd)}."))
    if ctx.daily_executed_usd + ctx.amount_usd_equiv > ctx.daily_cap_usd:
        f.append(Finding("DAILY_CAP", BLOCK,
                         f"Executed today {fmt(ctx.daily_executed_usd)} + {fmt(ctx.amount_usd_equiv)} USD exceeds the daily cap {fmt(ctx.daily_cap_usd)}."))
    if ctx.balance_send_currency - ctx.send_amount < ctx.reserve_min:
        f.append(Finding("INSUFFICIENT_BALANCE", BLOCK,
                         f"Balance {fmt(ctx.balance_send_currency)} {ctx.send_currency} minus {fmt(ctx.send_amount)} "
                         f"would fall below the reserve {fmt(ctx.reserve_min)}."))
    if ctx.quote_expires_at is not None and ctx.now > ctx.quote_expires_at:
        f.append(Finding("QUOTE_EXPIRED", BLOCK, f"Quote expired at {ctx.quote_expires_at.isoformat()}."))
    if ctx.settlement_days > ctx.days_until_due:
        f.append(Finding("SETTLEMENT_AFTER_DUE", WARN,
                         f"Settlement takes {ctx.settlement_days} day(s) but only {ctx.days_until_due} day(s) remain."))
    return RiskResult(not any(x.severity == BLOCK for x in f), f, ctx.now.isoformat())
