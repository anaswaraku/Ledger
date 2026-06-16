# app/domain/models/journal.py
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.account import Account
    from app.domain.models.transaction import Transaction


class Journal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "journals"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    base_currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="journals",
    )

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="journal",
        cascade="all, delete-orphan",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="journal",
        cascade="all, delete-orphan",
    )
