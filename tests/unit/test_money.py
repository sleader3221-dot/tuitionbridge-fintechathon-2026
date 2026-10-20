from decimal import Decimal

import pytest

from app.domain.money import MoneyError, check_currency, parse_amount, round_down, round_half_even, round_up


def test_floats_rejected():
    with pytest.raises(MoneyError):
        parse_amount(10.5)


def test_parse_and_round():
    assert parse_amount("10000.005") == Decimal("10000.005")
    assert round_half_even(Decimal("2.675"), "USD") == Decimal("2.68")
    assert round_half_even(Decimal("2.665"), "USD") == Decimal("2.66")
    assert round_up(Decimal("1.001"), "INR") == Decimal("1.01")
    assert round_down(Decimal("1.009"), "INR") == Decimal("1.00")


def test_invalid_inputs():
    with pytest.raises(MoneyError):
        parse_amount("abc")
    with pytest.raises(MoneyError):
        parse_amount("NaN")
    with pytest.raises(MoneyError):
        check_currency("XYZ")
