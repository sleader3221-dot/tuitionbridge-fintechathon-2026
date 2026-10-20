from decimal import Decimal

import pytest

from app.config import DATA_DIR
from app.domain.fx import RateTable
from app.domain.money import MoneyError
from app.domain.providers import load_providers, quote_for_send, quote_for_target_receive


@pytest.fixture
def rates():
    return RateTable.from_json(DATA_DIR / "rates.json")


@pytest.fixture
def providers():
    return load_providers(DATA_DIR / "providers.json")


def test_bank_wire_hand_checked(providers, rates):
    # fixed 1500 INR, 0% fee, 2.5% margin, mid 88.50 INR per USD, target 1000 USD
    # needed converted = 1000 * 88.5 / 0.975 = 90769.2308 -> send = 92269.24 (rounded up)
    q = quote_for_target_receive(providers["demo_bank_wire"], Decimal("1000"), "INR", "USD", rates)
    assert q.send_amount == Decimal("92269.24")
    assert q.receive_amount == Decimal("1000.00")
    assert q.total_fees == Decimal("1500.00")
    assert q.cost_vs_mid == Decimal("3769.24")
    assert q.cost_pct == Decimal("0.0409")


@pytest.mark.parametrize("pid", ["demo_bank_wire", "demo_fintech_a", "demo_fintech_b", "demo_edu_platform"])
@pytest.mark.parametrize("target", ["1.00", "999.99", "10000.00", "19999.99"])
def test_target_mode_meets_target_tightly(providers, rates, pid, target):
    q = quote_for_target_receive(providers[pid], Decimal(target), "INR", "USD", rates)
    assert q.receive_amount >= Decimal(target)
    assert q.receive_amount - Decimal(target) < Decimal("0.05")
    assert q.send_amount == q.total_fees + q.amount_converted
    assert q.total_fees == q.fixed_fee + q.percent_fee_amount


def test_send_mode_consistency(providers, rates):
    q = quote_for_send(providers["demo_fintech_a"], Decimal("100000"), "INR", "USD", rates)
    assert q.percent_fee_amount == Decimal("900.00")
    assert q.amount_converted == Decimal("99100.00")
    expected = (Decimal("99100.00") * (Decimal(1) / Decimal("88.50")) * Decimal("0.994")).quantize(Decimal("0.01"))
    assert abs(q.receive_amount - expected) <= Decimal("0.01")


def test_fees_exceed_amount(providers, rates):
    with pytest.raises(MoneyError):
        quote_for_send(providers["demo_bank_wire"], Decimal("1000"), "INR", "USD", rates)


def test_unsupported_corridor(providers, rates):
    with pytest.raises(MoneyError):
        quote_for_target_receive(providers["demo_fintech_b"], Decimal("100"), "INR", "EUR", rates)
