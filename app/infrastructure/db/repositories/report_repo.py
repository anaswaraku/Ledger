# app/infrastructure/db/repositories/report_repo.py
from datetime import date
from decimal import Decimal
from typing import NamedTuple
from uuid import UUID
import calendar
import datetime

from sqlalchemy import func, select, case,label
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account, AccountType
from app.domain.models.journal import Journal
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_entry import TransactionEntry


class AccountBalance(NamedTuple):
    name: str
    account_type: AccountType
    commodity: str
    balance: Decimal


class CashBalance(NamedTuple):
    commodity: str
    balance: Decimal


class CashMovement(NamedTuple):
    name: str
    commodity: str
    movement: Decimal


class NetWorthBalance(NamedTuple):
    account_type: AccountType
    commodity: str
    balance: Decimal


class MonthlyIncomeBalance(NamedTuple):
    commodity: str
    balance: Decimal


class ReportRepository:
    """Data-access layer for financial reporting aggregations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_account_balances(
        self, journal_id: UUID, date_to: date | None = None, date_from: date | None = None
    ) -> list[AccountBalance]:
        """
        Calculates the sum of all transaction entries for each account in a journal.
        Returns a list of AccountBalance named tuples.
        """
        query = (
            select(
                Account.name,
                Account.account_type,
                TransactionEntry.commodity,
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

        query = query.group_by(Account.id, Account.name, Account.account_type, TransactionEntry.commodity)

        result = await self.db.execute(query)
        return [AccountBalance(row.name, row.account_type, row.commodity, row.balance or Decimal("0.0")) for row in result.all()]

    async def get_cash_balances(self, journal_id: UUID, as_of: date) -> list[CashBalance]:
        """Return the cash balances grouped by commodity right before the given date."""
        query = (
            select(
                TransactionEntry.commodity,
                func.sum(TransactionEntry.amount).label("balance")
            )
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id == journal_id)
            .where(Transaction.date < as_of)
            .where(Account.account_type == AccountType.ASSET)
            .where(Account.name.ilike("%cash") | Account.name.ilike("%bank"))
            .group_by(TransactionEntry.commodity)
        )
        result = await self.db.execute(query)
        return [CashBalance(row.commodity, row.balance or Decimal("0.0")) for row in result.all()]
    
    async def get_cash_movements(
            self, journal_id: UUID,
            date_from: date,
            date_to: date,
    ) -> list[CashMovement]:
        """Returns the net movement for each account and commodity during the period."""
        query = (
            select(
                Account.name,
                TransactionEntry.commodity,
                func.sum(TransactionEntry.amount).label("movement")
            )
            .select_from(Account)
            .join(TransactionEntry, Account.id == TransactionEntry.account_id)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(Account.journal_id == journal_id)
            .where(Transaction.date >= date_from)
            .where(Transaction.date <= date_to)
            .where(Account.account_type == AccountType.ASSET)
            .where(Account.name.ilike("%cash") | Account.name.ilike("%bank"))
            .group_by(Account.id, Account.name, TransactionEntry.commodity)
        )
        result = await self.db.execute(query)
        return [CashMovement(row.name, row.commodity, row.movement or Decimal("0.0")) for row in result.all()]

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
    
    async def get_net_worth_balances(self, journal_id: UUID) -> list[NetWorthBalance]:
        """Return balances of Asset and Liability accounts, grouped by account_type and commodity."""
        query = (
            select(
                Account.account_type,
                TransactionEntry.commodity,
                func.sum(TransactionEntry.amount).label("balance")
            )
            .select_from(TransactionEntry)
            .join(Account, Account.id == TransactionEntry.account_id)
            .where(Account.journal_id == journal_id)
            .where(Account.account_type.in_([AccountType.ASSET, AccountType.LIABILITY]))
            .group_by(Account.account_type, TransactionEntry.commodity)
        )
        result = await self.db.execute(query)
        return [NetWorthBalance(row.account_type, row.commodity, row.balance or Decimal("0.0")) for row in result.all()]

    async def get_monthly_income_balances(self, journal_id: UUID) -> list[MonthlyIncomeBalance]:
        """Return balances of Income accounts for the current month, grouped by commodity."""
        query = (
            select(
                TransactionEntry.commodity,
                func.sum(TransactionEntry.amount).label("balance")
            )
            .select_from(TransactionEntry)
            .join(Account, Account.id == TransactionEntry.account_id)
            .join(Transaction, Transaction.id == TransactionEntry.transaction_id)
            .where(
                Account.account_type == AccountType.INCOME,
                Account.journal_id == journal_id,
                func.date_trunc("month", Transaction.date) == func.date_trunc("month", func.current_date())
            )
            .group_by(TransactionEntry.commodity)
        )
        result = await self.db.execute(query)
        return [MonthlyIncomeBalance(row.commodity, row.balance or Decimal("0.0")) for row in result.all()]