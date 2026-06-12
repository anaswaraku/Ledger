# app/infrastructure/db/repositories/report_repo.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account, AccountType
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_entry import TransactionEntry


class ReportRepository:
    """Data-access layer for financial reporting aggregations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_account_balances(
        self, journal_id: UUID, date_to: date | None = None, date_from: date | None = None
    ) -> list[tuple[str, AccountType, Decimal]]:
        """
        Calculates the sum of all transaction entries for each account in a journal.
        Returns a list of tuples: (account_name, account_type, balance).
        """
        query = (
            select(
                Account.name,
                Account.account_type,
                func.sum(TransactionEntry.amount).label("balance"),
            )
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id == journal_id)
        )

        if date_to:
            query = query.where(Transaction.date <= date_to)
        if date_from:
            query = query.where(Transaction.date >= date_from)

        query = query.group_by(Account.id, Account.name, Account.account_type)

        result = await self.db.execute(query)
        # SQLAlchemy rows act like tuples, but we return explicit typing
        return [(row.name, row.account_type, row.balance or Decimal("0.0")) for row in result.all()]
