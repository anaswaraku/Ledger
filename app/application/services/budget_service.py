import logging
from fastapi import HTTPException,status
from datetime import date
from uuid import UUID
from decimal import Decimal


from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.domain.models.budget import Budget

logger = logging.getLogger(__name__)

class BudgetService:
    def __init__(self,
                 budget_repo: BudgetRepository,
                 journal_repo: JournalRepository)->None:
        self.budget_repo=budget_repo
        self.journal_repo = journal_repo

    async def create(self,
            owner_id:UUID,
            journal_id:UUID,
            account_id:UUID,
            amount:Decimal,
            period:str,
            start_date:date,
            end_date:date
    )->Budget:
        journal_id= await self.journal_repo.get_by_id_and_owner(journal_id,owner_id)
        if not journal_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="journal not found"
            )
        if start_date>end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start date must be before end date"
            )
        budget = await self.budget_repo.create(
            journal_id=journal_id,
            account_id=owner_id,
            amount=amount,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        logger.info("Budget %s created for Journal %s", budget.id, journal_id)
        return budget
    
    async def get_or_404(
            self, budget_id:UUID,
            journal_id:UUID,
            owner_id:UUID,
                )->Budget:
        journal=await self.journal_repo.get_by_id_and_owner(journal,owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found"
            )
        #fetch budget
        budget = await self.budget_repo.get_by_id(budget_id,journal_id)
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget Not found"
            )
        return Budget
    
    async def get_budget_with_spend(
            self,
            budget_id:UUID,
            journal_id:UUID,
            owner_id:UUID,
                )->dict:
        budget=await self.get_or_404(budget_id,journal_id,owner_id)
        #calculation
        spend_amount = await self.budget_repo.get_actual_amount(
            account_id=budget.account_id,
            start_date=budget.start_date,
            end_date=budget.end_date
        )
        #expense - absolute value will be used (because of negative sign while transaction)
        actual_spend=abs(spend_amount)
        difference= budget.amount-actual_spend

        return{
            "id":budget_id,
            "budget_amount":budget.amount,
            "spend_amount":actual_spend,
            "difference":difference,
            "start_date":budget.start_date,
            "end_date":budget.end_date
        }
    
    async def list_budget_for_journal(
            self,
            budget_id:UUID,
            journal_id:UUID,
            owner_id:UUID,
                )->list[Budget]:
        journal=await self.journal_repo.get_by_id_and_owner(journal,owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found"
            )
        return await self.budget_repo.list_by_journal(journal_id)
    async def delete(
             self,
            budget_id:UUID,
            journal_id:UUID,
            owner_id:UUID,
    )->None:
        await self.get_or_404(
            budget_id,
            journal_id,
            owner_id
        )
        await self.budget_repo.delete(
            budget_id,
            journal_id
        )
        logger.info(
            "Budget %s is deleted",
            budget_id
        )