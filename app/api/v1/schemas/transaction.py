# app/api/v1/schemas/transaction.py
from datetime import date as date_type, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.rules.double_entry import DoubleEntryError, validate_double_entry


# ── Transaction Entry ─────────────────────────────────────────────────────────

class TransactionEntryBase(BaseModel):
    account_id: UUID
    amount: Decimal
    currency: str = "USD"

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Entry amount must not be zero.")
        return v


class TransactionEntryCreate(TransactionEntryBase):
    pass


class TransactionEntryUpdate(BaseModel):
    account_id: UUID | None = None
    amount: Decimal | None = None
    currency: str | None = None


class TransactionEntryResponse(TransactionEntryBase):
    id: UUID
    transaction_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    date: date_type
    description: str | None = None
    payee: str | None = None
    code: str | None = None


class TransactionCreate(TransactionBase):
    journal_id: UUID
    entries: list[TransactionEntryCreate]

    @field_validator("entries")
    @classmethod
    def validate_entries_double_entry(
        cls, entries: list[TransactionEntryCreate],
    ) -> list[TransactionEntryCreate]:
        """
        Delegate to the domain rule — single source of truth.
        Converts DoubleEntryError → ValueError so Pydantic renders it as a
        422 validation error with a clear message.
        """
        try:
            validate_double_entry([e.amount for e in entries])
        except DoubleEntryError as exc:
            raise ValueError(str(exc))
        return entries


class TransactionUpdate(BaseModel):
    date: date_type | None = None
    description: str | None = None
    payee: str | None = None
    code: str | None = None


class TransactionResponse(TransactionBase):
    id: UUID
    journal_id: UUID
    created_at: datetime
    entries: list[TransactionEntryResponse] = []

    model_config = ConfigDict(from_attributes=True)
