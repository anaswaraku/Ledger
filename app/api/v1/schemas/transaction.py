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
    cost_amount: Decimal | None=None
    cost_currency:str | None=None

    @field_validator("currency")
    @classmethod
    def currency_uppercase(_cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("amount")
    @classmethod
    def amount_not_zero(_cls, v: Decimal) -> Decimal:
        if v == 0:
            raise ValueError("Entry amount must not be zero.")
        return v


class TransactionEntryCreate(TransactionEntryBase):
    pass


class TransactionEntryResponse(TransactionEntryBase):
    id: UUID
    transaction_id: UUID
    account_name: str | None = None

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
        _cls, entries: list[TransactionEntryCreate],
    ) -> list[TransactionEntryCreate]:
        """
        Validate that transaction entries satisfy double-entry balancing rules.
        """
        if len(entries) < 2:
            raise ValueError(f"A transaction must have at least 2 entries, got {len(entries)}.")

        balances: dict[str, Decimal] = {}
        for e in entries:
            if e.cost_amount is not None and e.cost_currency is not None:
               
                cost_val = e.amount* abs(e.cost_amount)
                curr = e.cost_currency.strip().upper()
                balances[curr] = balances.get(curr, Decimal("0")) + cost_val
            else:
                curr = e.currency.strip().upper()
                balances[curr] = balances.get(curr, Decimal("0")) + e.amount

        for curr, total in balances.items():
            if total != Decimal("0"):
                raise ValueError(f"Transaction does not balance for currency {curr}. Imbalance: {total:+.10f}")
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

