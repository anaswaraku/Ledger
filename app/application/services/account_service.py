# app/application/services/account_service.py
import logging
import uuid

from fastapi import HTTPException, status

from app.domain.models.account import Account, AccountType
from app.domain.rules.account_validation import AccountValidationError, validate_account_name
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository

logger = logging.getLogger(__name__)


class AccountService:
    """Business logic for account management."""

    def __init__(
        self,
        account_repo: AccountRepository,
        journal_repo: JournalRepository,
    ) -> None:
        self.account_repo = account_repo
        self.journal_repo = journal_repo

    async def create(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        name: str,
        account_type: AccountType,
    ) -> Account:
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )

        # 2. Validate account name format
        try:
            normalised_name = validate_account_name(name)
        except AccountValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

        # 3. Check for duplicates within the journal
        existing = await self.account_repo.get_by_name_and_journal(
            normalised_name, journal_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account '{normalised_name}' already exists in this journal.",
            )

        account = await self.account_repo.create(
            journal_id=journal_id,
            name=normalised_name,
            account_type=account_type,
        )
        logger.info("Account '%s' created in journal %s", normalised_name, journal_id)
        return account

    async def list_for_journal(
        self, owner_id: uuid.UUID, journal_id: uuid.UUID
    ) -> list[Account]:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found.",
            )
        return await self.account_repo.get_by_journal(journal_id)

    async def search(
        self, owner_id: uuid.UUID, journal_id: uuid.UUID, prefix: str
    ) -> list[Account]:
        """Auto-suggest accounts matching a name prefix (FR-2.5)."""
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=404, detail="Journal not found.")
        return await self.account_repo.search_by_name_prefix(journal_id, prefix)
