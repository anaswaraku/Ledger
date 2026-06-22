# app/api/v1/routers/journals.py
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.schemas.journal import JournalCreate, JournalResponse, JournalUpdate
from app.application.services.journal_service import JournalService
from app.dependencies import get_current_user, get_journal_service
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/journals", tags=["Journals"])


@router.post(
    "/",
    response_model=JournalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new accounting journal",
)
async def create_journal(
    data: JournalCreate,
    service: JournalService = Depends(get_journal_service),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    journal = await service.create(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        base_currency=data.base_currency,
    )
    return journal  # type: ignore[return-value]


@router.get(
    "/",
    response_model=list[JournalResponse],
    summary="List all journals owned by the current user",
)
async def list_journals(
    service: JournalService = Depends(get_journal_service),
    current_user: User = Depends(get_current_user),
) -> list[JournalResponse]:
    return await service.list_for_user(current_user.id)  # type: ignore[return-value]


@router.get(
    "/{journal_id}",
    response_model=JournalResponse,
    summary="Get a specific journal by ID",
)
async def get_journal(
    journal_id: UUID,
    service: JournalService = Depends(get_journal_service),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    return await service.get_or_404(journal_id, current_user.id)  # type: ignore[return-value]


@router.delete(
    "/{journal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific journal by ID",
)
async def delete_journal(
    journal_id: UUID,
    service: JournalService = Depends(get_journal_service),
    current_user: User = Depends(get_current_user),
) -> None:
    await service.delete(journal_id, current_user.id)


@router.patch(
    "/{journal_id}",
    response_model=JournalResponse,
    summary="Update a specific journal by ID",
)
async def update_journal(
    journal_id: UUID,
    data: JournalUpdate,
    service: JournalService = Depends(get_journal_service),
    current_user: User = Depends(get_current_user),
) -> JournalResponse:
    journal = await service.update(
        journal_id=journal_id,
        owner_id=current_user.id,
        **data.model_dump(exclude_none=True),
    )
    return journal  # type: ignore[return-value]
