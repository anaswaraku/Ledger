# app/application/services/journal_service.py
import logging
import uuid

from fastapi import HTTPException, status

from app.domain.models.journal import Journal
from app.infrastructure.db.repositories.journal_repo import JournalRepository

logger = logging.getLogger(__name__)


class JournalService:
    """Logic for journal (accounting book) management."""

    def __init__(self, journal_repo: JournalRepository) -> None:
        self.journal_repo = journal_repo

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        description: str | None = None,
        base_currency: str = "USD",
    ) -> Journal:
        journal = await self.journal_repo.create(
            owner_id=owner_id,
            name=name,
            description=description,
            base_currency=base_currency,
        )
        logger.info("Journal '%s' created for user %s", name, owner_id)
        return journal

    async def list_for_user(self, owner_id: uuid.UUID) -> list[Journal]:
        return await self.journal_repo.list_by_owner(owner_id)

    async def get_or_404(
        self, journal_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Journal:
        """
        Return the journal if it belongs to the owner.

        Raises:
            HTTPException 404: If not found or not owned by the user.
        """
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )
        return journal

    async def delete(self, journal_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        journal = await self.get_or_404(journal_id, owner_id)
        await self.journal_repo.delete(journal)
        logger.info("Journal '%s' deleted by user %s", journal.name, owner_id)

    async def update(
        self,
        journal_id: uuid.UUID,
        owner_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        base_currency: str | None = None,
    ) -> Journal:
        journal = await self.get_or_404(journal_id, owner_id)
        if name is not None:
            journal.name = name
        if description is not None:
            journal.description = description
        if base_currency is not None:
            journal.base_currency = base_currency
        await self.journal_repo.db.commit()
        await self.journal_repo.db.refresh(journal)
        logger.info("Journal %s updated by user %s", journal_id, owner_id)
        return journal
