# app/application/services/chart_service.py
import logging
import uuid
from collections import defaultdict
from datetime import date as date_type
from decimal import Decimal

from fastapi import HTTPException, status

from app.api.v1.schemas.chart import (
    BalanceTrendResponse,
    ExpenseBreakdownResponse,
    MonthlyOverviewResponse,
)
from app.domain.models.account import AccountType
from app.infrastructure.db.repositories.chart_repo import ChartRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

logger = logging.getLogger(__name__)


class ChartService:
    """Business logic for generating activity charts data."""

    def __init__(
        self, chart_repo: ChartRepository, journal_repo: JournalRepository
    ) -> None:
        self.chart_repo = chart_repo
        self.journal_repo = journal_repo

    async def _verify_journal_owner(self, journal_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )

    async def get_monthly_overview(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
    ) -> MonthlyOverviewResponse:
        await self._verify_journal_owner(journal_id, owner_id)
        postings = await self.chart_repo.get_postings_for_charts(
            journal_id, date_from=date_from, date_to=date_to
        )

        monthly_income = defaultdict(Decimal)
        monthly_expense = defaultdict(Decimal)
        all_months = set()

        for p in postings:
            month_str = p["date"].strftime("%Y-%m")
            all_months.add(month_str)
            if p["account_type"] == AccountType.INCOME:
                # Income is naturally negative, flip to positive
                monthly_income[month_str] += -p["amount"]
            elif p["account_type"] == AccountType.EXPENSE:
                monthly_expense[month_str] += p["amount"]

        sorted_months = sorted(list(all_months))
        income_list = [monthly_income[m] for m in sorted_months]
        expense_list = [monthly_expense[m] for m in sorted_months]

        return MonthlyOverviewResponse(
            labels=sorted_months,
            income=income_list,
            expenses=expense_list,
        )

    async def get_balance_trend(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
    ) -> BalanceTrendResponse:
        await self._verify_journal_owner(journal_id, owner_id)
        # Fetch all postings from the beginning up to date_to to get correct running balances
        postings = await self.chart_repo.get_postings_for_charts(
            journal_id, date_from=None, date_to=date_to
        )

        daily_assets = defaultdict(Decimal)
        daily_liabilities = defaultdict(Decimal)
        all_dates = set()

        for p in postings:
            d_str = p["date"].isoformat()
            if date_from is None or p["date"] >= date_from:
                all_dates.add(d_str)

            if p["account_type"] == AccountType.ASSET:
                daily_assets[d_str] += p["amount"]
            elif p["account_type"] == AccountType.LIABILITY:
                # Liabilities are credit-normal (negative), flip to positive for display
                daily_liabilities[d_str] += -p["amount"]

        sorted_dates = sorted(list(all_dates))
        
        # Calculate running balances
        running_asset = Decimal("0.0")
        running_liability = Decimal("0.0")

        # To handle correct running totals from before date_from
        all_sorted_dates = sorted(list({p["date"].isoformat() for p in postings}))
        running_balances = {}
        for d in all_sorted_dates:
            running_asset += daily_assets.get(d, Decimal("0.0"))
            running_liability += daily_liabilities.get(d, Decimal("0.0"))
            running_balances[d] = (running_asset, running_liability)

        assets_list = []
        liabilities_list = []
        net_worth_list = []

        for d in sorted_dates:
            ras, rli = running_balances.get(d, (Decimal("0.0"), Decimal("0.0")))
            assets_list.append(ras)
            liabilities_list.append(rli)
            net_worth_list.append(ras - rli)

        return BalanceTrendResponse(
            labels=sorted_dates,
            assets=assets_list,
            liabilities=liabilities_list,
            net_worth=net_worth_list,
        )

    async def get_expense_breakdown(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
    ) -> ExpenseBreakdownResponse:
        await self._verify_journal_owner(journal_id, owner_id)
        postings = await self.chart_repo.get_postings_for_charts(
            journal_id, date_from=date_from, date_to=date_to
        )

        expense_groups = defaultdict(Decimal)

        for p in postings:
            if p["account_type"] == AccountType.EXPENSE:
                expense_groups[p["account_name"]] += p["amount"]

        # Sort breakdown by value descending
        sorted_items = sorted(expense_groups.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        return ExpenseBreakdownResponse(
            labels=labels,
            values=values,
        )
