# app/api/v1/routers/accounts.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.account import AccountCreate, AccountResponse
from app.application.services.account_service import AccountService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


def _make_service(db: AsyncSession) -> AccountService:
    return AccountService(
        account_repo=AccountRepository(db),
        journal_repo=JournalRepository(db),
    )


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account in a journal",
)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    account = await _make_service(db).create(
        owner_id=current_user.id,
        journal_id=data.journal_id,
        name=data.name,
        account_type=data.account_type,
    )
    return account  # type: ignore[return-value]


@router.get(
    "/",
    response_model=list[AccountResponse],
    summary="List all accounts in a journal",
)
async def list_accounts(
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    return await _make_service(db).list_for_journal(  # type: ignore[return-value]
        owner_id=current_user.id,
        journal_id=journal_id,
    )


@router.get(
    "/search",
    response_model=list[AccountResponse],
    summary="Auto-suggest accounts matching a name prefix (FR-2.5)",
)
async def search_accounts(
    journal_id: UUID = Query(...),
    q: str = Query(..., min_length=1, description="Account name prefix"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    return await _make_service(db).search(  # type: ignore[return-value]
        owner_id=current_user.id,
        journal_id=journal_id,
        prefix=q,
    )


@router.get(
    "/{account_name}/register",
    response_model=list[dict],
    summary="Account register — transaction history with running balance (FR-4.4)",
)
async def get_account_register(
    account_name: str,
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Phase 2: Returns transaction history for an account with running balance."""
    return []
