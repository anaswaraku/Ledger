# tests/test_api/test_files.py
import json
import uuid
import pytest
from httpx import AsyncClient


class TestFilesApi:
    async def test_export_import_csv(
        self, async_client: AsyncClient, auth_headers: dict, test_accounts: dict
    ):
        # 1. Create a transaction
        await async_client.post(
            "/api/v1/transactions/",
            json={
                "journal_id": test_accounts["journal_id"],
                "date": "2026-01-15",
                "description": "Grocery shopping",
                "entries": [
                    {
                        "account_id": test_accounts["food_id"],
                        "amount": "50.00",
                    },
                    {
                        "account_id": test_accounts["cash_id"],
                        "amount": "-50.00",
                    },
                ],
            },
            headers=auth_headers,
        )

        # 2. Export journal as CSV
        export_resp = await async_client.get(
            "/api/v1/files/export",
            params={"journal_id": test_accounts["journal_id"], "format": "csv"},
            headers=auth_headers,
        )
        assert export_resp.status_code == 200
        csv_content = export_resp.text
        assert "Grocery shopping" in csv_content
        assert "50.00" in csv_content

        # 3. Export journal as JSON
        export_json_resp = await async_client.get(
            "/api/v1/files/export",
            params={"journal_id": test_accounts["journal_id"], "format": "json"},
            headers=auth_headers,
        )
        assert export_json_resp.status_code == 200
        backup_data = export_json_resp.json()
        assert backup_data["journal"]["name"] == "Test Journal"
        assert len(backup_data["transactions"]) == 1
        assert backup_data["transactions"][0]["description"] == "Grocery shopping"

        # 4. Import a bank CSV file
        csv_file_content = (
            "Date,Description,Amount\n"
            "2026-02-10,Salary,1000.00\n"
            "2026-02-11,Coffee,-4.50\n"
        )
        
        # We upload using files and form data
        import_resp = await async_client.post(
            "/api/v1/files/import-csv",
            data={
                "journal_id": test_accounts["journal_id"],
                "debit_account_id": test_accounts["cash_id"],
                "credit_account_id": test_accounts["food_id"],
            },
            files={"file": ("bank.csv", csv_file_content, "text/csv")},
            headers=auth_headers,
        )
        assert import_resp.status_code == 200
        import_data = import_resp.json()
        assert import_data["imported"] == 2
        assert import_data["skipped"] == 0

        # Check that new transactions are listable
        txns_resp = await async_client.get(
            "/api/v1/transactions/",
            params={"journal_id": test_accounts["journal_id"]},
            headers=auth_headers,
        )
        txns = txns_resp.json()
        # Should have 3 total transactions now (1 created, 2 imported)
        assert len(txns) == 3
        descriptions = [t["description"] for t in txns]
        assert "Salary" in descriptions
        assert "Coffee" in descriptions

    async def test_upload_journal_backup_json(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        backup_json = {
            "journal": {
                "name": "Restored Journal",
                "description": "Restored from backup"
            },
            "accounts": [
                {"name": "assets:checking", "account_type": "ASSET"},
                {"name": "expenses:groceries", "account_type": "EXPENSE"}
            ],
            "transactions": [
                {
                    "date": "2026-03-01",
                    "description": "Weekly grocery run",
                    "entries": [
                        {"account_name": "expenses:groceries", "amount": "120.50", "currency": "USD"},
                        {"account_name": "assets:checking", "amount": "-120.50", "currency": "USD"}
                    ]
                }
            ]
        }

        # Upload JSON
        resp = await async_client.post(
            "/api/v1/files/",
            files={"file": ("backup.json", json.dumps(backup_json), "application/json")},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        journal_data = resp.json()
        assert journal_data["name"] == "Restored Journal"
        assert "id" in journal_data
        
        journal_id = journal_data["id"]

        # Verify transactions exist in the restored journal
        txns_resp = await async_client.get(
            "/api/v1/transactions/",
            params={"journal_id": journal_id},
            headers=auth_headers,
        )
        txns = txns_resp.json()
        assert len(txns) == 1
        assert txns[0]["description"] == "Weekly grocery run"
        assert len(txns[0]["entries"]) == 2
