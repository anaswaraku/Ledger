# app/infrastructure/db/repositories/market_price_repo.py
import uuid
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.market_price import MarketPrice


class MarketPriceRepository:
    """Data-access layer for the MarketPrice entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, price_id: uuid.UUID) -> MarketPrice | None:
        result = await self.db.execute(
            select(MarketPrice).where(MarketPrice.id == price_id)
        )
        return result.scalar_one_or_none()

    async def get_price(
        self, currency_from: str, currency_to: str, date: date_type
    ) -> MarketPrice | None:
        """Find the closest market price on or before the given date, or fallback to the closest after."""
        # 1. On or before
        stmt = (
            select(MarketPrice)
            .where(
                MarketPrice.currency_from == currency_from,
                MarketPrice.currency_to == currency_to,
                MarketPrice.date <= date,
            )
            .order_by(MarketPrice.date.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        price = res.scalar_one_or_none()
        if price:
            return price

        # 2. After
        stmt = (
            select(MarketPrice)
            .where(
                MarketPrice.currency_from == currency_from,
                MarketPrice.currency_to == currency_to,
                MarketPrice.date > date,
            )
            .order_by(MarketPrice.date.asc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_rate(
        self, currency_from: str, currency_to: str, date: date_type
    ) -> Decimal | None:
        """Get exchange rate from/to, checking direct rate and reciprocal reverse rate."""
        c_from = currency_from.upper()
        c_to = currency_to.upper()
        if c_from == c_to:
            return Decimal("1.0")

        # Try direct
        p = await self.get_price(c_from, c_to, date)
        if p:
            return p.price

        # Try reverse
        p_rev = await self.get_price(c_to, c_from, date)
        if p_rev and p_rev.price != Decimal("0.0"):
            return Decimal("1.0") / p_rev.price

        return None

    async def create_or_update(
        self, currency_from: str, currency_to: str, price: Decimal, date: date_type
    ) -> MarketPrice:
        """Upsert a market price for a given date."""
        c_from = currency_from.upper()
        c_to = currency_to.upper()
        
        # Check if exists
        stmt = select(MarketPrice).where(
            MarketPrice.currency_from == c_from,
            MarketPrice.currency_to == c_to,
            MarketPrice.date == date,
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.price = price
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        new_price = MarketPrice(
            currency_from=c_from,
            currency_to=c_to,
            price=price,
            date=date,
        )
        self.db.add(new_price)
        await self.db.commit()
        await self.db.refresh(new_price)
        return new_price

    async def list_prices(self, skip: int = 0, limit: int = 100) -> list[MarketPrice]:
        stmt = (
            select(MarketPrice)
            .order_by(MarketPrice.date.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete(self, price_id: uuid.UUID) -> bool:
        stmt = delete(MarketPrice).where(MarketPrice.id == price_id)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return (res.rowcount or 0) > 0
