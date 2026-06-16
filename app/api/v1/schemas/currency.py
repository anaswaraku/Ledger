# app/api/v1/schemas/currency.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class MarketPriceBase(BaseModel):
    currency_from: str
    currency_to: str
    price: Decimal
    date: date

    @field_validator("currency_from", "currency_to")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class MarketPriceCreate(MarketPriceBase):
    pass


class MarketPriceResponse(MarketPriceBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ConversionResponse(BaseModel):
    amount: Decimal
    currency_from: str
    currency_to: str
    rate: Decimal
    converted_amount: Decimal
    date: date
