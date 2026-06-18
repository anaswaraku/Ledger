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
             from sqlalchemy import func
             accounts = await self.get_by_journal_and_type(journal_id,account_type)
             if not accounts:
                  return {}
             account_ids = [acc.id for acc in accounts]
             result = await self.db.execute(
                  select(TransactionEntry.account_id, func.count(TransactionEntry.id),
                         func.sum(TransactionEntry.amount))
                  .where(TransactionEntry.account_id.in_(account_ids))
                  .group_by(TransactionEntry.account_id)
             )

             counts_dict = {row[0]:{"count":row[1],"amount":row[2] or 0} for row in result.all()}
             return [{"name":acc.name,
                     "count":counts_dict[acc.id]["count"],
                      "amount":counts_dict[acc.id]["amount"]} for acc in accounts if counts_dict.get(acc.id,{}.get("count",0)>0)]