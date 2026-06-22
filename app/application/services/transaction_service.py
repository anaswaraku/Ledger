# app/application/services/transaction_service.py
from __future__ import annotations

import logging
import uuid
from datetime import date as date_type

from fastapi import HTTPException, status

from app.api.v1.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionPatch
from app.application._utils import get_journal_or_404
from app.domain.models.transaction import Transaction
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository

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

    async def create(self, data: TransactionCreate, owner_id: uuid.UUID) -> Transaction:
        await get_journal_or_404(self.journal_repo, data.journal_id, owner_id)

        # Verify all account IDs belong to this journal
        for entry in data.entries:
            account = await self.account_repo.get_by_id(entry.account_id)
            if not account or account.journal_id != data.journal_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Account {entry.account_id} does not exist in the specified journal.",
                )

        # Check for duplicate transaction
        new_entries = [
            {
                "account_id": e.account_id,
                "amount": e.amount,
                "currency": e.currency,
            }
            for e in data.entries
        ]
        await self._check_duplicate(data.journal_id, data.date, data.payee, new_entries)

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
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        return await self.txn_repo.list_by_journal(
            journal_id,
            skip=skip,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
            payee=payee,
            description=description,
        )

    async def get_or_404(
        self, txn_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Transaction:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
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
        txn = await self.get_or_404(txn_id, journal_id, owner_id)
        update_data = data.model_dump(exclude_none=True)

        final_date = update_data.get("date", txn.date)
        final_payee = update_data.get("payee", txn.payee) if "payee" in update_data else txn.payee
        final_entries = [
            {
                "account_id": e.account_id,
                "amount": e.amount,
                "currency": e.commodity,
            }
            for e in txn.entries
        ]

        await self._check_duplicate(journal_id, final_date, final_payee, final_entries, exclude_txn_id=txn_id)

        updated = await self.txn_repo.update(
            txn_id, journal_id, **update_data
        )
        return updated  # type: ignore[return-value]

    async def patch(
        self,
        txn_id: uuid.UUID,
        journal_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: TransactionPatch,
    ) -> Transaction:
        txn = await self.get_or_404(txn_id, journal_id, owner_id)
        
        update_data = data.model_dump(exclude_unset=True)

        if "entries" in update_data:
            entries = update_data["entries"]
            if entries is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Transaction entries cannot be null.",
                )
            
            # Verify all account IDs belong to this journal
            for entry in entries:
                account = await self.account_repo.get_by_id(entry["account_id"])
                if not account or account.journal_id != journal_id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Account {entry['account_id']} does not exist in the specified journal.",
                    )

            update_data["entries_data"] = [
                {
                    "account_id": e["account_id"],
                    "amount": e["amount"],
                    "currency": e.get("currency", "USD"),
                    "cost_amount": e.get("cost_amount"),
                    "cost_currency": e.get("cost_currency"),
                }
                for e in entries
            ]
            del update_data["entries"]

        # Check for duplicates using final merged state
        final_date = update_data.get("date", txn.date)
        final_payee = update_data.get("payee", txn.payee) if "payee" in update_data else txn.payee
        if "entries_data" in update_data:
            final_entries = [
                {
                    "account_id": e["account_id"],
                    "amount": e["amount"],
                    "currency": e.get("currency", "USD"),
                }
                for e in update_data["entries_data"]
            ]
        else:
            final_entries = [
                {
                    "account_id": e.account_id,
                    "amount": e.amount,
                    "currency": e.commodity,
                }
                for e in txn.entries
            ]

        await self._check_duplicate(journal_id, final_date, final_payee, final_entries, exclude_txn_id=txn_id)

        updated = await self.txn_repo.patch(
            txn_id, journal_id, **update_data
        )
        return updated  # type: ignore[return-value]


    async def delete(
        self, txn_id: uuid.UUID, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        await self.get_or_404(txn_id, journal_id, owner_id)
        await self.txn_repo.delete(txn_id, journal_id)
        logger.info("Transaction %s deleted from journal %s", txn_id, journal_id)

    async def get_recent_transactions(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[Transaction]:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        return await self.txn_repo.get_recent_transactions(journal_id)

    async def _check_duplicate(
        self,
        journal_id: uuid.UUID,
        txn_date: date_type,
        payee: str | None,
        entries: list[dict],
        exclude_txn_id: uuid.UUID | None = None,
    ) -> None:
        existing_txns = await self.txn_repo.list_by_journal(
            journal_id=journal_id,
            date_from=txn_date,
            date_to=txn_date,
            limit=100
        )
        from app.application._utils import check_duplicate_transaction
        if check_duplicate_transaction(txn_date, payee, entries, existing_txns, exclude_txn_id=exclude_txn_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transaction Already Exists!",
            )

