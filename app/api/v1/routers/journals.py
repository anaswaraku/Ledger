# app/api/v1/routers/journals.py
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.journal import JournalCreate, JournalResponse
from app.application.services.journal_service import JournalService
from app.dependencies import get_current_user
from app.domain.models.user import User
from app.infrastructure.db.database import get_db
from app.infrastructure.db.repositories.journal_repo import JournalRepository

router = APIRouter(prefix="/api/v1/journals", tags=["Journals"])


def _make_service(db: AsyncSession) -> JournalService:
    return JournalService(JournalRepository(db))


@router.post(
    "/",
    response_model=JournalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accounting journal",
)
async def create_journal(
    data: JournalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    journal = await _make_service(db).create(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
    )
    return journal  # type: ignore[return-value]


@router.get(
    "/",
    response_model=list[JournalResponse],
    summary="List all journals owned by the current user",
)
async def list_journals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JournalResponse]:
    return await _make_service(db).list_for_user(current_user.id)  # type: ignore[return-value]


@router.get(
    "/{journal_id}",
    response_model=JournalResponse,
    summary="Get a specific journal by ID",
)
async def get_journal(
    journal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    return await _make_service(db).get_or_404(journal_id, current_user.id)  # type: ignore[return-value]


@router.delete(
    "/{journal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific journal by ID",
)
async def delete_journal(
    journal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await _make_service(db).delete(journal_id, current_user.id)
