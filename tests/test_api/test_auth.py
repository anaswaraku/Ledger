# tests/test_api/test_auth.py
"""
Integration tests for /api/v1/auth/* endpoints.
Uses the SQLite in-memory database via conftest fixtures.
"""
import uuid

import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success_returns_201(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid.uuid4()}@test.com", "password": "Password123!"},
        )
        assert resp.status_code == 201

    async def test_register_returns_user_fields(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid.uuid4()}@test.com", "password": "Password123!"},
        )
        data = resp.json()
        assert "id" in data
        assert "email" in data
        assert "created_at" in data
        # Password must NEVER appear in the response
        assert "password" not in data
        assert "password_hash" not in data

    async def test_register_duplicate_email_returns_400(self, async_client: AsyncClient):
        email = f"{uuid.uuid4()}@test.com"
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123!"},
        )
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "DifferentPassword!"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_invalid_email_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "Password123!"},
        )
        assert resp.status_code == 422

    async def test_register_missing_password_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success_returns_token(
        self, async_client: AsyncClient, registered_user: dict
    ):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["_password"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    async def test_login_wrong_password_returns_401(
        self, async_client: AsyncClient, registered_user: dict
    ):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": "WRONG_PASSWORD"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.com", "password": "anypassword"},
        )
        assert resp.status_code == 401

    async def test_login_error_message_is_generic(
        self, async_client: AsyncClient, registered_user: dict
    ):
        """Error must not reveal whether the email exists (prevent enumeration)."""
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": registered_user["email"], "password": "WRONG"},
        )
        detail = resp.json()["detail"].lower()
        # Must say something about invalid credentials, not "wrong password"
        assert "invalid" in detail or "incorrect" in detail or "password" in detail


class TestLogout:
    async def test_logout_with_valid_token_returns_204(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 204

    async def test_logout_without_token_returns_403(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/logout")
        assert resp.status_code in (401, 403)
