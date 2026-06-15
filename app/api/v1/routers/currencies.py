# app/api/v1/routers/currencies.py
import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.currency import ConversionResponse, MarketPriceCreate, MarketPriceResponse
from app.application.services.currency_service import CurrencyService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

router = APIRouter(prefix="/api/v1/currencies", tags=["Currencies"])


def _make_currency_service(db: AsyncSession) -> CurrencyService:
    return CurrencyService(MarketPriceRepository(db))


@router.post(
    "/prices",
    response_model=MarketPriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or update a historical market price",
)
async def add_price(
    data: MarketPriceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MarketPriceResponse:
    return await _make_currency_service(db).add_price(data)  # type: ignore[return-value]


@router.get(
    "/prices",
    response_model=list[MarketPriceResponse],
    summary="List all historical market prices",
)
async def list_prices(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MarketPriceResponse]:
    return await _make_currency_service(db).list_prices(skip=skip, limit=limit)  # type: ignore[return-value]


@router.delete(
    "/prices/{price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a historical market price",
)
async def delete_price(
    price_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _make_currency_service(db).delete_price(price_id)


@router.get(
    "/convert",
    response_model=ConversionResponse,
    summary="Convert between currencies on a specific date",
)
async def convert_currency(
    amount: Decimal = Query(..., description="Amount to convert"),
    currency_from: str = Query(..., min_length=1, max_length=10),
    currency_to: str = Query(..., min_length=1, max_length=10),
    date_query: date | None = Query(default=None, alias="date", description="Date of rate (default: today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversionResponse:
    as_of = date_query or date.today()
    return await _make_currency_service(db).convert(
        amount=amount,
        currency_from=currency_from,
        currency_to=currency_to,
        date=as_of,
    )
