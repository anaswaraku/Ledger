# tests/test_api/test_currencies.py
import pytest
from decimal import Decimal
from httpx import AsyncClient


class TestCurrenciesApi:
    async def test_crud_market_prices(self, async_client: AsyncClient, auth_headers: dict):
        # 1. Add a price
        resp = await async_client.post(
            "/api/v1/currencies/prices",
            json={
                "currency_from": "USD",
                "currency_to": "EUR",
                "price": "0.92",
                "date": "2026-06-14",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        price_data = resp.json()
        assert price_data["currency_from"] == "USD"
        assert price_data["currency_to"] == "EUR"
        assert Decimal(price_data["price"]) == Decimal("0.92")
        assert price_data["date"] == "2026-06-14"
        
        price_id = price_data["id"]

        # 2. List prices
        list_resp = await async_client.get(
            "/api/v1/currencies/prices",
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        prices = list_resp.json()
        assert len(prices) >= 1
        assert any(p["id"] == price_id for p in prices)

        # 3. Convert currencies
        # Direct conversion
        conv_resp = await async_client.get(
            "/api/v1/currencies/convert",
            params={
                "amount": "100.00",
                "currency_from": "USD",
                "currency_to": "EUR",
                "date": "2026-06-14",
            },
            headers=auth_headers,
        )
        assert conv_resp.status_code == 200, conv_resp.text
        conv_data = conv_resp.json()
        assert Decimal(conv_data["amount"]) == Decimal("100.00")
        assert Decimal(conv_data["rate"]) == Decimal("0.92")
        assert Decimal(conv_data["converted_amount"]) == Decimal("92.00")

        # Reciprocal conversion
        conv_rev_resp = await async_client.get(
            "/api/v1/currencies/convert",
            params={
                "amount": "92.00",
                "currency_from": "EUR",
                "currency_to": "USD",
                "date": "2026-06-14",
            },
            headers=auth_headers,
        )
        assert conv_rev_resp.status_code == 200, conv_rev_resp.text
        conv_rev_data = conv_rev_resp.json()
        # rate should be 1 / 0.92 = 1.0869565217
        assert Decimal(conv_rev_data["rate"]).quantize(Decimal("0.0001")) == Decimal("1.0870")
        assert Decimal(conv_rev_data["converted_amount"]).quantize(Decimal("0.01")) == Decimal("100.00")

        # 4. Delete price
        del_resp = await async_client.delete(
            f"/api/v1/currencies/prices/{price_id}",
            headers=auth_headers,
        )
        assert del_resp.status_code == 204

        # Verify list no longer has it
        list_resp2 = await async_client.get(
            "/api/v1/currencies/prices",
            headers=auth_headers,
        )
        assert not any(p["id"] == price_id for p in list_resp2.json())
