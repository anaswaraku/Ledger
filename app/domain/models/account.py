from sqlalchemy import String, UUID, TIMESTAMP, ForeignKey, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func
from enum import Enum


class AccountType(str, Enum):
    ASSETS ="Assets"
    LIABILITIES = "Liabilities"
    EQUITY = "Equity"
    INCOME = "Income"
    EXPENSES = "Expenses"

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)
    journal_id: Mapped[UUID] = mapped_column(
        ForeignKey("journals.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)

    account_type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    journal: Mapped["Journal"] = relationship("Journal", back_populates="accounts")
    transaction_entries: Mapped[list["TransactionEntry"]] = relationship(
        "TransactionEntry", back_populates="account"
    )
