# app/infrastructure/db/repositories/chart_repo.py
import uuid
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_entry import TransactionEntry


class ChartRepository:
    """Data-access layer for charting aggregations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_postings_for_charts(
        self, journal_id: uuid.UUID, date_from: date_type | None = None, date_to: date_type | None = None
    ) -> list[dict]:
        """
        Fetch all entries in USD with transaction dates for the specified journal.
        Returns a list of dicts: {"date": date, "account_type": AccountType, "account_name": str, "amount": Decimal}.
        """
        query = (
            select(
                Transaction.date.label("date"),
                Account.account_type.label("account_type"),
                Account.name.label("account_name"),
                TransactionEntry.amount.label("amount"),
            )
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id == journal_id)
            .where(TransactionEntry.commodity == "USD")
        )
        if date_from:
            query = query.where(Transaction.date >= date_from)
        if date_to:
            query = query.where(Transaction.date <= date_to)

        query = query.order_by(Transaction.date.asc(), Transaction.created_at.asc())
        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result.all()]
