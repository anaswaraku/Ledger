from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.db.database import Base, engine
from app.domain.models.account import User, Accounts, MarketPrices
from app.domain.models.journal import Journal
from app.domain.models.transaction import Transaction, TransactionEntries

try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
except:
    print("Failed")
