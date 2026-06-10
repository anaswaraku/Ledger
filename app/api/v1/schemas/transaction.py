from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

#  Transaction Entry 


class TransactionEntryBase(BaseModel):
    account_id: UUID
    amount: Decimal
    currency: str = "USD"

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("amount must not be zero")
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


#  Transaction 


class TransactionBase(BaseModel):
    date: date
    description: str | None = None
    payee: str | None = None
    code: str | None = None


class TransactionCreate(TransactionBase):
    journal_id: UUID
    entries: list[TransactionEntryCreate]

    @field_validator("entries")
    @classmethod
    def validate_double_entry(
        cls, entries: list[TransactionEntryCreate]
    ) -> list[TransactionEntryCreate]:
        """Enforce double-entry: debits must equal credits (net sum == 0)."""
        if len(entries) < 2:
            raise ValueError("a transaction must have at least 2 entries")
        total = sum(e.amount for e in entries)
        if total != 0:
            raise ValueError(
                f"transaction entries must balance to zero (current sum: {total})"
            )
        return entries


class TransactionUpdate(BaseModel):
    date: date | None = None
    description: str | None = None
    payee: str | None = None
    code: str | None = None


class TransactionResponse(TransactionBase):
    id: UUID
    journal_id: UUID
    created_at: datetime
    entries: list[TransactionEntryResponse] = []

    model_config = ConfigDict(from_attributes=True)
