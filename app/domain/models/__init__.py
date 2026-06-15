# app/domain/models/__init__.py
"""
Import all ORM models here so that:
1. SQLAlchemy Base.metadata discovers every table for Alembic autogenerate.
2. Relationship back-references resolve without circular import errors.
"""
from app.domain.models.user import User
from app.domain.models.journal import Journal
from app.domain.models.account import Account
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_entry import TransactionEntry
from app.domain.models.market_price import MarketPrice
from app.domain.models.budget import Budget

__all__ = [
    "User",
    "Journal",
    "Account",
    "Transaction",
    "TransactionEntry",
    "MarketPrice",
    "Budget",
]
