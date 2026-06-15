# app/api/v1/schemas/investment.py
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ROIResponse(BaseModel):
    account_id: UUID
    account_name: str
    commodity: str
    units: Decimal
    average_cost_basis: Decimal
    current_price: Decimal
    cost_basis: Decimal
    current_value: Decimal
    net_gain: Decimal
    roi: Decimal  # ratio, e.g. 0.15 for 15%
