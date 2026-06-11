# tests/conftest.py
"""
Shared pytest fixtures for all test modules.

Database strategy:
- A fresh SQLite in-memory database is created per test function.
- Tables are created before the test and the engine is disposed after.
- This gives perfect isolation without the overhead of a running PostgreSQL.
- The `get_db` FastAPI dependency is overridden to use the test session.
"""
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models so Base.metadata knows about every table
from app.domain.models.base import Base
import app.domain.models  # noqa: F401


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields a fresh async SQLite session with all tables created."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an httpx AsyncClient wired to the FastAPI app,
    with get_db overridden to use the test SQLite session.
    """
    from app.main import app
    from app.infrastructure.db.database import get_db

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ── Convenience fixtures ──────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def registered_user(async_client: AsyncClient) -> dict:
    """Register a user and return the response payload plus the plain password."""
    email = f"user-{uuid.uuid4()}@example.com"
    password = "TestPassword123!"
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    data["_password"] = password  # stash for login fixture
    return data


@pytest_asyncio.fixture
async def auth_token(async_client: AsyncClient, registered_user: dict) -> str:
    """Return a valid JWT for the registered_user."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["_password"],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def test_journal(async_client: AsyncClient, auth_headers: dict) -> dict:
    """Create a journal and return its response payload."""
    resp = await async_client.post(
        "/api/v1/journals/",
        json={"name": "Test Journal", "description": "For testing"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest_asyncio.fixture
async def test_accounts(
    async_client: AsyncClient, auth_headers: dict, test_journal: dict
) -> dict:
    """Create a pair of accounts (assets:cash, expenses:food) and return their IDs."""
    journal_id = test_journal["id"]

    cash_resp = await async_client.post(
        "/api/v1/accounts/",
        json={
            "journal_id": journal_id,
            "name": "assets:cash",
            "account_type": "ASSET",
        },
        headers=auth_headers,
    )
    assert cash_resp.status_code == 201, cash_resp.text

    food_resp = await async_client.post(
        "/api/v1/accounts/",
        json={
            "journal_id": journal_id,
            "name": "expenses:food",
            "account_type": "EXPENSE",
        },
        headers=auth_headers,
    )
    assert food_resp.status_code == 201, food_resp.text

    return {
        "cash_id": cash_resp.json()["id"],
        "food_id": food_resp.json()["id"],
        "journal_id": journal_id,
    }
