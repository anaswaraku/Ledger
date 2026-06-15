# app/application/services/file_service.py
"""
Business logic for CSV import and journal export (FR-6.3, FR-6.4, FR-1.7).
"""
import csv
import io
import json
import logging
import uuid
from decimal import Decimal

from fastapi import HTTPException, status

from app.api.v1.schemas.file import CSVImportResponse, CSVImportRowError
from app.domain.rules.double_entry import validate_double_entry, DoubleEntryError
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository
from app.infrastructure.external.csv_importer import ParsedRow, RowError, parse_csv

logger = logging.getLogger(__name__)


class FileService:
    """Handles CSV import and journal data export."""

    def __init__(
        self,
        txn_repo: TransactionRepository,
        journal_repo: JournalRepository,
        account_repo: AccountRepository,
    ) -> None:
        self.txn_repo = txn_repo
        self.journal_repo = journal_repo
        self.account_repo = account_repo

    # ── CSV Import ────────────────────────────────────────────────────────────

    async def import_csv(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        debit_account_id: uuid.UUID,
        credit_account_id: uuid.UUID,
        csv_content: str,
    ) -> CSVImportResponse:
        """Parse a CSV string and create double-entry transactions."""
        # 1. Verify journal ownership
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found.")

        # 2. Verify both accounts belong to this journal
        for acc_id, label in [
            (debit_account_id, "debit"),
            (credit_account_id, "credit"),
        ]:
            account = await self.account_repo.get_by_id(acc_id)
            if not account or account.journal_id != journal_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The {label} account does not exist in the specified journal.",
                )

        # 3. Parse CSV
        result = parse_csv(csv_content)

        errors = [CSVImportRowError(row=e.row, message=e.message) for e in result.errors]
        imported = 0

        # 4. Create a transaction for each valid row
        for row in result.rows:
            # Positive amount → debit the debit_account, credit the credit_account
            # Negative amount → reverse
            amount = row.amount
            entries_data = [
                {"account_id": debit_account_id, "amount": abs(amount), "currency": "USD"},
                {"account_id": credit_account_id, "amount": -abs(amount), "currency": "USD"},
            ]
            if amount < 0:
                # Flip: credit receives the positive, debit receives the negative
                entries_data = [
                    {"account_id": debit_account_id, "amount": amount, "currency": "USD"},
                    {"account_id": credit_account_id, "amount": -amount, "currency": "USD"},
                ]

            await self.txn_repo.create(
                journal_id=journal_id,
                date=row.date,
                description=row.description,
                payee=None,
                code=None,
                entries_data=entries_data,
            )
            imported += 1

        logger.info(
            "CSV import: %d imported, %d skipped for journal %s",
            imported, len(errors), journal_id,
        )
        return CSVImportResponse(imported=imported, skipped=len(errors), errors=errors)

    # ── Export ─────────────────────────────────────────────────────────────────

    async def export_csv(self, owner_id: uuid.UUID, journal_id: uuid.UUID) -> str:
        """Export all transactions in a journal as CSV text."""
        transactions = await self._get_all_transactions(owner_id, journal_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Description", "Payee", "Account ID", "Amount", "Currency"])

        for txn in transactions:
            for entry in txn.entries:
                writer.writerow([
                    txn.date.isoformat(),
                    txn.description,
                    txn.payee or "",
                    str(entry.account_id),
                    str(entry.amount),
                    entry.commodity,
                ])

        return output.getvalue()

    async def export_json(self, owner_id: uuid.UUID, journal_id: uuid.UUID) -> str:
        """Export the journal, its accounts, and all transactions as JSON text for backup."""
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found.")

        accounts = await self.account_repo.get_by_journal(journal_id)
        transactions = await self._get_all_transactions(owner_id, journal_id)

        data = {
            "journal": {
                "name": journal.name,
                "description": journal.description,
            },
            "accounts": [
                {
                    "name": acc.name,
                    "account_type": acc.account_type.value,
                }
                for acc in accounts
            ],
            "transactions": [
                {
                    "date": txn.date.isoformat(),
                    "description": txn.description,
                    "payee": txn.payee,
                    "code": txn.code,
                    "entries": [
                        {
                            "account_name": next((acc.name for acc in accounts if acc.id == e.account_id), ""),
                            "amount": str(e.amount),
                            "currency": e.commodity,
                        }
                        for e in txn.entries
                    ],
                }
                for txn in transactions
            ]
        }

        return json.dumps(data, indent=2)

    async def import_journal_json(self, owner_id: uuid.UUID, json_content: str):
        """Import a journal backup from JSON content."""
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file format.")

        if "journal" not in data or "name" not in data["journal"]:
            raise HTTPException(status_code=400, detail="Missing journal name in JSON.")

        # Create new journal
        journal = await self.journal_repo.create(
            owner_id=owner_id,
            name=data["journal"]["name"],
            description=data["journal"].get("description"),
        )

        # Create accounts
        account_name_map = {}
        for acc_data in data.get("accounts", []):
            acc_name = acc_data["name"]
            acc_type_str = acc_data["account_type"]
            from app.domain.models.account import AccountType
            try:
                acc_type = AccountType(acc_type_str.upper())
            except ValueError:
                acc_type = AccountType.ASSET

            acc = await self.account_repo.get_by_name_and_journal(acc_name, journal.id)
            if not acc:
                acc = await self.account_repo.create(
                    journal_id=journal.id,
                    name=acc_name,
                    account_type=acc_type,
                )
            account_name_map[acc_name] = acc.id

        # Create transactions
        from datetime import datetime
        for txn_data in data.get("transactions", []):
            try:
                txn_date = datetime.strptime(txn_data["date"][:10], "%Y-%m-%d").date()
            except ValueError:
                continue

            entries_data = []
            for entry_data in txn_data.get("entries", []):
                acc_name = entry_data.get("account_name")
                if not acc_name:
                    continue

                acc_id = account_name_map.get(acc_name)
                if not acc_id:
                    # Auto-create account if missing
                    parts = acc_name.lower().split(":")
                    prefix = parts[0]
                    from app.domain.models.account import AccountType
                    acc_type = AccountType.ASSET
                    if prefix.startswith("liabilit"):
                        acc_type = AccountType.LIABILITY
                    elif prefix.startswith("equit"):
                        acc_type = AccountType.EQUITY
                    elif prefix.startswith("income") or prefix.startswith("revenu"):
                        acc_type = AccountType.INCOME
                    elif prefix.startswith("expense"):
                        acc_type = AccountType.EXPENSE

                    acc = await self.account_repo.create(
                        journal_id=journal.id,
                        name=acc_name,
                        account_type=acc_type,
                    )
                    account_name_map[acc_name] = acc.id
                    acc_id = acc.id

                entries_data.append({
                    "account_id": acc_id,
                    "amount": Decimal(str(entry_data["amount"])),
                    "currency": entry_data.get("currency", "USD"),
                })

            if entries_data:
                await self.txn_repo.create(
                    journal_id=journal.id,
                    date=txn_date,
                    description=txn_data.get("description", ""),
                    payee=txn_data.get("payee"),
                    code=txn_data.get("code"),
                    entries_data=entries_data,
                )

        return journal

    async def _get_all_transactions(self, owner_id: uuid.UUID, journal_id: uuid.UUID):
        """Verify ownership and return all transactions for export."""
        journal = await self.journal_repo.get_by_id_and_owner(journal_id, owner_id)
        if not journal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found.")
        # Fetch with a generous limit for export
        return await self.txn_repo.list_by_journal(journal_id, skip=0, limit=100_000)
