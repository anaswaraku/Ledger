# app/api/v1/routers/transactions.py
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.application.services.account_service import AccountService
from app.application.services.transaction_service import TransactionService
from app.application.use_cases.create_transaction import CreateTransactionUseCase
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


def _make_service(db: AsyncSession) -> TransactionService:
    return TransactionService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
    )


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    return await _make_service(db).list(  # type: ignore[return-value]
        owner_id=current_user.id,
        journal_id=journal_id,
        skip=skip,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
        payee=payee,
    )


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new double-entry transaction",
)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    service = _make_service(db)
    use_case = CreateTransactionUseCase(service)
    txn = await use_case.execute(data=data, owner_id=current_user.id)
    return txn  # type: ignore[return-value]


@router.get(
    "/{txn_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction by ID",
)
async def get_transaction(
    txn_id: UUID,
    journal_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await _make_service(db).get_or_404(  # type: ignore[return-value]
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await _make_service(db).update(  # type: ignore[return-value]
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _make_service(db).delete(
        txn_id=txn_id,
        journal_id=journal_id,
        owner_id=current_user.id,
    )
