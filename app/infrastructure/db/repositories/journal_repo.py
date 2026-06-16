# app/infrastructure/db/repositories/journal_repo.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.journal import Journal


class JournalRepository:
    """Data-access layer for the Journal entity."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, journal_id: uuid.UUID) -> Journal | None:
        result = await self.db.execute(
            select(Journal).where(Journal.id == journal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_owner(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Journal | None:
        result = await self.db.execute(
            select(Journal).where(
                Journal.id == journal_id,
                Journal.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Journal]:
        result = await self.db.execute(
            select(Journal)
            .where(Journal.owner_id == owner_id)
            .order_by(Journal.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        description: str | None = None,
        base_currency: str = "USD",
    ) -> Journal:
        journal = Journal(
            owner_id=owner_id,
            name=name,
            description=description,
            base_currency=base_currency,
        )
        self.db.add(journal)
        await self.db.commit()
        await self.db.refresh(journal)
        return journal

    async def delete(self, journal: Journal) -> None:
        await self.db.delete(journal)
        await self.db.commit()
