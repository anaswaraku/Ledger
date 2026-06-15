# tests/test_api/test_roi.py
import pytest
from decimal import Decimal
from httpx import AsyncClient


class TestRoiApi:
    async def test_roi_calculation(
        self, async_client: AsyncClient, auth_headers: dict, test_journal: dict
    ):
        journal_id = test_journal["id"]

        # 1. Create accounts: assets:investments:btc, assets:bank:checking
        checking_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "assets:bank:checking",
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        assert checking_resp.status_code == 201
        checking_id = checking_resp.json()["id"]

        btc_resp = await async_client.post(
            "/api/v1/accounts/",
            json={
                "journal_id": journal_id,
                "name": "assets:investments:btc",
                "account_type": "ASSET",
            },
            headers=auth_headers,
        )
        assert btc_resp.status_code == 201
        btc_id = btc_resp.json()["id"]

        # 2. Buy 2 BTC for 1000 USD (post transaction)
        buy_resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-01",
                "description": "Buy Bitcoin",
                "entries": [
                    {
                        "account_id": btc_id,
                        "amount": "2.00",
                        "currency": "BTC",
                    },
                    {
                        "account_id": checking_id,
                        "amount": "-1000.00",
                        "currency": "USD",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert buy_resp.status_code == 201, buy_resp.text

        # 3. Add historical price for BTC on 2026-06-14 (600 USD)
        price_resp = await async_client.post(
            "/api/v1/currencies/prices",
            json={
                "currency_from": "BTC",
                "currency_to": "USD",
                "price": "600.00",
                "date": "2026-06-14",
            },
            headers=auth_headers,
        )
        assert price_resp.status_code == 201

        # 4. Generate ROI report as of 2026-06-14
        roi_resp = await async_client.get(
            "/api/v1/reports/roi",
            params={"journal_id": journal_id, "date": "2026-06-14"},
            headers=auth_headers,
        )
        assert roi_resp.status_code == 200, roi_resp.text
        reports = roi_resp.json()
        assert len(reports) == 1
        
        btc_report = reports[0]
        assert btc_report["account_name"] == "assets:investments:btc"
        assert btc_report["commodity"] == "BTC"
        assert Decimal(btc_report["units"]) == Decimal("2.00")
        assert Decimal(btc_report["cost_basis"]) == Decimal("1000.00")
        assert Decimal(btc_report["average_cost_basis"]) == Decimal("500.00")
        assert Decimal(btc_report["current_price"]) == Decimal("600.00")
        assert Decimal(btc_report["current_value"]) == Decimal("1200.00")
        assert Decimal(btc_report["net_gain"]) == Decimal("200.00")
        assert Decimal(btc_report["roi"]) == Decimal("0.20")  # 20% ROI

        # 5. Sell 1 BTC for 700 USD (post transaction)
        sell_resp = await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": journal_id,
                "date": "2026-06-10",
                "description": "Sell BTC",
                "entries": [
                    {
                        "account_id": btc_id,
                        "amount": "-1.00",
                        "currency": "BTC",
                    },
                    {
                        "account_id": checking_id,
                        "amount": "700.00",
                        "currency": "USD",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert sell_resp.status_code == 201, sell_resp.text

        # 6. Generate ROI report again as of 2026-06-14
        # Remaining: 1 BTC.
        # Average purchase price was 500 USD, so remaining cost basis = 500 USD.
        # Current Price = 600 USD. Current Value = 600 USD.
        # Net gain = 100 USD. ROI = 100 / 500 = 20%.
        roi_resp2 = await async_client.get(
            "/api/v1/reports/roi",
            params={"journal_id": journal_id, "date": "2026-06-14"},
            headers=auth_headers,
        )
        assert roi_resp2.status_code == 200, roi_resp2.text
        reports2 = roi_resp2.json()
        assert len(reports2) == 1
        
        btc_report2 = reports2[0]
        assert Decimal(btc_report2["units"]) == Decimal("1.00")
        assert Decimal(btc_report2["cost_basis"]) == Decimal("500.00")
        assert Decimal(btc_report2["average_cost_basis"]) == Decimal("500.00")
        assert Decimal(btc_report2["current_value"]) == Decimal("600.00")
        assert Decimal(btc_report2["net_gain"]) == Decimal("100.00")
        assert Decimal(btc_report2["roi"]) == Decimal("0.20")
