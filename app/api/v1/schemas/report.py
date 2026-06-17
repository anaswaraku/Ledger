from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.api.v1.schemas.account import AccountType

#  Balance Sheet
class BalanceSheetResponse(BaseModel):
    date: date
    assets: dict[str, Decimal]
    liabilities: dict[str, Decimal]
    equity: dict[str, Decimal]
    net: Decimal


#  Income Statement 
class IncomeStatementResponse(BaseModel):
    date_from: date
    date_to: date
    income: dict[str, Decimal]
    expenses: dict[str, Decimal]
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal

#movement of cash over a specific period
class CashFlowStatementResponse(BaseModel):
    date_from: date
    date_to: date
    beginning_balance: Decimal
    inflows: dict[str, Decimal]
    outflows: dict[str, Decimal]
    net_cash_flow: Decimal
    ending_balance: Decimal

#networth
class NetWorthResponse(BaseModel):
    assets:Decimal
    liabilities:Decimal
    net_worth:Decimal


#monthly_income
class MonthlyIncomeResponse(BaseModel):
    monthly_income:Decimal

# ROI Report
class ROIAssetResponse(BaseModel):
    account_name: str
    commodity: str
    cost_commodity: str
    quantity: Decimal
    cost_basis: Decimal
    current_value: Decimal
    gain: Decimal
    roi_percent: Decimal

class ROIReportResponse(BaseModel):
    date: date
    assets: list[ROIAssetResponse]
    is_complete: bool
    missing_rates: list[dict] | None = None

