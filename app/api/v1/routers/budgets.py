# app/api/v1/routers/budgets.py
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.budget import BudgetCreate, BudgetResponse # BudgetUpdate, BudgetVarianceResponse
from app.application.services.budget_service import BudgetService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

router = APIRouter(prefix="/api/v1/budgets", tags=["Budgets"])


def _make_budget_service(db: AsyncSession) -> BudgetService:
    return BudgetService(
        budget_repo=BudgetRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
    )


@router.post(
    "/",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget target",
)
async def create_budget(
    data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BudgetResponse:
    return await _make_budget_service(db).create_budget(
        owner_id=current_user.id, data=data
    )  # type: ignore[return-value]


@router.get(
    "/",
    response_model=list[BudgetResponse],
    summary="List all budgets in a journal",
)
async def list_budgets(
    journal_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BudgetResponse]:
    return await _make_budget_service(db).list_budgets(
        owner_id=current_user.id, journal_id=journal_id
    )  # type: ignore[return-value]


# @router.put(
#     "/{budget_id}",
#     response_model=BudgetResponse,
#     summary="Update a budget target",
# )
# async def update_budget(
#     budget_id: uuid.UUID,
#     journal_id: uuid.UUID = Query(...),
#     data: BudgetUpdate = ...,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ) -> BudgetResponse:
#     return await _make_budget_service(db).update_budget(
#         owner_id=current_user.id,
#         journal_id=journal_id,
#         budget_id=budget_id,
#         data=data,
#     )  # type: ignore[return-value]


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT, 
    summary="Delete a budget target",
)
async def delete_budget(
    budget_id: uuid.UUID,
    journal_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _make_budget_service(db).delete_budget(
        owner_id=current_user.id,
        journal_id=journal_id,
        budget_id=budget_id,
    )


# @router.get(
#     "/{budget_id}/variance",
#     response_model=BudgetVarianceResponse,
#     summary="Get variance analysis report for a budget",
# )
# async def get_budget_variance(
#     budget_id: uuid.UUID,
#     journal_id: uuid.UUID = Query(...),
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ) -> BudgetVarianceResponse:
#     return await _make_budget_service(db).get_budget_variance(
#         owner_id=current_user.id,
#         journal_id=journal_id,
#         budget_id=budget_id,
#     )
