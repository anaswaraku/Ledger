from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

class BudgetCreate(BaseModel):
    account_id:UUID
    amount: Decimal
    currency: str
    period: str
    start_date: date
    end_date:date

class BudgetResponse(BaseModel):
    id: UUID
    budget_amount:Decimal
    currency: str
    spend_amount: Decimal
    difference: Decimal
    start_date: date
    end_date:date
    is_complete: bool
    missing_rates: list[dict] | None = None

    model_config=ConfigDict(from_attributes=True)

