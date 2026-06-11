# app/api/v1/schemas/journal.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JournalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class JournalResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
