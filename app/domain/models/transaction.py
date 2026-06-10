from sqlalchemy import String, UUID, TIMESTAMP, ForeignKey, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func
from decimal import Decimal


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)
    journal_id: Mapped[UUID] = mapped_column(
        ForeignKey("journals.id", ondelete="CASCADE")
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500))
    payee: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    transaction_entries: Mapped[list["TransactionEntry"]] = relationship(
        "TransactionEntry", back_populates="transaction", cascade="all, delete-orphan"
    )

    journal: Mapped["Journal"] = relationship("Journal", back_populates="transactions")


class TransactionEntry(Base):
    __tablename__ = "transaction_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, primary_key=True)
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE")
    )
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="transaction_entries"
    )
    account: Mapped["Account"] = relationship(
        "Account", back_populates="transaction_entries"
    )
