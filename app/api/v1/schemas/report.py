from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.api.v1.schemas.account import AccountType

#  Query params 






#  Shared line item 




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

class NetWorthResponse(BaseModel):
    assets:Decimal
    liabilities:Decimal
    net_worth:Decimal