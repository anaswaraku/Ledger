# tests/test_api/test_charts.py
import pytest
from decimal import Decimal
from httpx import AsyncClient


class TestChartsApi:
    async def test_charts_data(
        self, async_client: AsyncClient, auth_headers: dict, test_journal: dict
    ):
        journal_id = test_journal["id"]

        # 1. Create accounts: assets:checking, income:salary, expenses:rent
        checking_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "assets:checking",
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        checking_id = checking_resp.json()["id"]

        salary_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "income:salary",
                "account_type": "INCOME",
            },
            headers=auth_headers,
        )
        salary_id = salary_resp.json()["id"]

        rent_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "expenses:rent",
                "account_type": "EXPENSE",
            },
            headers=auth_headers,
        )
        rent_id = rent_resp.json()["id"]

        # 2. Add Salary income (debit checking 1500, credit salary -1500) on 2026-06-01
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-01",
                "description": "Salary",
                "entries": [
                    {"account_id": checking_id, "amount": "1500.00"},
                    {"account_id": salary_id, "amount": "-1500.00"},
                ],
            },
            headers=auth_headers,
        )

        # 3. Add Rent expense (debit rent 800, credit checking -800) on 2026-06-05
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-05",
                "description": "Rent",
                "entries": [
                    {"account_id": rent_id, "amount": "800.00"},
                    {"account_id": checking_id, "amount": "-800.00"},
                ],
            },
            headers=auth_headers,
        )

        # 4. Monthly overview check
        mo_resp = await async_client.get(
            "/api/v1/charts/monthly-overview",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert mo_resp.status_code == 200, mo_resp.text
        mo_data = mo_resp.json()
        assert "2026-06" in mo_data["labels"]
        idx = mo_data["labels"].index("2026-06")
        assert Decimal(mo_data["income"][idx]) == Decimal("1500.00")
        assert Decimal(mo_data["expenses"][idx]) == Decimal("800.00")

        # 5. Balance trend check
        bt_resp = await async_client.get(
            "/api/v1/charts/balance-trend",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert bt_resp.status_code == 200
        bt_data = bt_resp.json()
        assert "2026-06-01" in bt_data["labels"]
        assert "2026-06-05" in bt_data["labels"]
        
        idx1 = bt_data["labels"].index("2026-06-01")
        assert Decimal(bt_data["assets"][idx1]) == Decimal("1500.00")
        assert Decimal(bt_data["net_worth"][idx1]) == Decimal("1500.00")

        idx2 = bt_data["labels"].index("2026-06-05")
        # assets = 1500 - 800 = 700
        assert Decimal(bt_data["assets"][idx2]) == Decimal("700.00")
        assert Decimal(bt_data["net_worth"][idx2]) == Decimal("700.00")

        # 6. Expense breakdown check
        eb_resp = await async_client.get(
            "/api/v1/charts/expense-breakdown",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert eb_resp.status_code == 200
        eb_data = eb_resp.json()
        assert "expenses:rent" in eb_data["labels"]
        idx3 = eb_data["labels"].index("expenses:rent")
        assert Decimal(eb_data["values"][idx3]) == Decimal("800.00")
