"""Deterministic tuition payment plan: rank providers, check timing and affordability."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .fx import RateTable, usd_equivalent
from .money import MoneyError, check_currency, fmt
from .providers import Provider, quote_for_target_receive

RECOMMENDATION_RULE = (
    "Among providers that settle on or before the due date, recommend the lowest send amount; "
    "if none settle in time, recommend the fastest and warn."
)


@dataclass(frozen=True)
class PlanRequest:
    balances: dict[str, Decimal]
    reserve_min: Decimal
    target_receive: Decimal
    receive_currency: str
    send_currency: str
    due_date: date
    today: date


def build_plan(providers: dict[str, Provider], rates: RateTable, req: PlanRequest) -> dict:
    send_ccy = check_currency(req.send_currency)
    recv = check_currency(req.receive_currency)
    days_until_due = (req.due_date - req.today).days
    usd_equiv = usd_equivalent(req.target_receive, recv, rates)

    quotes, exclusions = [], []
    for p in providers.values():
        if not p.supports(send_ccy, recv):
            exclusions.append({"provider_id": p.id, "reason": "CORRIDOR_NOT_SUPPORTED"})
            continue
        if usd_equiv > p.max_amount_usd:
            exclusions.append({"provider_id": p.id, "reason": "PROVIDER_MAX_AMOUNT"})
            continue
        try:
            quotes.append(quote_for_target_receive(p, req.target_receive, send_ccy, recv, rates))
        except MoneyError as exc:
            exclusions.append({"provider_id": p.id, "reason": "QUOTE_ERROR", "detail": str(exc)})

    quotes.sort(key=lambda q: (q.send_amount, q.settlement_days))
    in_time = [q for q in quotes if q.settlement_days <= days_until_due]
    warnings: list[str] = []
    if not quotes:
        recommended = None
        warnings.append("No provider supports this corridor and amount.")
    elif in_time:
        recommended = in_time[0]
    else:
        recommended = min(quotes, key=lambda q: (q.settlement_days, q.send_amount))
        warnings.append("No provider settles before the due date; the fastest option is recommended.")

    balance = req.balances.get(send_ccy, Decimal(0))
    affordability = None
    if recommended is not None:
        after = balance - recommended.send_amount
        affordable = after >= req.reserve_min
        affordability = {
            "currency": send_ccy, "balance": fmt(balance), "send_amount": fmt(recommended.send_amount),
            "balance_after": fmt(after), "reserve_min": fmt(req.reserve_min), "affordable": affordable,
        }
        if not affordable:
            warnings.append("Payment would take the balance below the minimum reserve.")

    ranked = []
    for i, q in enumerate(quotes, start=1):
        d = q.to_dict()
        d["rank"] = i
        d["settles_before_due"] = q.settlement_days <= days_until_due
        d["extra_cost_vs_best"] = fmt(q.send_amount - quotes[0].send_amount)
        ranked.append(d)

    return {
        "target_receive_amount": fmt(req.target_receive), "receive_currency": recv, "send_currency": send_ccy,
        "usd_equivalent": fmt(usd_equiv), "due_date": req.due_date.isoformat(), "today": req.today.isoformat(),
        "days_until_due": days_until_due, "quotes": ranked, "exclusions": exclusions,
        "recommended_provider_id": recommended.provider_id if recommended else None,
        "recommendation_rule": RECOMMENDATION_RULE, "affordability": affordability,
        "warnings": warnings, "data_label": "SYNTHETIC_FIXTURE",
    }
