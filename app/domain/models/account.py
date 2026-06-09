from sqlalchemy import String, UUID, TIMESTAMP, ForeignKey,Numeric, Date
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.db import Base
import uuid
from datetime import datetime
from sqlalchemy.sql import func

class User(Base):
    __tablename__="users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        default=uuid.uuid4,
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    journals: Mapped[list["Journal"]] = relationship("Journal", back_populates="user")

class Accounts(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        default=uuid.uuid4,
        primary_key=True
    )
    journal_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "journals.id",ondelete="CASCADE"
        )
    )
    name: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False
    )

    account_type: Mapped[str] = mapped_column(
        String(50)
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )

    journal: Mapped["Journal"] =  relationship(
        "Journal",
        back_populates="accounts"
    )

class MarketPrices(Base):
    __tablename__="marketprices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        default=uuid.uuid4,
        primary_key=True
    )
    currency_from: Mapped[str] = mapped_column(
        String(3)
    )
    currency_to: Mapped[str] = mapped_column(
        String(3)
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(28, 10),
        nullable=False
    )

    date: Mapped[datetime] = mapped_column(
        Date, nullable=False
    )