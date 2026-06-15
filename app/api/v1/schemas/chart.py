# app/api/v1/schemas/chart.py
from decimal import Decimal
from pydantic import BaseModel


class MonthlyOverviewResponse(BaseModel):
    labels: list[str]
    income: list[Decimal]
    expenses: list[Decimal]


class BalanceTrendResponse(BaseModel):
    labels: list[str]
    assets: list[Decimal]
    liabilities: list[Decimal]
    net_worth: list[Decimal]


class ExpenseBreakdownResponse(BaseModel):
    labels: list[str]
    values: list[Decimal]
