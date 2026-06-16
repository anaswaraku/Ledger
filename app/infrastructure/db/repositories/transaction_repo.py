# app/infrastructure/db/repositories/transaction_repo.py
import uuid
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.transaction import Transaction
from app.domain.models.transaction_entry import TransactionEntry


class TransactionRepository:
    """Data-access layer for the Transaction entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(
        self, txn_id: uuid.UUID, journal_id: uuid.UUID
    ) -> Transaction | None:
        result = await self.db.execute(
            select(Transaction)
            .where(
                Transaction.id == txn_id,
                Transaction.journal_id == journal_id,
            )
            .options(selectinload(Transaction.entries))
        )
        return result.scalar_one_or_none()

    async def list_by_journal(
        self,
        journal_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        date_from: date_type | None = None,
        date_to: date_type | None = None,
        payee: str | None = None,
        description: str | None = None,
    ) -> list[Transaction]:
        query = (
            select(Transaction)
            .where(Transaction.journal_id == journal_id)
            .options(selectinload(Transaction.entries))
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if date_from:
            query = query.where(Transaction.date >= date_from)
        if date_to:
            query = query.where(Transaction.date <= date_to)
        if payee:
            query = query.where(Transaction.payee.ilike(f"%{payee}%"))
        if description:
            query = query.where(Transaction.description.ilike(f"%{description}%"))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        journal_id: uuid.UUID,
        date: date_type,
        description: str,
        payee: str | None,
        code: str | None,
        entries_data: list[dict],
    ) -> Transaction:
        txn = Transaction(
            journal_id=journal_id,
            date=date,
            description=description,
            payee=payee,
            code=code,
        )
        self.db.add(txn)
        await self.db.flush()  # populate txn.id before creating entries

        for entry in entries_data:
            self.db.add(
                TransactionEntry(
                    transaction_id=txn.id,
                    account_id=entry["account_id"],
                    amount=entry["amount"],
                    commodity=entry.get("currency", "USD"),
                )
            )

        await self.db.commit()
        await self.db.refresh(txn)
        return txn

    async def update(
        self,
        txn_id: uuid.UUID,
        journal_id: uuid.UUID,
        **kwargs,
    ) -> Transaction | None:
        txn = await self.get_by_id(txn_id, journal_id)
        if not txn:
            return None
        for field, value in kwargs.items():
            if value is not None:
                setattr(txn, field, value)
        await self.db.commit()
        await self.db.refresh(txn)
        return txn

    async def delete(
        self, txn_id: uuid.UUID, journal_id: uuid.UUID
    ) -> bool:
        txn = await self.get_by_id(txn_id, journal_id)
        if not txn:
            return False
        await self.db.delete(txn)
        await self.db.commit()
        return True

    async def get_account_entries(
        self, account_id: uuid.UUID
    ) -> list[tuple[Transaction, TransactionEntry]]:
        query = (
            select(Transaction, TransactionEntry)
            .join(TransactionEntry, Transaction.id == TransactionEntry.transaction_id)
            .where(TransactionEntry.account_id == account_id)
            .order_by(Transaction.date.asc(), Transaction.created_at.asc())
        )
        result = await self.db.execute(query)
        # result.all() returns a list of Row objects containing (Transaction, TransactionEntry)
        return list(result.all())

    async def recent_transactions(
        self,journal_id:uuid.UUID
    ):
    query=(
        select(Transaction)
        .where (Transaction.journal_id ==journal_id )
        .order_by(
            Transaction.date.desc(),
            Transaction.created_at.desc()
        )
        .limit(10)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

    
