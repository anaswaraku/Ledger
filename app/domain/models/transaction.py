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
