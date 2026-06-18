# app/application/services/plot_service.py
#permission to read the jorunal and executing database
import logging
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.models.account import Account, AccountType
from app.domain.rules.account_validation import AccountValidationError, validate_account_name
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository
from app.infrastructure.db.repositories.plot_repo import PlotRepository
from app.api.v1.schemas.account import RegisterEntryResponse
from decimal import Decimal

class PlotService:
    def __init__(self,
                 account_repo:AccountRepository,
                 journal_repo: JournalRepository,
                 plot_repo: PlotRepository):
        self.account_repo = account_repo
        self.journal_repo = journal_repo
        self.plot_repo = plot_repo

    async def get_names_by_type(
            self,owner_id:UUID,
            journal_id:UUID,
            account_type:AccountType)->list[str]:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id=journal_id,owner_id=owner_id)
        if not journal:
            raise HTTPException(
                status_code=404,
                detail="Journal Not found"
            )
        accounts = await self.plot_repo.get_by_journal_and_type(journal_id,account_type)

        return [acc.name for acc in accounts]
    
    async def get_account_entry(
            self,
            owner_id:UUID,
            journal_id:UUID,
            account_type:AccountType,
            )->list[str]:
        journal = await self.journal_repo.get_by_id_and_owner(journal_id=journal_id,owner_id=owner_id)
        if not journal:
            raise HTTPException(
                status_code=404,
                detail="Journal Not found"
            )
        counts=await self.plot_repo.get_count(
            journal_id,
            account_type
        )
        return [count.account for count in counts]
    