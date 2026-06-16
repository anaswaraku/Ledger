# app/domain/models/transaction.py
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.journal import Journal
    from app.domain.models.transaction_entry import TransactionEntry


class Transaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    __table_args__ = (
        Index("ix_transaction_journal_date", "journal_id", "date"),
        Index("ix_transaction_payee", "payee"),
    )

    journal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    payee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationships
    journal: Mapped["Journal"] = relationship(
        "Journal",
        back_populates="transactions",
    )

    entries: Mapped[list["TransactionEntry"]] = relationship(
        "TransactionEntry",
        back_populates="transaction",
        cascade="all, delete-orphan",
        lazy="selectin",  # auto-load entries for async sessions
    )

    def balance(self)->bool:
        from app.domain.money import Money, UnbalancedTransactionError
        from decimal import Decimal

        balances: dict[str, Money]={}

        for entry in self.entries:
            value = entry.cost_amount if entry.cost_money else entry.money

            if value.currency in balances:
                balances[value.currency]+=value
            else:
                balances[value.currency]=value

        for curr, total in self.balances.items():
            if total.amount !=Decimal("0"):
                raise UnbalancedTransactionError(
                    f"Transaction does not balance. Currency {curr} has non zero {total.amount}"
                )
        return True
