"""Mid-market rate table loaded from a clearly labelled synthetic fixture."""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .money import MoneyError, check_currency, round_half_even


@dataclass(frozen=True)
class Rate:
    base: str
    quote: str
    mid: Decimal  # 1 base = mid quote
    as_of: str
    source: str


class RateTable:
    def __init__(self, rates: list[Rate]):
        self._rates = {(r.base, r.quote): r for r in rates}

    @classmethod
    def from_json(cls, path: Path) -> "RateTable":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls([Rate(r["base"], r["quote"], Decimal(r["mid"]), r["as_of"], r["source"]) for r in raw["rates"]])

    def mid_rate(self, from_ccy: str, to_ccy: str) -> tuple[Decimal, Rate]:
        """Return (rate, source) such that to_amount = from_amount * rate."""
        f, t = check_currency(from_ccy), check_currency(to_ccy)
        if f == t:
            raise MoneyError("from and to currency must differ")
        if (f, t) in self._rates:
            r = self._rates[(f, t)]
            return r.mid, r
        if (t, f) in self._rates:
            r = self._rates[(t, f)]
            return Decimal(1) / r.mid, r
        raise MoneyError(f"No rate available for {f}->{t}")

    def all(self) -> list[Rate]:
        return list(self._rates.values())


def usd_equivalent(amount: Decimal, currency: str, rates: RateTable) -> Decimal:
    c = check_currency(currency)
    if c == "USD":
        return round_half_even(amount, "USD")
    try:
        rate, _ = rates.mid_rate(c, "USD")
    except MoneyError:
        r1, _ = rates.mid_rate(c, "INR")
        r2, _ = rates.mid_rate("INR", "USD")
        rate = r1 * r2
    return round_half_even(amount * rate, "USD")
