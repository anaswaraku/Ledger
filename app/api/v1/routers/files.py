# app/api/v1/routers/files.py
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.file import CSVImportResponse
from app.api.v1.schemas.journal import JournalResponse
from app.application.services.file_service import FileService, JournalImportError
from app.dependencies import get_current_user, get_file_service
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/files", tags=["Files"])

@router.post(
    "/",
    response_model=JournalResponse | CSVImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload journal backup file (JSON) or Transaction entries (CSV)",
)
async def upload_file(
    file: UploadFile = File(...),
    journal_id: uuid.UUID | None = Form(None),
    service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user),
) -> JournalResponse | CSVImportResponse:
    """
    Restore a journal from an uploaded JSON backup file OR import CSV transactions.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name missing.",
        )
        
    if file.filename.endswith(".csv"):
        if not journal_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="journal_id form field is required when uploading a CSV file.",
            )
        content = await file.read()
        try:
            csv_str = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text encoding in CSV file.",
            )
        return await service.import_transactions_csv(
            owner_id=current_user.id,
            journal_id=journal_id,
            csv_content=csv_str,
        )

    elif file.filename.endswith(".json"):
        content = await file.read()
        try:
            json_str = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text encoding in file.",
            )
        try:
            journal = await service.import_journal_json(owner_id=current_user.id, json_content=json_str)
        except JournalImportError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        return journal  # type: ignore[return-value]
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON journal backup files and CSV transaction files are supported.",
        )


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
    service: FileService = Depends(get_file_service),
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

    result = await service.import_csv(
        owner_id=current_user.id,
        journal_id=journal_id,
        debit_account_id=debit_account_id,
        credit_account_id=credit_account_id,
        csv_content=csv_str,
    )
    return result


@router.post(
    "/import-accounts-csv",
    response_model=CSVImportResponse,
    summary="Import accounts from CSV file",
)
async def import_accounts_csv(
    journal_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user),
) -> CSVImportResponse:
    """
    Import accounts from a CSV file into the specified journal.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )

    content = await file.read()
    try:
        csv_str = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid text encoding in CSV file.",
        )

    result = await service.import_accounts_csv(
        owner_id=current_user.id,
        journal_id=journal_id,
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
    entity: str = Query("transactions", description="What to export: transactions, accounts, or all"),
    service: FileService = Depends(get_file_service),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Export journal data as CSV or JSON stream.
    """
    fmt = format.lower()
    ent = entity.lower()

    if fmt == "csv":
        if ent == "accounts":
            data = await service.export_accounts_csv(owner_id=current_user.id, journal_id=journal_id)
            filename = f"accounts_{journal_id}.csv"
        else:
            data = await service.export_transactions_csv(owner_id=current_user.id, journal_id=journal_id)
            filename = f"transactions_{journal_id}.csv"
        media_type = "text/csv"
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
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
