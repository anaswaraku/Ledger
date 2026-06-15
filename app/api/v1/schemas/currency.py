# app/api/v1/schemas/currency.py
from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MarketPriceCreate(BaseModel):
    currency_from: str = Field(..., min_length=1, max_length=10, description="Source currency code (e.g., USD)")
    currency_to: str = Field(..., min_length=1, max_length=10, description="Target currency code (e.g., EUR)")
    price: Decimal = Field(..., gt=0, description="Exchange rate (1 currency_from = X currency_to)")
    date: date_type = Field(..., description="Date of the exchange rate")


class MarketPriceResponse(BaseModel):
    id: UUID
    currency_from: str
    currency_to: str
    price: Decimal
    date: date_type

    model_config = ConfigDict(from_attributes=True)


class ConversionResponse(BaseModel):
    amount: Decimal
    currency_from: str
    currency_to: str
    rate: Decimal
    converted_amount: Decimal
    date: date_type
