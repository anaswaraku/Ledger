# app/application/services/plot_service.py
import logging
from uuid import UUID

from fastapi import HTTPException

from app.application._utils import get_journal_or_404
from app.domain.models.account import AccountType
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository
from app.infrastructure.db.repositories.plot_repo import PlotRepository

logger = logging.getLogger(__name__)


class PlotService:
    def __init__(
        self,
        account_repo: AccountRepository,
        journal_repo: JournalRepository,
        plot_repo: PlotRepository,
        market_price_repo: MarketPriceRepository,
    ) -> None:
        self.account_repo = account_repo
        self.journal_repo = journal_repo
        self.plot_repo = plot_repo
        self.market_price_repo = market_price_repo

    async def get_names_by_type(
        self, owner_id: UUID, journal_id: UUID, account_type: AccountType
    ) -> list[str]:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        accounts = await self.plot_repo.get_by_journal_and_type(journal_id, account_type)
        return [acc.name for acc in accounts]

    async def get_account_entry(
        self, owner_id: UUID, journal_id: UUID, account_type: AccountType
    ) -> list[dict]:
        await get_journal_or_404(self.journal_repo, journal_id, owner_id)
        return await self.plot_repo.get_count(journal_id, account_type)

    async def get_market_price(self, skip: int = 0, limit: int = 500):
        return await self.market_price_repo.list_prices(skip=skip, limit=limit)