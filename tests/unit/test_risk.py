from datetime import timedelta
from decimal import Decimal

from app.domain import risk
from tests.helpers import FIXED_NOW

BENEF = {"id": "b", "currency": "USD", "blocked": 0, "blocked_reason": None}


def ctx(**over):
    base = dict(amount_usd_equiv=Decimal("10000"), send_amount=Decimal("900000"), send_currency="INR",
                balance_send_currency=Decimal("1250000"), reserve_min=Decimal("150000"), beneficiary=BENEF,
                receive_currency="USD", provider_supports_corridor=True, provider_max_amount_usd=Decimal("20000"),
                per_transfer_cap_usd=Decimal("15000"), daily_cap_usd=Decimal("20000"),
                daily_executed_usd=Decimal("0"), quote_expires_at=FIXED_NOW + timedelta(minutes=15), now=FIXED_NOW,
                already_executed=False, settlement_days=1, days_until_due=10)
    base.update(over)
    return risk.RiskContext(**base)


def codes(r):
    return {f.code for f in r.findings}


def test_passes_clean():
    assert risk.evaluate(ctx()).passed


def test_per_transfer_cap():
    r = risk.evaluate(ctx(amount_usd_equiv=Decimal("15000.01")))
    assert not r.passed and "PER_TRANSFER_CAP" in codes(r)


def test_daily_cap_boundary():
    assert risk.evaluate(ctx(daily_executed_usd=Decimal("10000"))).passed  # exactly at cap passes
    r = risk.evaluate(ctx(daily_executed_usd=Decimal("10000.01")))
    assert "DAILY_CAP" in codes(r)


def test_blocked_beneficiary_and_mismatch():
    r = risk.evaluate(ctx(beneficiary={**BENEF, "blocked": 1, "blocked_reason": "demo", "currency": "GBP"}))
    assert {"BENEFICIARY_BLOCKED", "CURRENCY_MISMATCH"} <= codes(r)


def test_insufficient_balance_boundary():
    assert risk.evaluate(ctx(send_amount=Decimal("1100000"))).passed  # leaves exactly the reserve
    assert "INSUFFICIENT_BALANCE" in codes(risk.evaluate(ctx(send_amount=Decimal("1100000.01"))))


def test_expired_quote_and_duplicate():
    r = risk.evaluate(ctx(quote_expires_at=FIXED_NOW - timedelta(seconds=1), already_executed=True))
    assert {"QUOTE_EXPIRED", "DUPLICATE_EXECUTION"} <= codes(r)


def test_settlement_warning_does_not_block():
    r = risk.evaluate(ctx(settlement_days=5, days_until_due=2))
    assert r.passed and "SETTLEMENT_AFTER_DUE" in codes(r)
