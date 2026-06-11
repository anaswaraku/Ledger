# app/domain/models/account.py
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.journal import Journal
    from app.domain.models.transaction_entry import TransactionEntry


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Account(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    __table_args__ = (
        UniqueConstraint(
            "journal_id",
            "name",
            name="uq_account_journal_name",
        ),
    )

    journal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SAEnum(AccountType, native_enum=False),
        nullable=False,
    )

    # Relationships
    journal: Mapped["Journal"] = relationship(
        "Journal",
        back_populates="accounts",
    )

    entries: Mapped[list["TransactionEntry"]] = relationship(
        "TransactionEntry",
        back_populates="account",
    )
