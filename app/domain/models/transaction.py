from datetime import date

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Transaction(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "transactions"

    journal_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
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
    )

    payee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    journal = relationship(
        "Journal",
        back_populates="transactions",
    )

    entries = relationship(
        "TransactionEntry",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
