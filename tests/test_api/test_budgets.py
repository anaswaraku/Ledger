# tests/test_api/test_budgets.py
import pytest
from decimal import Decimal
from httpx import AsyncClient


class TestBudgetsApi:
    async def test_budget_lifecycle_and_variance(
        self, async_client: AsyncClient, auth_headers: dict, test_journal: dict
    ):
        journal_id = test_journal["id"]

        # 1. Create accounts: assets:checking, expenses:food
        checking_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "assets:checking",
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        assert checking_resp.status_code == 201
        checking_id = checking_resp.json()["id"]

        food_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "expenses:food",
                "account_type": "EXPENSE",
            },
            headers=auth_headers,
        )
        assert food_resp.status_code == 201
        food_id = food_resp.json()["id"]

        # 2. Create budget
        budget_resp = await async_client.post(
            "/api/v1/budgets/",
            json={
                "journal_id": journal_id,
                "account_id": food_id,
                "amount": "500.00",
                "period": "monthly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-30",
            },
            headers=auth_headers,
        )
        assert budget_resp.status_code == 201, budget_resp.text
        budget_data = budget_resp.json()
        assert budget_data["account_name"] == "expenses:food"
        assert Decimal(budget_data["amount"]) == Decimal("500.00")
        assert budget_data["period"] == "monthly"
        assert budget_data["start_date"] == "2026-06-01"
        assert budget_data["end_date"] == "2026-06-30"
        
        budget_id = budget_data["id"]

        # 3. List budgets
        list_resp = await async_client.get(
            "/api/v1/budgets/",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        budgets = list_resp.json()
        assert len(budgets) == 1
        assert budgets[0]["id"] == budget_id

        # 4. Update budget to 600.00
        update_resp = await async_client.put(
            f"/api/v1/budgets/{budget_id}",
            params={"journal_id": journal_id},
            json={"amount": "600.00"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert Decimal(update_resp.json()["amount"]) == Decimal("600.00")

        # 5. Get variance (actual should be 0, so favorable variance = 600)
        var_resp1 = await async_client.get(
            f"/api/v1/budgets/{budget_id}/variance",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert var_resp1.status_code == 200, var_resp1.text
        var_data1 = var_resp1.json()
        assert Decimal(var_data1["budgeted_amount"]) == Decimal("600.00")
        assert Decimal(var_data1["actual_amount"]) == Decimal("0.00")
        assert Decimal(var_data1["variance"]) == Decimal("600.00")
        assert var_data1["is_favorable"] is True

        # 6. Post an expense transaction of 200.00 USD on 2026-06-15
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-15",
                "description": "Weekly grocery buy",
                "entries": [
                    {"account_id": food_id, "amount": "200.00"},
                    {"account_id": checking_id, "amount": "-200.00"},
                ],
            },
            headers=auth_headers,
        )

        # 7. Get variance (actual should be 200, variance = 400, favorable = True)
        var_resp2 = await async_client.get(
            f"/api/v1/budgets/{budget_id}/variance",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert var_resp2.status_code == 200
        var_data2 = var_resp2.json()
        assert Decimal(var_data2["actual_amount"]) == Decimal("200.00")
        assert Decimal(var_data2["variance"]) == Decimal("400.00")
        assert var_data2["is_favorable"] is True

        # 8. Post another expense transaction of 500.00 USD on 2026-06-20 (total actual = 700)
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-20",
                "description": "Fancy dinner",
                "entries": [
                    {"account_id": food_id, "amount": "500.00"},
                    {"account_id": checking_id, "amount": "-500.00"},
                ],
            },
            headers=auth_headers,
        )

        # 9. Get variance (actual should be 700, variance = -100, favorable = False)
        var_resp3 = await async_client.get(
            f"/api/v1/budgets/{budget_id}/variance",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert var_resp3.status_code == 200
        var_data3 = var_resp3.json()
        assert Decimal(var_data3["actual_amount"]) == Decimal("700.00")
        assert Decimal(var_data3["variance"]) == Decimal("-100.00")
        assert var_data3["is_favorable"] is False

        # 10. Delete budget
        del_resp = await async_client.delete(
            f"/api/v1/budgets/{budget_id}",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert del_resp.status_code == 204

        # Verify list is empty
        list_resp2 = await async_client.get(
            "/api/v1/budgets/",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        assert list_resp2.status_code == 200
        assert len(list_resp2.json()) == 0
