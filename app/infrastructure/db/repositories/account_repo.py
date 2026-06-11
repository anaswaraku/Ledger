# app/infrastructure/db/repositories/account_repo.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account, AccountType


class AccountRepository:
    """Data-access layer for the Account entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_journal(self, journal_id: uuid.UUID) -> list[Account]:
        result = await self.db.execute(
            select(Account)
            .where(Account.journal_id == journal_id)
            .order_by(Account.name)
        )
        return list(result.scalars().all())

    async def get_by_name_and_journal(
        self, name: str, journal_id: uuid.UUID
    ) -> Account | None:
        result = await self.db.execute(
            select(Account).where(
                Account.name == name,
                Account.journal_id == journal_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        journal_id: uuid.UUID,
        name: str,
        account_type: AccountType,
    ) -> Account:
        account = Account(
            journal_id=journal_id,
            name=name,
            account_type=account_type,
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def search_by_name_prefix(
        self, journal_id: uuid.UUID, prefix: str, limit: int = 10
    ) -> list[Account]:
        """Used for auto-suggest in the UI (FR-2.5)."""
        result = await self.db.execute(
            select(Account)
            .where(
                Account.journal_id == journal_id,
                Account.name.ilike(f"{prefix}%"),
            )
            .order_by(Account.name)
            .limit(limit)
        )
        return list(result.scalars().all())
