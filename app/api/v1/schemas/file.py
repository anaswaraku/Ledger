# app/api/v1/schemas/file.py
from uuid import UUID

from pydantic import BaseModel, Field


class CSVImportRequest(BaseModel):
    """Metadata sent alongside the uploaded CSV file."""

    journal_id: UUID
    debit_account_id: UUID = Field(
        ..., description="Default account to debit (e.g. expenses:unknown)"
    )
    credit_account_id: UUID = Field(
        ..., description="Default account to credit (e.g. assets:checking)"
    )


class CSVImportRowError(BaseModel):
    row: int
    message: str


class CSVImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[CSVImportRowError] = []
