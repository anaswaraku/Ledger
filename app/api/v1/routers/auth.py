# app/api/v1/routers/auth.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.application.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.user_repo import UserRepository

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _make_auth_service(db: AsyncSession) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> User:
    return await _make_auth_service(db).register(
        email=data.email, password=data.password
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive a JWT access token",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token = await _make_auth_service(db).login(
        email=data.email, password=data.password
    )
    return TokenResponse(access_token=token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (client should discard the token)",
)
async def logout(
    _current_user: User = Depends(get_current_user),
) -> None:
    """
    JWT is stateless. The client must discard the token.
    A server-side token blacklist (Redis) will be added in Phase 2.
    """
    return None
