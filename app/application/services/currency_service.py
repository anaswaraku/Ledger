# app/application/services/currency_service.py
import uuid
from datetime import date as date_type
from decimal import Decimal

from fastapi import HTTPException, status

from app.api.v1.schemas.currency import ConversionResponse, MarketPriceCreate
from app.domain.models.market_price import MarketPrice
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository


class CurrencyService:
    """Logic for historical exchange rates and currency conversion."""

    def __init__(self, repo: MarketPriceRepository) -> None:
        self.repo = repo

    async def add_price(self, data: MarketPriceCreate) -> MarketPrice:
        if data.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Price must be positive.",
            )
        return await self.repo.create_or_update(
            currency_from=data.currency_from,
            currency_to=data.currency_to,
            price=data.price,
            date=data.date,
        )

    async def list_prices(self, skip: int = 0, limit: int = 100) -> list[MarketPrice]:
        return await self.repo.list_prices(skip=skip, limit=limit)

    async def delete_price(self, price_id: uuid.UUID) -> None:
        deleted = await self.repo.delete(price_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market price not found.",
            )

    async def convert(
        self,
        amount: Decimal,
        currency_from: str,
        currency_to: str,
        date: date_type,
    ) -> ConversionResponse:
        rate = await self.repo.get_rate(currency_from, currency_to, date)
        if rate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exchange rate from {currency_from} to {currency_to} not found for date {date}.",
            )
        converted_amount = amount * rate
        return ConversionResponse(
            amount=amount,
            currency_from=currency_from.upper(),
            currency_to=currency_to.upper(),
            rate=rate,
            converted_amount=converted_amount,
            date=date,
        )
