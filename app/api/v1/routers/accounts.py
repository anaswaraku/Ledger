# app/api/v1/routers/accounts.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.schemas.account import AccountCreate, AccountResponse, RegisterEntryResponse
from app.application.services.account_service import AccountService
from app.dependencies import get_account_service, get_current_user
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account in a journal",
)
async def create_account(
    data: AccountCreate,
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> AccountResponse:
    account = await service.create(
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
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    return await service.list_for_journal(  # type: ignore[return-value]
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
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> list[AccountResponse]:
    return await service.search(  # type: ignore[return-value]
        owner_id=current_user.id,
        journal_id=journal_id,
        prefix=q,
    )


@router.get(
    "/{account_id}/register",
    response_model=list[RegisterEntryResponse],
    summary="Account register — transaction history with running balance (FR-4.4)",
)
async def get_account_register(
    account_id: UUID,
    journal_id: UUID = Query(...),
    service: AccountService = Depends(get_account_service),
    current_user: User = Depends(get_current_user),
) -> list[RegisterEntryResponse]:
    """Returns transaction history for an account with running balance."""
    return await service.get_account_register(
        owner_id=current_user.id,
        journal_id=journal_id,
        account_id=account_id,
    )
