# tests/test_services/test_config.py
"""Tests that app settings load correctly from the .env file."""
from app.core.config import settings


def test_settings_load():
    """Settings object must be instantiated without error."""
    assert settings is not None


def test_app_name_is_set():
    assert isinstance(settings.APP_NAME, str)
    assert len(settings.APP_NAME) > 0


def test_postgres_settings_are_present():
    assert settings.POSTGRES_HOST
    assert settings.POSTGRES_PORT
    assert settings.POSTGRES_DB
    assert settings.POSTGRES_USER
    assert settings.POSTGRES_PASSWORD


def test_jwt_settings_are_present():
    assert settings.SECRET_KEY
    assert settings.ALGORITHM in ("HS256", "HS384", "HS512", "RS256")
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_secret_key_is_long_enough():
    """JWT secret should be at least 32 characters for security."""
    assert len(settings.SECRET_KEY) >= 32
