# app/application/services/budget_service.py
import logging
import uuid
from decimal import Decimal

from fastapi import HTTPException, status

from app.api.v1.schemas.budget import BudgetCreate, BudgetUpdate, BudgetVarianceResponse
from app.domain.models.account import AccountType
from app.domain.models.budget import Budget
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

logger = logging.getLogger(__name__)


class BudgetService:
    """Business logic for budget tracking and variance analysis."""

    def __init__(
        self,
        budget_repo: BudgetRepository,
        journal_repo: JournalRepository,
        account_repo: AccountRepository,
    ) -> None:
        self.budget_repo = budget_repo
        self.journal_repo = journal_repo
        self.account_repo = account_repo

    async def _verify_journal_owner(self, journal_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )

    async def create_budget(self, owner_id: uuid.UUID, data: BudgetCreate) -> Budget:
        await self._verify_journal_owner(data.journal_id, owner_id)

        # Verify account belongs to the same journal
        account = await self.account_repo.get_by_id(data.account_id)
        if not account or account.journal_id != data.journal_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The specified account does not exist in the journal.",
            )

        budget = await self.budget_repo.create(
            journal_id=data.journal_id,
            account_id=data.account_id,
            amount=data.amount,
            period=data.period.lower(),
            start_date=data.start_date,
            end_date=data.end_date,
        )
        logger.info(
            "Budget created for account %s: %s within %s -> %s",
            data.account_id,
            data.amount,
            data.start_date,
            data.end_date,
        )
        return budget

    async def list_budgets(self, owner_id: uuid.UUID, journal_id: uuid.UUID) -> list[Budget]:
        await self._verify_journal_owner(journal_id, owner_id)
        return await self.budget_repo.list_by_journal(journal_id)

    async def update_budget(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        budget_id: uuid.UUID,
        data: BudgetUpdate,
    ) -> Budget:
        await self._verify_journal_owner(journal_id, owner_id)
        budget = await self.budget_repo.get_by_id(budget_id, journal_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )

        updated = await self.budget_repo.update(
            budget_id=budget_id,
            journal_id=journal_id,
            **data.model_dump(exclude_none=True),
        )
        return updated  # type: ignore[return-value]

    async def delete_budget(
        self, owner_id: uuid.UUID, journal_id: uuid.UUID, budget_id: uuid.UUID
    ) -> None:
        await self._verify_journal_owner(journal_id, owner_id)
        deleted = await self.budget_repo.delete(budget_id, journal_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found.",
            )
        logger.info("Budget %s deleted", budget_id)

    async def get_budget_variance(
        self, owner_id: uuid.UUID, journal_id: uuid.UUID, budget_id: uuid.UUID
    ) -> BudgetVarianceResponse:
        await self._verify_journal_owner(journal_id, owner_id)
        budget = await self.budget_repo.get_by_id(budget_id, journal_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found or does not belong to the journal.",
            )

        actual_raw = await self.budget_repo.get_actual_amount(
            budget.account_id, budget.start_date, budget.end_date
        )

        account = budget.account
        # Handle sign conversion based on account type
        if account.account_type in (AccountType.INCOME, AccountType.LIABILITY, AccountType.EQUITY):
            # Credit-normal accounts: actual values are negative in DB, flip to positive
            actual_amount = -actual_raw
            # Favorable for income/equity/liability is earning/increasing more than budgeted
            variance = actual_amount - budget.amount
            is_favorable = variance >= 0
        else:
            # Debit-normal accounts (ASSET, EXPENSE): actual values are positive in DB
            actual_amount = actual_raw
            # Favorable for expense is spending less than budgeted
            variance = budget.amount - actual_amount
            is_favorable = variance >= 0

        return BudgetVarianceResponse(
            budget_id=budget.id,
            account_id=budget.account_id,
            account_name=account.name,
            period=budget.period,
            start_date=budget.start_date,
            end_date=budget.end_date,
            budgeted_amount=budget.amount,
            actual_amount=actual_amount,
            variance=variance,
            is_favorable=is_favorable,
        )
