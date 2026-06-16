# app/api/v1/schemas/journal.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JournalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    base_currency: str = Field(default="USD", min_length=1, max_length=10)

    @field_validator("base_currency")
    @classmethod
    def base_currency_uppercase(cls, v: str) -> str:
        return v.strip().upper()


class JournalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    base_currency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    base_currency: str | None = Field(default=None, min_length=1, max_length=10)

    @field_validator("base_currency")
    @classmethod
    def base_currency_uppercase(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v
