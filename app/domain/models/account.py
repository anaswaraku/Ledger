from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Account(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "accounts"

    journal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType),
        nullable=False,
    )

    journal = relationship(
        "Journal",
        back_populates="accounts",
    )

    entries = relationship(
        "TransactionEntry",
        back_populates="account",
    )
