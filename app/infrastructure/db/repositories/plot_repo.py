# app/infrastructure/db/repositories/plot_repo.py
#add queries to execute
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.account import Account, AccountType
from app.domain.models.transaction_entry import TransactionEntry

class PlotRepository:
        def __init__(self, db: AsyncSession) -> None:
            self.db = db
        
        async def get_by_journal_and_type(
            self,journal_id:uuid.UUID,
            account_type: AccountType
    )->list[Account]:
            result = await self.db.execute(
                select(
                    Account
                ).where (Account.journal_id==journal_id)
                .where(Account.account_type==account_type)
                .order_by(Account.name)
            )
            return list(result.scalars().all())
        
        async def get_count( self,journal_id:uuid.UUID,
            account_type: AccountType):
             accounts = await self.get_by_journal_and_type(journal_id,account_type)
             account_ids = [acc.id for acc in accounts]
             result = await self.db.execute(
                  select(TransactionEntry)
                  .where(TransactionEntry.account_id.in_(account_ids))
                  .order_by(TransactionEntry.transaction_id)
             )
             return list(result.scalars().all())