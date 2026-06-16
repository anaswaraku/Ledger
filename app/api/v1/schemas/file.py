# app/api/v1/schemas/file.py
from uuid import UUID

from pydantic import BaseModel, Field


class CSVImportRowError(BaseModel):
    row: int
    message: str


class CSVImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[CSVImportRowError] = []
