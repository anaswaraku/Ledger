# app/api/v1/routers/budgets.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.budget import BudgetCreate, BudgetResponse
from app.application.services.budget_service import BudgetService
from app.dependencies import get_budget_service, get_current_user
from app.domain.models.user import User
from app.domain.money import MissingExchangeRatesCollectedError

router = APIRouter(prefix="/api/v1/budgets", tags=["Budgets"])


@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget target",
)
async def create_budget(
    data: BudgetCreate,
    journal_id: UUID = Query(...),
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    budget = await service.create(
        owner_id=current_user.id,
        journal_id=journal_id,
        account_id=data.account_id,
        amount=data.amount,
        currency=data.currency,
        period=data.period,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    return await service.get_budget_with_spending(
        budget_id=budget.id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )  # type: ignore[return-value]


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get a specific budget and its spending status",
)
async def get_budget(
    budget_id: UUID,
    journal_id: UUID = Query(...),
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    return await service.get_budget_with_spending(
        budget_id=budget_id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )  # type: ignore[return-value]


@router.get(
    "/",
    response_model=List[BudgetResponse],
    summary="List all budgets in a journal",
)
async def list_budgets(
    journal_id: UUID = Query(...),
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> List[BudgetResponse]:
    # list_for_journal verifies ownership once then computes spending for all
    # budgets — no N+1 ownership re-checks.
    return await service.list_for_journal(journal_id, current_user.id)  # type: ignore[return-value]


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget target",
)
async def delete_budget(
    budget_id: UUID,
    journal_id: UUID = Query(...),
    service: BudgetService = Depends(get_budget_service),
    current_user: User = Depends(get_current_user),
) -> None:
    await service.delete(
        budget_id=budget_id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )
