from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import UUIDMixin, TimestampMixin


class Journal(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "journals"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    owner_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    accounts = relationship(
        "Account",
        back_populates="journal",
        cascade="all, delete-orphan",
    )

    transactions = relationship(
        "Transaction",
        back_populates="journal",
        cascade="all, delete-orphan",
    )
