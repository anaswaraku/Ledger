# app/api/v1/routers/charts.py
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.chart import (
    BalanceTrendResponse,
    ExpenseBreakdownResponse,
    MonthlyOverviewResponse,
)
from app.application.services.chart_service import ChartService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.chart_repo import ChartRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

router = APIRouter(prefix="/api/v1/charts", tags=["Charts"])


def _make_chart_service(db: AsyncSession) -> ChartService:
    return ChartService(
        chart_repo=ChartRepository(db),
        journal_repo=JournalRepository(db),
    )


@router.get(
    "/monthly-overview",
    response_model=MonthlyOverviewResponse,
    summary="Get monthly income vs expenses overview",
)
async def get_monthly_overview(
    journal_id: uuid.UUID = Query(...),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlyOverviewResponse:
    return await _make_chart_service(db).get_monthly_overview(
        owner_id=current_user.id,
        journal_id=journal_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/balance-trend",
    response_model=BalanceTrendResponse,
    summary="Get assets, liabilities and net worth balance trend",
)
async def get_balance_trend(
    journal_id: uuid.UUID = Query(...),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BalanceTrendResponse:
    return await _make_chart_service(db).get_balance_trend(
        owner_id=current_user.id,
        journal_id=journal_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/expense-breakdown",
    response_model=ExpenseBreakdownResponse,
    summary="Get breakdown of expenses by account",
)
async def get_expense_breakdown(
    journal_id: uuid.UUID = Query(...),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExpenseBreakdownResponse:
    return await _make_chart_service(db).get_expense_breakdown(
        owner_id=current_user.id,
        journal_id=journal_id,
        date_from=date_from,
        date_to=date_to,
    )
