# app/domain/models/transaction_entry.py
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin

if TYPE_CHECKING:
    from app.domain.models.transaction import Transaction
    from app.domain.models.account import Account


class TransactionEntry(UUIDMixin, Base):
    """
    A single posting in a double-entry transaction.
    Two or more entries make up one transaction; they must sum to zero.
    """

    __tablename__ = "transaction_entries"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(28, 10),
        nullable=False,
    )

    commodity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USD",
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="entries",
    )

    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="entries",
    )
