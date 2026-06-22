# app/api/v1/routers/transactions.py
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionPatch,
)
from app.application.services.account_service import AccountService
from app.application.services.transaction_service import TransactionService
from app.dependencies import get_current_user, get_transaction_service
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/transactions",tags=["Transactions"])

@router.get(
    "/",
    response_model=list[TransactionResponse],
    summary="List transactions in a journal",
)
async def list_transactions(
    journal_id: UUID = Query(..., description="Journal to query"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    payee: str | None = Query(default=None),
    description: str | None = Query(default=None),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    return await service.list(  # type: ignore[return-value]
        owner_id=current_user.id,
        journal_id=journal_id,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        payee=payee,
        description=description,
    )


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new double-entry transaction",
)
async def create_transaction(
    data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    txn = await service.create(data=data, owner_id=current_user.id)
    return txn  # type: ignore[return-value]


@router.get(
    "/recent",
    response_model=list[TransactionResponse],
    summary="List recent transactions in a journal",
)
async def get_recent_transactions(
    journal_id: UUID = Query(...),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    return await service.get_recent_transactions(
        journal_id=journal_id,
        owner_id=current_user.id,
    )


@router.get(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction by ID",
)
async def get_transaction(
    txn_id: UUID,
    journal_id: UUID = Query(...),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await service.get_or_404(  # type: ignore[return-value]
        txn_id=txn_id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )


@router.put(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Update transaction metadata (date, description, payee, code)",
)
async def update_transaction(
    txn_id: UUID,
    journal_id: UUID = Query(...),
    data: TransactionUpdate = ...,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await service.update(  # type: ignore[return-value]
        txn_id=txn_id,
        journal_id=journal_id,
        owner_id=current_user.id,
        data=data,
    )


@router.patch(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Partially update an existing transaction (metadata and/or entries)",
)
async def patch_transaction(
    txn_id: UUID,
    journal_id: UUID = Query(...),
    data: TransactionPatch = ...,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await service.patch(  # type: ignore[return-value]
        txn_id=txn_id,
        journal_id=journal_id,
        owner_id=current_user.id,
        data=data,
    )



@router.delete(
    "/{txn_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction and all its entries",
)
async def delete_transaction(
    txn_id: UUID,
    journal_id: UUID = Query(...),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user),
) -> None:
    await service.delete(
        txn_id=txn_id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )

