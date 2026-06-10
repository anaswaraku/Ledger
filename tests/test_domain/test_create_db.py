import sys
import os
import asyncio

# Add project root to the Python path to allow absolute imports from `app`
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)  # noqa
sys.path.insert(0, project_root)

from app.infrastructure.db.database import Base, engine

# These imports are necessary for Base.metadata to discover the tables.
from app.domain.models.user import User
from app.domain.models.account import Account
from app.domain.models.market_price import MarketPrices
from app.domain.models.journal import Journal
from app.domain.models.transaction import Transaction, TransactionEntry


async def main():
    """Asynchronously creates all database tables."""
    try:
        print("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Failed to create tables: {e}")


if __name__ == "__main__":
    asyncio.run(main())
