import asyncio
import uuid
from decimal import Decimal
from app.application.services.plot_service import PlotService
from app.domain.models.account import AccountType

class MockJournalRepo:
    async def get_by_id_and_owner(self, journal_id, owner_id):
        return True

class MockPlotRepo:
    async def get_count(self, journal_id, account_type):
        return [
            {"name": "Cash", "count": 10, "amount": Decimal("100.50")}
        ]

async def test():
    service = PlotService(account_repo=None, journal_repo=MockJournalRepo(), plot_repo=MockPlotRepo())
    try:
        res = await service.get_account_entry(
            uuid.uuid4(),
            uuid.uuid4(),
            AccountType.ASSET
        )
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
