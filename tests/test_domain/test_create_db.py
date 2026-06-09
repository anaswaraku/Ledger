import sys
import os

# Add project root to the Python path to allow absolute imports from `app`
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from app.infrastructure.db.database import Base, engine
from app.domain.models.account import User, Accounts, MarketPrices
from app.domain.models.journal import Journal
from app.domain.models.transaction import Transaction, TransactionEntries

try:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
except Exception as e:
    print(f"Failed to create tables: {e}")
