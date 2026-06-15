# app/api/v1/schemas/budget.py
from datetime import date as date_type, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    journal_id: UUID
    account_id: UUID
    amount: Decimal = Field(..., gt=0, description="Budgeted target amount")
    period: str = Field(default="monthly", description="Budget period (e.g., monthly, yearly)")
    start_date: date_type = Field(..., description="Start date of the budget period")
    end_date: date_type = Field(..., description="End date of the budget period")


class BudgetUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    period: str | None = None
    start_date: date_type | None = None
    end_date: date_type | None = None


class BudgetResponse(BaseModel):
    id: UUID
    journal_id: UUID
    account_id: UUID
    account_name: str
    amount: Decimal
    period: str
    start_date: date_type
    end_date: date_type
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetVarianceResponse(BaseModel):
    budget_id: UUID
    account_id: UUID
    account_name: str
    period: str
    start_date: date_type
    end_date: date_type
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance: Decimal  # budgeted_amount - actual_amount (positive = favorable for expenses)
    is_favorable: bool
