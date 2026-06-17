# app/api/v1/routers/budgets.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.budget import BudgetCreate, BudgetResponse
from app.application.services.budget_service import BudgetService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

router = APIRouter(prefix="/api/v1/budgets", tags=["Budgets"])

def _make_budget_service(db: AsyncSession) -> BudgetService:
    return BudgetService(
        budget_repo=BudgetRepository(db),
        journal_repo=JournalRepository(db)
    )

@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget target",
)
async def create_budget(
    data: BudgetCreate,
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    service = _make_budget_service(db)
    
    # Create the budget
    budget = await service.create(
        owner_id=current_user.id,
        journal_id=journal_id,
        account_id=data.account_id,
        amount=data.amount,
        period=data.period,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    
    # Return formatted response
    return await service.get_budget_with_spending(
        budget_id=budget.id, 
        journal_id=journal_id, 
        owner_id=current_user.id
    )  # type: ignore[return-value]

@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get a specific budget and its spending status"
)
async def get_budget(
    budget_id: UUID,
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    service = _make_budget_service(db)
    return await service.get_budget_with_spending(
        budget_id=budget_id, 
        journal_id=journal_id, 
        owner_id=current_user.id
    )  # type: ignore[return-value]

@router.get(
    "/",
    response_model=List[BudgetResponse],
    summary="List all budgets in a journal",
)
async def list_budgets(
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BudgetResponse]:
    service = _make_budget_service(db)
    budgets = await service.list_for_journal(journal_id, current_user.id)
    
    # Calculate spending for every budget
    results = []
    for budget in budgets:
        b_dict = await service.get_budget_with_spending(
            budget_id=budget.id, 
            journal_id=journal_id, 
            owner_id=current_user.id
        )
        results.append(b_dict)
        
    return results  # type: ignore[return-value]

@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget target"
)
async def delete_budget(
    budget_id: UUID,
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = _make_budget_service(db)
    await service.delete(
        budget_id=budget_id, 
        journal_id=journal_id, 
        owner_id=current_user.id
    )
