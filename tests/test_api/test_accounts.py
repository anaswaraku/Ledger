import uuid
from httpx import AsyncClient


class TestCreateAccount:
    async def test_create_account_success(
        self, async_client: AsyncClient, auth_headers: dict, test_journal: dict
    ):
        resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": test_journal["id"],
                "name": "assets:checking",
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "assets:checking"
        assert data["account_type"] == "ASSET"
        assert data["journal_id"] == test_journal["id"]
        assert "id" in data

    async def test_create_account_unauthenticated(
        self, async_client: AsyncClient, test_journal: dict
    ):
        resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": test_journal["id"],
                "name": "assets:checking",
                "account_type": "ASSET",
            },
        )
        assert resp.status_code in (401, 403)

    async def test_create_account_invalid_name(
        self, async_client: AsyncClient, auth_headers: dict, test_journal: dict
    ):
        resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": test_journal["id"],
                "name": "",  # Empty name
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestListAccounts:
    async def test_list_accounts_returns_created_accounts(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.get(
            "/api/v1/accounts/",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [acc["name"] for acc in data]
        assert "assets:cash" in names
        assert "expenses:food" in names

    async def test_list_accounts_wrong_journal(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/accounts/",
            params={"journal_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        # Assuming the service returns an empty list or 404 for unknown journals.
        # Typically it returns empty list if journal not found or belongs to someone else.
        assert resp.status_code in (200, 404)


class TestSearchAccounts:
    async def test_search_accounts_by_prefix(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.get(
            "/api/v1/accounts/search",
            params={"journal_id": test_accounts["journal_id"], "q": "assets"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "assets:cash"

    async def test_search_accounts_no_match(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        resp = await async_client.get(
            "/api/v1/accounts/search",
            params={"journal_id": test_accounts["journal_id"], "q": "liabilities"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestGetAccountRegister:
    async def test_get_account_register_returns_history(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        # Create a transaction affecting cash and food
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-05-01",
                "description": "Lunch",
                "entries": [
                    {"account_id": test_accounts["food_id"], "amount": "15", "currency": "USD"},
                    {"account_id": test_accounts["cash_id"], "amount": "-15", "currency": "USD"},
                ],
            },
            headers=auth_headers,
        )

        resp = await async_client.get(
            f"/api/v1/accounts/{test_accounts['cash_id']}/register",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have the register entry
        assert len(data) == 1
        assert data[0]["description"] == "Lunch"
        assert float(data[0]["amount"]) == -15.0
        assert float(data[0]["running_balance"]) == -15.0
