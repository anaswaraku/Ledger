# app/dependencies.py
"""
Shared FastAPI dependencies.

All service factories live here so every router can use Depends() for DI,
enabling easy test overrides and a single source of truth for wiring.
"""
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.budget_repo import BudgetRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.market_price_repo import MarketPriceRepository
from app.infrastructure.db.repositories.plot_repo import PlotRepository
from app.infrastructure.db.repositories.report_repo import ReportRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository
from app.infrastructure.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

bearer = HTTPBearer(auto_error=True)


# ── Auth guard ────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT and return the authenticated User.

    Raises:
        HTTPException 401: Token is missing, expired, or invalid.
        HTTPException 401: User referenced in the token no longer exists.
    """
    token = credentials.credentials

    try:
        user_id_str = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid JWT received: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ── Service factories ─────────────────────────────────────────────────────────
# Each factory is a FastAPI dependency that wires repos → service in one place.

async def get_auth_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.auth_service import AuthService
    return AuthService(UserRepository(db))


async def get_journal_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.journal_service import JournalService
    return JournalService(JournalRepository(db))


async def get_account_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.account_service import AccountService
    return AccountService(
        account_repo=AccountRepository(db),
        journal_repo=JournalRepository(db),
        transaction_repo=TransactionRepository(db),
    )


async def get_transaction_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.transaction_service import TransactionService
    return TransactionService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
    )


async def get_report_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.report_service import ReportService
    return ReportService(
        report_repo=ReportRepository(db),
        journal_repo=JournalRepository(db),
        market_price_repo=MarketPriceRepository(db),
    )


async def get_file_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.file_service import FileService
    return FileService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
        budget_repo=BudgetRepository(db),
    )


async def get_currency_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.currency_service import CurrencyService
    return CurrencyService(MarketPriceRepository(db))


async def get_budget_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.budget_service import BudgetService
    return BudgetService(
        budget_repo=BudgetRepository(db),
        journal_repo=JournalRepository(db),
        market_price_repo=MarketPriceRepository(db),
    )


async def get_plot_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.plot_service import PlotService
    return PlotService(
        account_repo=AccountRepository(db),
        journal_repo=JournalRepository(db),
        plot_repo=PlotRepository(db),
        market_price_repo=MarketPriceRepository(db),
    )