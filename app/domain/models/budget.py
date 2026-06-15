# app/domain/models/budget.py
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.journal import Journal
    from app.domain.models.account import Account


class Budget(UUIDMixin, TimestampMixin, Base):
    """Budget target for an account in a journal."""

    __tablename__ = "budgets"

    journal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("journals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(28, 10),
        nullable=False,
    )

    period: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="monthly",  # monthly, yearly, etc.
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Relationships
    journal: Mapped["Journal"] = relationship("Journal")
    account: Mapped["Account"] = relationship("Account")

    @property
    def account_name(self) -> str:
        return self.account.name if self.account else ""
