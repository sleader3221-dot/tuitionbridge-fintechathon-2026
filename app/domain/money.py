"""Decimal money helpers. Floats are rejected at the boundary; all rounding is explicit."""
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, InvalidOperation, getcontext

getcontext().prec = 28

SUPPORTED_CURRENCIES = {"INR": 2, "USD": 2, "GBP": 2, "EUR": 2, "CAD": 2, "AUD": 2}


class MoneyError(ValueError):
    pass


def check_currency(ccy: str) -> str:
    c = (ccy or "").upper()
    if c not in SUPPORTED_CURRENCIES:
        raise MoneyError(f"Unsupported currency: {ccy!r}")
    return c


def parse_amount(value) -> Decimal:
    if isinstance(value, float):
        raise MoneyError("Floats are not accepted for money; send a decimal string such as '10000.00'")
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise MoneyError(f"Invalid amount: {value!r}")
    if not d.is_finite():
        raise MoneyError("Amount must be finite")
    return d


def minor_unit(ccy: str) -> Decimal:
    return Decimal(1).scaleb(-SUPPORTED_CURRENCIES[check_currency(ccy)])


def round_half_even(amount: Decimal, ccy: str) -> Decimal:
    return amount.quantize(minor_unit(ccy), rounding=ROUND_HALF_EVEN)


def round_up(amount: Decimal, ccy: str) -> Decimal:
    return amount.quantize(minor_unit(ccy), rounding=ROUND_CEILING)


def round_down(amount: Decimal, ccy: str) -> Decimal:
    return amount.quantize(minor_unit(ccy), rounding=ROUND_FLOOR)


def fmt(amount: Decimal) -> str:
    return format(amount, "f")
