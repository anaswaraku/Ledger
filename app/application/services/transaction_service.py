# app/application/services/transaction_service.py
import logging
import uuid
from datetime import date as date_type

from fastapi import HTTPException, status

from app.api.v1.schemas.transaction import TransactionCreate, TransactionUpdate
from app.domain.models.transaction import Transaction
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository

from app.domain.models.transaction import Transaction as DomainTransaction
from app.domain.models.transaction_entry import TransactionEntry as DomainTransactionEntry
from app.domain.money import UnbalancedTransactionError

logger = logging.getLogger(__name__)


class TransactionService:
    """Logic for double-entry transaction management."""

    def __init__(
        self,
        txn_repo: TransactionRepository,
        journal_repo: JournalRepository,
        account_repo: AccountRepository,
    ) -> None:
        self.txn_repo = txn_repo
        self.journal_repo = journal_repo
        self.account_repo = account_repo

    async def create(
        self, data: TransactionCreate, owner_id: uuid.UUID
    ) -> Transaction:
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(
            data.journal_id, owner_id
        )
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )



        # 3. Verify all account IDs belong to this journal
        for entry in data.entries:
            account = await self.account_repo.get_by_id(entry.account_id)
            if not account or account.journal_id != data.journal_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Account {entry.account_id} does not exist "
                        "in the specified journal."
                    ),
                )

        txn = await self.txn_repo.create(
            journal_id=data.journal_id,
            date=data.date,
            description=data.description or "",
            payee=data.payee,
            code=data.code,
            entries_data=[
                {
                    "account_id": e.account_id,
                    "amount": e.amount,
                    "currency": e.currency,
                    "cost_amount": e.cost_amount,
                    "cost_currency": e.cost_currency,
                }
                for e in data.entries
            ],
        )
        logger.info(
            "Transaction %s created in journal %s (%.2f)",
            txn.id,
            data.journal_id,
            float(data.entries[0].amount),
        )
        return txn

    async def list(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        payee: str | None = None,
        description: str | None = None,
    ) -> list[Transaction]:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")
        return await self.txn_repo.list_by_journal(
            journal_id, skip=skip, limit=limit,
            date_from=date_from, date_to=date_to, payee=payee,
            description=description,
        )

    async def get_or_404(
        self, txn_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Transaction:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")
        txn = await self.txn_repo.get_by_id(txn_id, journal_id)
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found.")
        return txn

    async def update(
        self,
        txn_id: uuid.UUID,
        journal_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: TransactionUpdate,
    ) -> Transaction:
        await self.get_or_404(txn_id, journal_id, owner_id)
        updated = await self.txn_repo.update(
            txn_id,
            journal_id,
            **data.model_dump(exclude_none=True),
        )
        return updated  # type: ignore[return-value]

    async def delete(
        self,
        txn_id: uuid.UUID,
        journal_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        await self.get_or_404(txn_id, journal_id, owner_id)
        await self.txn_repo.delete(txn_id, journal_id)
        logger.info("Transaction %s deleted from journal %s", txn_id, journal_id)
    async def get_recent_transactions(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> "list[Transaction]":
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")
        return await self.txn_repo.get_recent_transactions(journal_id)
