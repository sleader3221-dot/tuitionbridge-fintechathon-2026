"""Provider fee models and deterministic quoting.

Formulas (send currency S, receive currency R):
  customer_rate      = mid_rate(S->R) * (1 - fx_margin)
  percent_fee_amount = round_half_even(send_amount * percent_fee, S)
  total_fees         = fixed_fee + percent_fee_amount
  amount_converted   = send_amount - total_fees
  receive_amount     = round_down(amount_converted * customer_rate, R)
  cost_vs_mid        = round_half_even(send_amount - receive_amount / mid_rate, S)
  cost_pct           = cost_vs_mid / send_amount   (4 dp fraction)
Target-receive mode solves for send_amount (rounded UP) and then re-quotes forward,
nudging by one minor unit until receive_amount >= target.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

from .fx import RateTable
from .money import MoneyError, fmt, minor_unit, round_down, round_half_even, round_up


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    fixed_fee: Decimal
    fixed_fee_currency: str
    percent_fee: Decimal
    fx_margin: Decimal
    settlement_days: int
    corridors: frozenset[str]
    max_amount_usd: Decimal
    pays_institution_directly: bool
    label: str

    def supports(self, send_ccy: str, receive_ccy: str) -> bool:
        return f"{send_ccy}-{receive_ccy}" in self.corridors and self.fixed_fee_currency == send_ccy

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "fixed_fee": fmt(self.fixed_fee),
            "fixed_fee_currency": self.fixed_fee_currency, "percent_fee": fmt(self.percent_fee),
            "fx_margin": fmt(self.fx_margin), "settlement_days": self.settlement_days,
            "corridors": sorted(self.corridors), "max_amount_usd": fmt(self.max_amount_usd),
            "pays_institution_directly": self.pays_institution_directly, "label": self.label,
        }


def load_providers(path: Path) -> dict[str, Provider]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, Provider] = {}
    for p in raw["providers"]:
        out[p["id"]] = Provider(
            id=p["id"], name=p["name"], fixed_fee=Decimal(p["fixed_fee"]),
            fixed_fee_currency=p["fixed_fee_currency"], percent_fee=Decimal(p["percent_fee"]),
            fx_margin=Decimal(p["fx_margin"]), settlement_days=int(p["settlement_days"]),
            corridors=frozenset(p["corridors"]), max_amount_usd=Decimal(p["max_amount_usd"]),
            pays_institution_directly=bool(p["pays_institution_directly"]), label=p.get("label", "SIMULATED"),
        )
    return out


@dataclass(frozen=True)
class Quote:
    provider_id: str
    provider_name: str
    send_currency: str
    receive_currency: str
    send_amount: Decimal
    fixed_fee: Decimal
    percent_fee_amount: Decimal
    total_fees: Decimal
    amount_converted: Decimal
    mid_rate: Decimal
    customer_rate: Decimal
    receive_amount: Decimal
    cost_vs_mid: Decimal
    cost_pct: Decimal
    settlement_days: int
    pays_institution_directly: bool
    rate_as_of: str
    rate_source: str
    label: str

    def to_dict(self) -> dict:
        return {k: (fmt(v) if isinstance(v, Decimal) else v) for k, v in asdict(self).items()}


def _check_corridor(provider: Provider, send_ccy: str, receive_ccy: str) -> None:
    if not provider.supports(send_ccy, receive_ccy):
        raise MoneyError(f"Provider {provider.id} does not support {send_ccy}->{receive_ccy}")


def quote_for_send(provider: Provider, send_amount: Decimal, send_ccy: str, receive_ccy: str, rates: RateTable) -> Quote:
    _check_corridor(provider, send_ccy, receive_ccy)
    mid, rate = rates.mid_rate(send_ccy, receive_ccy)
    send_amount = round_half_even(send_amount, send_ccy)
    if send_amount <= 0:
        raise MoneyError("send_amount must be positive")
    pct_fee = round_half_even(send_amount * provider.percent_fee, send_ccy)
    fees = provider.fixed_fee + pct_fee
    converted = send_amount - fees
    if converted <= 0:
        raise MoneyError("Fees exceed the amount sent")
    customer_rate = mid * (Decimal(1) - provider.fx_margin)
    received = round_down(converted * customer_rate, receive_ccy)
    cost = round_half_even(send_amount - (received / mid), send_ccy)
    cost_pct = (cost / send_amount).quantize(Decimal("0.0001"))
    return Quote(
        provider_id=provider.id, provider_name=provider.name, send_currency=send_ccy,
        receive_currency=receive_ccy, send_amount=send_amount, fixed_fee=provider.fixed_fee,
        percent_fee_amount=pct_fee, total_fees=fees, amount_converted=converted,
        mid_rate=mid.quantize(Decimal("0.00000001")), customer_rate=customer_rate.quantize(Decimal("0.00000001")),
        receive_amount=received, cost_vs_mid=cost, cost_pct=cost_pct,
        settlement_days=provider.settlement_days, pays_institution_directly=provider.pays_institution_directly,
        rate_as_of=rate.as_of, rate_source=rate.source, label=provider.label,
    )


def quote_for_target_receive(provider: Provider, target: Decimal, send_ccy: str, receive_ccy: str, rates: RateTable) -> Quote:
    _check_corridor(provider, send_ccy, receive_ccy)
    target = round_half_even(target, receive_ccy)
    if target <= 0:
        raise MoneyError("target receive amount must be positive")
    mid, _ = rates.mid_rate(send_ccy, receive_ccy)
    customer_rate = mid * (Decimal(1) - provider.fx_margin)
    needed_converted = target / customer_rate
    send = round_up((needed_converted + provider.fixed_fee) / (Decimal(1) - provider.percent_fee), send_ccy)
    for _ in range(5):
        q = quote_for_send(provider, send, send_ccy, receive_ccy, rates)
        if q.receive_amount >= target:
            return q
        send += minor_unit(send_ccy)
    raise MoneyError("Could not construct a quote that meets the target receive amount")
