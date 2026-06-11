# app/domain/models/market_price.py
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin


class MarketPrice(UUIDMixin, Base):
    """Historical exchange rate between two commodities on a given date."""

    __tablename__ = "market_prices"

    __table_args__ = (
        UniqueConstraint(
            "currency_from",
            "currency_to",
            "date",
            name="uq_market_price_date",
        ),
        Index("ix_market_price_lookup", "currency_from", "currency_to", "date"),
    )

    currency_from: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    currency_to: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(28, 10),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
