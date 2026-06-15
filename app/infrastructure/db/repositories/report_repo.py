# app/infrastructure/db/repositories/report_repo.py
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, case,label
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account, AccountType
from app.domain.models.journal import Journal
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

    #why cash instead of account?
    async def get_cash_balance(self, journal_id:UUID, as_of:date)->Decimal:
        """Return the total balanace of all Cash or Bank accounts right before the given date"""
        query = (
            select(func.sum(TransactionEntry.amount).label("balance"))
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id==journal_id)
            .where(Transaction.date<as_of)
            .where(Account.account_type==AccountType.ASSET)
            .where(Account.name.ilike("%cash")|Account.name.ilike("%bank"))
        )
        result=await self.db.execute(query)
        row=result.scalar_one_or_none()
        return row or Decimal("0.0")
    
    async def get_cash_movements(
            self, journal_id:UUID,
            date_from: date,
            date_to: date,
    )->list[tuple[str, Decimal]]:
        """Returns the net movement for each account during the period"""
        query=(
            select(
                Account.name,
                func.sum(TransactionEntry.amount).label("movement")
            )
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id==journal_id)
            .where(Transaction.date>=date_from)
            .where(Transaction.date<=date_to)
            .where(Account.account_type==AccountType.ASSET)
            .where(Account.name.ilike("%cash")|Account.name.ilike("%bank"))
            .group_by(Account.id, Account.name)
        )
        result = await self.db.execute(query)
        return [(row.name, row.movement or Decimal("0.0")) for row in result.all()]

    async def get_investment_transactions_entries(
        self, journal_id: UUID, account_id: UUID | None = None, date_to: date | None = None
    ) -> list[dict]:
        """Fetch all entries of transactions that touch non-USD investment accounts."""
        stmt_txns = (
            select(Transaction.id)
            .join(TransactionEntry, Transaction.id == TransactionEntry.transaction_id)
            .join(Account, TransactionEntry.account_id == Account.id)
            .where(Account.journal_id == journal_id)
            .where(TransactionEntry.commodity != "USD")
        )
        if account_id:
            stmt_txns = stmt_txns.where(Account.id == account_id)
        if date_to:
            stmt_txns = stmt_txns.where(Transaction.date <= date_to)

        query = (
            select(
                Transaction.id.label("txn_id"),
                Transaction.date.label("txn_date"),
                TransactionEntry.account_id.label("account_id"),
                Account.name.label("account_name"),
                TransactionEntry.amount.label("amount"),
                TransactionEntry.commodity.label("commodity"),
            )
            .select_from(Transaction)
            .join(TransactionEntry, Transaction.id == TransactionEntry.transaction_id)
            .join(Account, TransactionEntry.account_id == Account.id)
            .where(Transaction.id.in_(stmt_txns))
            .order_by(Transaction.date.asc(), Transaction.created_at.asc())
        )
        res = await self.db.execute(query)
        return [dict(row._mapping) for row in res.all()]
    
    #net worth for dashboard
    async def get_net_worth(self,journal_id: UUID):
        """Return total networth for display"""
        query = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (Account.account_type==AccountType.ASSET,
                             TransactionEntry.amount),else_=0,
                        )
                    ),0,
                ).label("assets"),
                func.coalesce(
                    func.sum(
                        case(
                            (Account.account_type==AccountType.LIABILITY,
                             TransactionEntry.amount),
                             else_=0
                        )
                    ),0,
                ).label("liabilities")
            ).select_from(TransactionEntry)
            .join(Account, Account.id == TransactionEntry.account_id)
            .join(Journal, Journal.id ==Account.journal_id)
            .where(Journal.id==journal_id)
        )

        result = await self.db.execute(query)
        row = result.first()
        assets = row.assets if row else Decimal("0.0")
        liabilities = row.liabilities if row else Decimal("0.0")
        
        # In a ledger, liabilities are usually negative (credits). 
        # Net worth is Assets + Liabilities (e.g., 1000 + (-400) = 600)
        net_worth = assets + liabilities

        # Convert liabilities to positive for display
        return {
            "assets": assets,
            "liabilities": abs(liabilities),
            "net_worth": net_worth
        }