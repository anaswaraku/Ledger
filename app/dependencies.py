# app/dependencies.py
"""
Shared FastAPI dependencies.

These are injected into route handlers via Depends().
"""
import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.application.services.transaction_service import TransactionService
from app.application.services.file_service import FileService
from app.application.services.plot_service import PlotService
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.plot_repo import PlotRepository
from app.infrastructure.db.repositories.budget_repo import BudgetRepository

logger = logging.getLogger(__name__)

bearer = HTTPBearer(auto_error=True)


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

async def get_transaction_service(db: AsyncSession = Depends(get_db)) -> TransactionService:
    return TransactionService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
    )

async def get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    return FileService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
        budget_repo=BudgetRepository(db),
    )

async def get_plot_service(db: AsyncSession = Depends(get_db))->PlotService:
    return PlotService(
        account_repo=AccountRepository(db),
        journal_repo=JournalRepository(db),
        plot_repo=PlotRepository(db)
    )