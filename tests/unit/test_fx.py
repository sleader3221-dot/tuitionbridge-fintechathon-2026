from decimal import Decimal

import pytest

from app.config import DATA_DIR
from app.domain.fx import RateTable, usd_equivalent
from app.domain.money import MoneyError


@pytest.fixture
def rates():
    return RateTable.from_json(DATA_DIR / "rates.json")


def test_direct_and_inverse(rates):
    r, src = rates.mid_rate("USD", "INR")
    assert r == Decimal("88.50") and src.source == "SYNTHETIC_FIXTURE"
    inv, _ = rates.mid_rate("INR", "USD")
    assert (inv * Decimal("88.50")).quantize(Decimal("0.0001")) == Decimal("1.0000")


def test_unsupported_pair(rates):
    with pytest.raises(MoneyError):
        rates.mid_rate("USD", "USD")


def test_usd_equivalent_cross(rates):
    assert usd_equivalent(Decimal("100"), "USD", rates) == Decimal("100.00")
    assert usd_equivalent(Decimal("100"), "GBP", rates) == Decimal("133.56")
    cad = usd_equivalent(Decimal("100"), "CAD", rates)  # cross via INR
    assert cad == (Decimal("100") * Decimal("64.10") / Decimal("88.50")).quantize(Decimal("0.01"))
