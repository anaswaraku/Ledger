# tests/test_api/test_transactions.py
"""
Integration tests for /api/v1/transactions/* endpoints.

Flow:
  registered_user → auth_token → test_journal → test_accounts → transactions
"""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient


class TestCreateTransaction:
    async def test_create_balanced_transaction_returns_201(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "Grocery shopping",
                "payee": "SuperMart",
                "entries": [
                    {
                        "account_id": test_accounts["food_id"],
                        "amount": "50.00",
                        "currency": "USD",
                    },
                    {
                        "account_id": test_accounts["cash_id"],
                        "amount": "-50.00",
                        "currency": "USD",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "id" in data
        assert data["description"] == "Grocery shopping"
        assert data["payee"] == "SuperMart"
        assert len(data["entries"]) == 2

    async def test_create_three_way_split_returns_201(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        """One debit to cash, two credits split between expenses."""
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-16",
                "description": "Split purchase",
                "entries": [
                    {
                        "account_id": test_accounts["food_id"],
                        "amount": "60.00",
                    },
                    {
                        "account_id": test_accounts["food_id"],
                        "amount": "40.00",
                    },
                    {
                        "account_id": test_accounts["cash_id"],
                        "amount": "-100.00",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    async def test_create_imbalanced_transaction_returns_422(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "Bad transaction",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "50.00"},
                    {"account_id": test_accounts["cash_id"], "amount": "-40.00"},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_single_entry_returns_422(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "Only one entry",
                "entries": [
                    {"account_id": test_accounts["cash_id"], "amount": "50.00"}
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_zero_amount_entry_returns_422(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "Zero entry",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "0"},
                    {"account_id": test_accounts["cash_id"], "amount": "0"},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_unauthenticated_returns_403(
        self, async_client: AsyncClient, test_accounts: dict
    ):
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "No auth",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "50"},
                    {"account_id": test_accounts["cash_id"], "amount": "-50"},
                ],
            },
        )
        assert resp.status_code in (401, 403)

    async def test_create_wrong_journal_returns_404(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        """Referencing a journal that doesn't belong to the user should 404."""
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": str(uuid.uuid4()),  # random, non-existent
                "date": "2026-01-15",
                "description": "Wrong journal",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "50"},
                    {"account_id": test_accounts["cash_id"], "amount": "-50"},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestListTransactions:
    async def test_list_returns_empty_for_new_journal(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.get(
            "/api/v1/transactions/",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_returns_created_transaction(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        # Create one transaction
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-02-01",
                "description": "Rent",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "1000"},
                    {"account_id": test_accounts["cash_id"], "amount": "-1000"},
                ],
            },
            headers=auth_headers,
        )
        resp = await async_client.get(
            "/api/v1/transactions/",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["description"] == "Rent"

    async def test_list_unauthenticated_returns_403(
        self, async_client: AsyncClient, test_accounts: dict
    ):
        resp = await async_client.get(
            "/api/v1/transactions/",
            params={"journal_id": test_accounts["journal_id"]},
        )
        assert resp.status_code in (401, 403)


class TestGetTransaction:
    async def test_get_existing_transaction(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        create_resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-03-01",
                "description": "Coffee",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "5"},
                    {"account_id": test_accounts["cash_id"], "amount": "-5"},
                ],
            },
            headers=auth_headers,
        )
        txn_id = create_resp.json()["id"]

        resp = await async_client.get(
            f"/api/v1/transactions/{txn_id}",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == txn_id
        assert resp.json()["description"] == "Coffee"

    async def test_get_nonexistent_transaction_returns_404(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.get(
            f"/api/v1/transactions/{uuid.uuid4()}",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestDeleteTransaction:
    async def test_delete_transaction_returns_204(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        create_resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-04-01",
                "description": "To delete",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "25"},
                    {"account_id": test_accounts["cash_id"], "amount": "-25"},
                ],
            },
            headers=auth_headers,
        )
        txn_id = create_resp.json()["id"]

        delete_resp = await async_client.delete(
            f"/api/v1/transactions/{txn_id}",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

        # Verify it's gone
        get_resp = await async_client.get(
            f"/api/v1/transactions/{txn_id}",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert get_resp.status_code == 404
