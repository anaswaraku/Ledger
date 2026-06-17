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

logger = logging.getLogger(__name__)

class BudgetService:
    """Business logic for managing budgets."""

    def __init__(
        self, 
        budget_repo: BudgetRepository, 
        journal_repo: JournalRepository,
        account_repo: AccountRepository = None
    ) -> None:
        self.budget_repo = budget_repo
        self.journal_repo = journal_repo
        self.account_repo = account_repo

    async def create(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        account_id: uuid.UUID,
        amount: Decimal,
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
        Fetches a budget and calculates exactly how much has been spent.
        """
        # 1. Get the budget (automatically handles 404s and permissions)
        budget = await self.get_or_404(budget_id, journal_id, owner_id)

        # 2. Calculate the math by asking the repository for actual spending
        spend_amount = await self.budget_repo.get_actual_amount(
            account_id=budget.account_id,
            start_date=budget.start_date,
            end_date=budget.end_date
        )

        # Expense might be positive or negative. Use abs() for the progress bar.
        actual_spend = abs(spend_amount)
        difference = budget.amount - actual_spend

        return {
            "id": budget.id,
            "budget_amount": budget.amount,
            "spend_amount": actual_spend,
            "difference": difference,
            "start_date": budget.start_date,
            "end_date": budget.end_date
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