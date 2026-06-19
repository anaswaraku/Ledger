import pytest
from httpx import AsyncClient


class TestReportsAPI:
    @pytest.fixture(autouse=True)
    async def setup_transactions(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        """Pre-populate a transaction so reports have some data."""
        resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-05-01",
                "description": "Salary",
                "entries": [
                    {"account_id": test_accounts["cash_id"], "amount": "5000", "currency": "USD"},
                    {"account_id": test_accounts["food_id"], "amount": "-5000", "currency": "USD"},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    async def test_get_balance_sheet(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/balance-sheet",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "net" in data

    async def test_get_income_statement(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/income-statement",
            params={
                "journal_id": test_accounts["journal_id"],
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "income" in data
        assert "expenses" in data
        assert "net_income" in data

    async def test_get_cash_flow(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/cash-flow",
            params={
                "journal_id": test_accounts["journal_id"],
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "beginning_balance" in data
        assert "inflows" in data
        assert "outflows" in data
        assert "net_cash_flow" in data
        assert "ending_balance" in data

    @pytest.mark.skip(reason="Requires PostgreSQL for date_trunc function")
    async def test_get_net_worth(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/net-worth",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_assets" in data
        assert "total_liabilities" in data
        assert "net_worth" in data

    @pytest.mark.skip(reason="Requires PostgreSQL for date_trunc function")
    async def test_get_monthly_income(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/monthly-income",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "months" in data

    async def test_get_roi_report(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/roi",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "assets" in data

    @pytest.mark.skip(reason="Requires PostgreSQL for date_trunc function")
    async def test_get_roi_timeline(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/roi-timeline",
            params={
                "journal_id": test_accounts["journal_id"],
                "commodity": "USD",
                "cost_commodity": "USD",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "timeline" in data

    @pytest.mark.skip(reason="Requires PostgreSQL for date_trunc function")
    async def test_get_htmx_roi_chart(self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict):
        resp = await async_client.get(
            "/api/v1/reports/htmx/roi-chart",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "No historical data available yet." in resp.text or "plotly" in resp.text.lower()
