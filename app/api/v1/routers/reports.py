from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/balance-sheet")
def get_balance_report():
    """Balance sheet"""
    # /api/v1/reports/balance-sheet
    return "balance sheet"


@router.get("/income-statement")
def get_income_statement():
    """Income Statement"""
    return "income statement"


@router.get("/cash-flow")
def get_cash_flow():
    """Cash Flow Report"""
    # /api/v1/reports/cash-flow
    return "cash flow"
