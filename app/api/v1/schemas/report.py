from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.api.v1.schemas.account import AccountType

#  Query params 


class ReportQuery(BaseModel):
    """Common query parameters shared across all report endpoints."""

    journal_id: UUID
    as_of: date | None = None  # point-in-time snapshot; defaults to today
    currency: str = "USD"


class DateRangeReportQuery(ReportQuery):
    """For reports that span a period (e.g. income statement)."""

    date_from: date
    date_to: date


#  Shared line item 


class ReportLineItem(BaseModel):
    account_id: UUID
    account_name: str
    account_type: AccountType
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


#  Trial Balance 


class TrialBalanceResponse(BaseModel):
    journal_id: UUID
    as_of: date
    currency: str
    lines: list[ReportLineItem]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


#  Balance Sheet 


class BalanceSheetSection(BaseModel):
    label: str  # e.g. "Assets", "Liabilities", "Equity"
    lines: list[ReportLineItem]
    total: Decimal


class BalanceSheetResponse(BaseModel):
    journal_id: UUID
    as_of: date
    currency: str
    assets: BalanceSheetSection
    liabilities: BalanceSheetSection
    equity: BalanceSheetSection
    is_balanced: bool  # assets == liabilities + equity


#  Income Statement 


class IncomeStatementResponse(BaseModel):
    journal_id: UUID
    date_from: date
    date_to: date
    currency: str
    income: list[ReportLineItem]
    expenses: list[ReportLineItem]
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal  # total_income - total_expenses
