# app/application/services/currency_service.py
import logging
import uuid
from datetime import date as date_type
from decimal import Decimal

from fastapi import HTTPException, status

from app.api.v1.schemas.currency import MarketPriceCreate, ConversionResponse
from app.domain.models.market_price import MarketPrice
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

logger = logging.getLogger(__name__)


class CurrencyService:
    """Business logic for historical currency rates and conversions."""

    def __init__(self, market_price_repo: MarketPriceRepository) -> None:
        self.market_price_repo = market_price_repo

    async def add_price(self, data: MarketPriceCreate) -> MarketPrice:
        price = await self.market_price_repo.create_or_update(
            currency_from=data.currency_from,
            currency_to=data.currency_to,
            price=data.price,
            date=data.date,
        )
        logger.info(
            "Market price added/updated: %s -> %s = %s on %s",
            data.currency_from,
            data.currency_to,
            data.price,
            data.date,
        )
        return price

    async def list_prices(self, skip: int = 0, limit: int = 100) -> list[MarketPrice]:
        return await self.market_price_repo.list_prices(skip=skip, limit=limit)

    async def delete_price(self, price_id: uuid.UUID) -> None:
        deleted = await self.market_price_repo.delete(price_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market price not found.",
            )
        logger.info("Market price %s deleted", price_id)

    async def convert(
        self, amount: Decimal, currency_from: str, currency_to: str, date: date_type
    ) -> ConversionResponse:
        rate = await self.market_price_repo.get_rate(
            currency_from=currency_from,
            currency_to=currency_to,
            date=date,
        )
        if rate is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exchange rate not found for {currency_from} -> {currency_to} on or near {date}.",
            )

        converted_amount = amount * rate
        return ConversionResponse(
            amount=amount,
            currency_from=currency_from,
            currency_to=currency_to,
            rate=rate,
            converted_amount=converted_amount,
            date=date,
        )
