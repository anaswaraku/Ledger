# app/application/services/budget_service.py
import logging
import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status

from app.domain.models.budget import Budget
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository
from app.domain.money import MissingExchangeRateError, MissingExchangeRatesCollectedError

logger = logging.getLogger(__name__)

class BudgetService:
    """Business logic for managing budgets."""

    def __init__(
        self, 
        budget_repo: BudgetRepository, 
        journal_repo: JournalRepository,
        account_repo: AccountRepository = None,
        market_price_repo: MarketPriceRepository = None
    ) -> None:
        self.budget_repo = budget_repo
        self.journal_repo = journal_repo
        self.account_repo = account_repo
        self.market_price_repo = market_price_repo

    async def _convert_amount(
        self, amount: Decimal, from_currency: str, to_currency: str, as_of: date
    ) -> Decimal:
        """Converts currency using the historical market price repository."""
        if from_currency.upper() == to_currency.upper():
            return amount
            
        rate = await self.market_price_repo.get_rate(from_currency, to_currency, as_of)
        if rate is None:
            logger.error(
                "Missing exchange rate: %s -> %s on %s for amount %s",
                from_currency, to_currency, as_of, amount
            )
            raise MissingExchangeRateError(from_currency, to_currency, as_of, amount)
            
        return amount * rate

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
        # 1. Security Check: Does the user own this journal?
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )

        # 2. Validation: Dates must make sense
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date."
            )

        # 3. Create the budget
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
        # Verify journal ownership first
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found."
            )

        # Fetch the budget
        budget = await self.budget_repo.get_by_id(budget_id, journal_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found."
            )
        return budget

    async def get_budget_with_spending(
        self, budget_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> dict:
        """
        Fetches a budget and calculates exactly how much has been spent,
        converting all transaction currencies into the Budget's specific currency.
        """
        # 1. Get the budget
        budget = await self.get_or_404(budget_id, journal_id, owner_id)

        # 2. Ask the repository for actual spending entries
        entries = await self.budget_repo.get_spending_entries(
            account_id=budget.account_id,
            start_date=budget.start_date,
            end_date=budget.end_date
        )

        spend_amount = Decimal("0.0")
        missing_rates = []

        # 3. Loop through each entry, convert currency, and sum up
        for amount, commodity, entry_date in entries:
            try:
                converted = await self._convert_amount(amount, commodity, budget.currency, budget.end_date)
                spend_amount += converted
            except MissingExchangeRateError as e:
                missing_rates.append(e.to_dict())

        # If any exchange rates are missing, deduplicate them for the UI
        if missing_rates:
            from app.application.services.report_service import _deduplicate
            missing_rates = _deduplicate(missing_rates)

        # Expense entries represent negative outflows. Use max to gracefully handle net-positive refunds.
        actual_spend = max(Decimal("0.0"), -spend_amount)
        difference = budget.amount - actual_spend
        is_complete = len(missing_rates) == 0

        return {
            "id": budget.id,
            "budget_amount": budget.amount,
            "currency": budget.currency,
            "spend_amount": actual_spend,
            "difference": difference,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "is_complete": is_complete,
            "missing_rates": missing_rates if missing_rates else None
        }

    async def list_for_journal(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[Budget]:
        # Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Journal not found."
            )
            
        return await self.budget_repo.list_by_journal(journal_id)

    async def delete(
        self, budget_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        await self.get_or_404(budget_id, journal_id, owner_id)
        await self.budget_repo.delete(budget_id, journal_id)
        logger.info("Budget %s deleted", budget_id)