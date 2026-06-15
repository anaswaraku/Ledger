from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.report import BalanceSheetResponse, IncomeStatementResponse, CashFlowStatementResponse, NetWorthResponse
from app.application.services.report_service import ReportService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


def _make_report_service(db: AsyncSession) -> ReportService:
    return ReportService(
        report_repo=ReportRepository(db),
        journal_repo=JournalRepository(db),
    )


@router.get(
    "/balance-sheet",
    response_model=BalanceSheetResponse,
    summary="Generate a balance sheet report",
)
async def get_balance_report(
    journal_id: UUID = Query(...),
    date: date | None = Query(default=None, description="As of date (default: today)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceSheetResponse:
    """Returns a balance sheet snapshot at the given date."""
    from datetime import date as date_type
    as_of = date or date_type.today()
    return await _make_report_service(db).generate_balance_sheet(
        owner_id=current_user.id,
        journal_id=journal_id,
        as_of=as_of,
    )


@router.get(
    "/income-statement",
    response_model=IncomeStatementResponse,
    summary="Generate an income statement report",
)
async def get_income_report(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncomeStatementResponse:
    """Returns an income statement for a specific period."""
    return await _make_report_service(db).generate_income_statement(
        owner_id=current_user.id,
        journal_id=journal_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/cash-flow", response_model=CashFlowStatementResponse, summary="Generate cash-flow report",)
async def get_cash_flow(
    journal_id: UUID = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
)->CashFlowStatementResponse:
    """Cash Flow Report-for specific period"""
    # /api/v1/reports/cash-flow
    return await _make_report_service(db).generate_cash_flow(
        owner_id=current_user.id,
        journal_id=journal_id,
        date_from=date_from,
        date_to=date_to
    )


from app.api.v1.schemas.investment import ROIResponse

@router.get(
    "/roi",
    response_model=list[ROIResponse],
    summary="Generate a Return on Investment (ROI) report",
)
async def get_roi_report(
    journal_id: UUID = Query(...),
    account_id: UUID | None = Query(default=None),
    date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ROIResponse]:
    """Returns the Return on Investment (ROI) details for investment accounts."""
    return await _make_report_service(db).generate_roi_report(
        owner_id=current_user.id,
        journal_id=journal_id,
        account_id=account_id,
        as_of=date,
    )  # type: ignore[return-value]

@router.get("/net-worth", response_model=NetWorthResponse)
async def get_net_worth(
    db:AsyncSession=Depends(get_db),
    current_user: User = Depends(get_current_user),
)->NetWorthResponse:
    """For networth for display"""
    return await _make_report_service(db).get_net_worth(current_user)