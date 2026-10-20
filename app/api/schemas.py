from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator

from ..domain.money import MoneyError, check_currency, parse_amount


class _PaymentBase(BaseModel):
    account_id: str = Field(..., min_length=1, max_length=64)
    target_receive_amount: str = Field(..., description="Decimal string, e.g. '10000.00'", examples=["10000.00"])
    receive_currency: str = Field(..., min_length=3, max_length=3)
    send_currency: str | None = Field(default=None, min_length=3, max_length=3)
    due_date: date

    @field_validator("target_receive_amount")
    @classmethod
    def _amount(cls, v: str) -> str:
        try:
            d = parse_amount(v)
        except MoneyError as exc:
            raise ValueError(str(exc))
        if d <= 0:
            raise ValueError("target_receive_amount must be positive")
        if d > 10_000_000:
            raise ValueError("target_receive_amount is implausibly large")
        return v

    @field_validator("receive_currency", "send_currency")
    @classmethod
    def _ccy(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            return check_currency(v)
        except MoneyError as exc:
            raise ValueError(str(exc))


class CompareRequest(_PaymentBase):
    question: str | None = Field(default=None, max_length=500)


class PrepareRequest(_PaymentBase):
    beneficiary_id: str = Field(..., min_length=1, max_length=64)
    provider_id: str = Field(..., min_length=1, max_length=64)
    memo: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(..., min_length=8, max_length=128)


class NoteRequest(BaseModel):
    note: str | None = Field(default=None, max_length=300)
