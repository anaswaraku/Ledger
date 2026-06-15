# app/application/use_cases/import_csv.py
"""
ImportCSV use case.
Orchestrates importing transactions from a CSV file.
"""
import uuid

from app.api.v1.schemas.file import CSVImportResponse
from app.application.services.file_service import FileService


class ImportCSVUseCase:
    """
    Encapsulates the 'import transactions from CSV' workflow.
    """

    def __init__(self, file_service: FileService) -> None:
        self.file_service = file_service

    async def execute(
        self,
        owner_id: uuid.UUID,
        journal_id: uuid.UUID,
        debit_account_id: uuid.UUID,
        credit_account_id: uuid.UUID,
        csv_content: str,
    ) -> CSVImportResponse:
        return await self.file_service.import_csv(
            owner_id=owner_id,
            journal_id=journal_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            csv_content=csv_content,
        )
