# app/api/v1/routers/auth.py
from fastapi import APIRouter, Depends, status

from app.api.v1.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.application.services.auth_service import AuthService
from app.dependencies import get_auth_service, get_current_user
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> User:
    return await service.register(email=data.email, password=data.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive a JWT access token",
)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token = await service.login(email=data.email, password=data.password)
    return TokenResponse(access_token=token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (client should discard the token)",
)
async def logout(_current_user: User = Depends(get_current_user)) -> None:
    """
    JWT is stateless — the client must discard the token.
    A server-side token blacklist (Redis) can be added as a future enhancement.
    """
    return None
