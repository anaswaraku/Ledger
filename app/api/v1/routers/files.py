# app/api/v1/routers/files.py
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.file import CSVImportResponse
from app.api.v1.schemas.journal import JournalResponse
from app.application.services.file_service import FileService
from app.application.use_cases.import_csv import ImportCSVUseCase
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.account_repo import AccountRepository
from app.infrastructure.db.repositories.journal_repo import JournalRepository
from app.infrastructure.db.repositories.transaction_repo import TransactionRepository

router = APIRouter(prefix="/api/v1/files", tags=["Files"])


def _make_file_service(db: AsyncSession) -> FileService:
    return FileService(
        txn_repo=TransactionRepository(db),
        journal_repo=JournalRepository(db),
        account_repo=AccountRepository(db),
    )


@router.post(
    "/",
    response_model=JournalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload journal backup file (JSON)",
)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    """
    Restore a journal from an uploaded JSON backup file.
    """
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON journal backup files are supported.",
        )

    content = await file.read()
    try:
        json_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text encoding in file.",
        )

    service = _make_file_service(db)
    journal = await service.import_journal_json(owner_id=current_user.id, json_content=json_str)
    return journal  # type: ignore[return-value]


@router.post(
    "/import-csv",
    response_model=CSVImportResponse,
    summary="Import transactions from bank CSV file",
)
async def import_csv(
    journal_id: uuid.UUID = Form(...),
    debit_account_id: uuid.UUID = Form(...),
    credit_account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CSVImportResponse:
    """
    Import transactions from a CSV file into the specified journal.
    """
    content = await file.read()
    try:
        csv_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text encoding in CSV file.",
        )

    service = _make_file_service(db)
    use_case = ImportCSVUseCase(service)
    result = await use_case.execute(
        owner_id=current_user.id,
        journal_id=journal_id,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
        csv_content=csv_str,
    )
    return result


@router.get(
    "/export",
    summary="Export journal data (CSV or JSON)",
)
async def export_journal(
    journal_id: uuid.UUID = Query(...),
    format: str = Query("csv", description="Format to export (csv or json)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Export all transactions in a journal as CSV or JSON stream.
    """
    service = _make_file_service(db)
    fmt = format.lower()

    if fmt == "csv":
        data = await service.export_csv(owner_id=current_user.id, journal_id=journal_id)
        media_type = "text/csv"
        filename = f"journal_{journal_id}.csv"
    elif fmt == "json":
        data = await service.export_json(owner_id=current_user.id, journal_id=journal_id)
        media_type = "application/json"
        filename = f"journal_{journal_id}.json"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Must be 'csv' or 'json'.",
        )

    async def gen():
        yield data

    return StreamingResponse(
        gen(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
