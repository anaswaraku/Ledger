# app/application/services/budget_service.py
import logging
import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status

from app.application._utils import convert_amount, deduplicate_rates, get_journal_or_404
from app.domain.models.budget import Budget
from app.domain.money import MissingExchangeRateError, MissingExchangeRatesCollectedError
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository

logger = logging.getLogger(__name__)


class BudgetService:
    """Logic for managing budgets."""

    def __init__(
        self,
        budget_repo: BudgetRepository,
        journal_repo: JournalRepository,
        market_price_repo: MarketPriceRepository,
    ) -> None:
        self.budget_repo = budget_repo
        self.journal_repo = journal_repo
        self.market_price_repo = market_price_repo

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _calc_spending(self, budget: Budget) -> dict:
        """
        Calculate how much has been spent against *budget*.

        Accepts a pre-fetched Budget object so callers that already hold one
        (e.g. list_for_journal) can avoid the extra ownership-check round-trip.
        """
        entries = await self.budget_repo.get_spending_entries(
            account_id=budget.account_id,
            start_date=budget.start_date,
            end_date=budget.end_date,
        )

        spend_amount = Decimal("0.0")
        missing_rates: list[dict] = []

        for amount, commodity, _entry_date in entries:
            try:
                converted = await convert_amount(
                    self.market_price_repo, amount, commodity, budget.currency, budget.end_date
                )
                spend_amount += converted
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())

        if missing_rates:
            missing_rates = deduplicate_rates(missing_rates)

        actual_spend = max(Decimal("0.0"), spend_amount)
        return {
            "id": budget.id,
            "budget_amount": budget.amount,
            "currency": budget.currency,
            "spend_amount": actual_spend,
            "difference": budget.amount - actual_spend,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "is_complete": len(missing_rates) == 0,
            "missing_rates": missing_rates if missing_rates else None,
        }

    # ── Public methods ────────────────────────────────────────────────────────

    async def create(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        account_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        period: str,
        start_date: date,
        end_date: date,
    ) -> Budget:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)

        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date.",
            )

        budget = await self.budget_repo.create(
            journal_id=journal_id,
            account_id=account_id,
            amount=amount,
            currency=currency,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )
        logger.info("Budget %s created for journal %s", budget.id, journal_id)
        return budget

    async def get_or_404(
        self, budget_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Budget:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        budget = await self.budget_repo.get_by_id(budget_id, journal_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        return budget

    async def get_budget_with_spending(
        self, budget_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> dict:
        """Fetch a single budget by ID and calculate its spending."""
        budget = await self.get_or_404(budget_id, journal_id, owner_id)
        return await self._calc_spending(budget)

    async def list_for_journal(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[dict]:
        """
        Return all budgets for a journal, each with spending calculated.

        Performs one ownership check upfront then reuses pre-fetched Budget
        objects — no N+1 ownership queries.
        """
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        budgets = await self.budget_repo.list_by_journal(journal_id)
        return [await self._calc_spending(b) for b in budgets]

    async def delete(
        self, budget_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        await self.get_or_404(budget_id, journal_id, owner_id)
        await self.budget_repo.delete(budget_id, journal_id)
        logger.info("Budget %s deleted", budget_id)