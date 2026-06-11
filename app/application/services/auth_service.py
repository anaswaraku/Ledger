# app/application/services/auth_service.py
import logging

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.domain.models.user import User
from app.infrastructure.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic for user authentication and registration."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, email: str, password: str) -> User:
        """
        Register a new user.

        Raises:
            HTTPException 400: If the email is already registered.
        """
        if await self.user_repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        password_hash = hash_password(password)
        user = await self.user_repo.create(email=email, password_hash=password_hash)
        logger.info("New user registered: %s", email)
        return user

    async def login(self, email: str, password: str) -> str:
        """
        Authenticate a user and return a signed JWT access token.

        Raises:
            HTTPException 401: If credentials are invalid.
        """
        user = await self.user_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            # Deliberately vague error to prevent user enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(subject=str(user.id))
        logger.info("User logged in: %s", email)
        return token
