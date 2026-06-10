from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class TransactionEntry(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "transaction_entries"

    transaction_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )

    account_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
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

    transaction = relationship(
        "Transaction",
        back_populates="entries",
    )

    account = relationship(
        "Account",
        back_populates="entries",
    )
