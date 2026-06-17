from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

class BudgetCreate(BaseModel):
    account_id:UUID
    amount: Decimal
    period: str
    start_date: date
    end_date:date

class BudgetResponse(BaseModel):
    id: UUID
    budget_amount:Decimal
    spend_amount: Decimal
    difference: Decimal
    start_date: date
    end_date:date

    model_config=ConfigDict(from_attributes=True)

