# app/infrastructure/db/repositories/budget_repo.py
import uuid
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.budget import Budget


class BudgetRepository:
    """Data-access layer for the Budget entity."""
 
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, budget_id: uuid.UUID, journal_id: uuid.UUID) -> Budget | None:
        stmt = (
            select(Budget)
            .where(Budget.id == budget_id, Budget.journal_id == journal_id)
            .options(selectinload(Budget.account))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create(
        self,
        journal_id: uuid.UUID,
        account_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        period: str,
        start_date: date_type,
        end_date: date_type ,
    ) -> Budget:
        budget = Budget(
            journal_id=journal_id,
            account_id=account_id,
            amount=amount,
            currency=currency,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(budget)
        await self.db.commit()
        await self.db.refresh(budget)
        # Fetch again with relationship
        return await self.get_by_id(budget.id, journal_id)  # type: ignore[return-value]

    async def list_by_journal(self, journal_id: uuid.UUID) -> list[Budget]:
        stmt = (
            select(Budget)
            .where(Budget.journal_id == journal_id)
            .options(selectinload(Budget.account))
            .order_by(Budget.start_date.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update(
        self,
        budget_id: uuid.UUID,
        journal_id: uuid.UUID,
        **kwargs,
    ) -> Budget | None:
        budget = await self.get_by_id(budget_id, journal_id)
        if not budget:
            return None
        for field, value in kwargs.items():
            if value is not None:
                setattr(budget, field, value)
        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    async def delete(self, budget_id: uuid.UUID, journal_id: uuid.UUID) -> bool:
        stmt = delete(Budget).where(Budget.id == budget_id, Budget.journal_id == journal_id)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return (res.rowcount or 0) > 0

    async def get_spending_entries(
        self, account_id: uuid.UUID, start_date: date_type, end_date: date_type
    ) -> list[tuple[Decimal, str, date_type]]:
        """Fetch all individual transaction entries for the budget's currency calculations."""
        from app.domain.models.transaction import Transaction
        from app.domain.models.transaction_entry import TransactionEntry

        stmt = (
            select(TransactionEntry.amount, TransactionEntry.commodity, Transaction.date)
            .join(Transaction, TransactionEntry.transaction_id == Transaction.id)
            .where(
                TransactionEntry.account_id == account_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
            )
        )
        res = await self.db.execute(stmt)
        return list(res.all())
