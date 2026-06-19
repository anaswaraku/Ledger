# Ledger Web Application - Developer Guides

This document provides step-by-step developer guides reflecting the current tooling and architecture of the Ledger Web Application.

---

## Guide 1: How to Run and Manage Database Migrations

Ledger Web uses **Alembic** alongside **SQLAlchemy** to manage schema migrations. 

> [!IMPORTANT]
> **Database Drivers Warning**: 
> The application uses `postgresql+asyncpg` for runtime database operations. However, Alembic operations are synchronous and use `postgresql+psycopg2`. Ensure you have both installed (typically via `pip install -r requirements.txt`).

### Scenario A: Running Migrations

* **Local Environment Setup**:
  If you are running the database locally outside Docker:
  ```bash
  alembic upgrade head
  ```

* **Docker Compose Environment Setup**:
  If you are running the system using Docker Compose:
  ```bash
  docker compose exec app alembic upgrade head
  ```

### Scenario B: Creating a New Migration (Autogenerating Schema Changes)
Alembic can automatically detect differences between your database schema and your SQLAlchemy models in `app/domain/models/`.

1. **Modify your models**:
   Add or edit SQLAlchemy model columns in `app/domain/models/` files.
2. **Register the model**:
   Ensure your model is imported in `app/domain/models/__init__.py` so that it is registered to `Base.metadata` in `alembic/env.py`.
3. **Autogenerate the migration file**:
   ```bash
   alembic revision --autogenerate -m "describe_your_changes"
   ```
4. **Review the migration script**:
   Open the newly created file in `alembic/versions/` to verify the generated operations before applying them.
5. **Apply the changes**:
   ```bash
   alembic upgrade head
   ```

### Scenario C: Rolling Back and Troubleshooting
* **Roll back the last migration**:
  ```bash
  alembic downgrade -1
  ```
* **Roll back all migrations (Resets database)**:
  ```bash
  alembic downgrade base
  ```
* **Check the current database schema revision**:
  ```bash
  alembic current
  ```
* **View the migration history**:
  ```bash
  alembic history --verbose
  ```

---

## Guide 2: How to Add a New Feature

This guide walks you through adding a new feature from database tables to UI templates using the project's Clean Architecture conventions. 

**Example Scenario**: We want to add a feature to support **Transaction Notes** where users can attach custom textual notes to transactions.

### Step 1: Create the Domain Model
Define the table schema and properties in `app/domain/models/`. Create `app/domain/models/transaction_note.py`:
```python
# app/domain/models/transaction_note.py
import uuid
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.domain.models.base import Base
from app.domain.models.mixins import UUIDMixin

class TransactionNote(UUIDMixin, Base):
    __tablename__ = "transaction_notes"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="notes"
    )
```

### Step 2: Register the Model
Import the model in `app/domain/models/__init__.py` so Alembic can discover it:
```python
# Add to app/domain/models/__init__.py
from app.domain.models.transaction_note import TransactionNote
```
Also update `Transaction` in `app/domain/models/transaction.py` to add the `notes` relationship:
```python
notes: Mapped[list["TransactionNote"]] = relationship(
    "TransactionNote",
    back_populates="transaction",
    cascade="all, delete-orphan"
)
```

### Step 3: Run Database Migrations
Generate and run the database migration to create the `transaction_notes` table:
```bash
alembic revision --autogenerate -m "add_transaction_notes_table"
alembic upgrade head
```

### Step 4: Add the Infrastructure Repository
Write a repository layer for CRUD queries in `app/infrastructure/db/repositories/transaction_note_repo.py`:
```python
# app/infrastructure/db/repositories/transaction_note_repo.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.transaction_note import TransactionNote

class TransactionNoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_transaction(self, transaction_id: UUID) -> list[TransactionNote]:
        stmt = select(TransactionNote).where(TransactionNote.transaction_id == transaction_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, transaction_id: UUID, content: str) -> TransactionNote:
        note = TransactionNote(transaction_id=transaction_id, content=content)
        self.db.add(note)
        await self.db.flush() # Flushes to database to populate note.id without committing yet
        return note
```

### Step 5: Implement Pydantic Schemas
Create request/response validators in `app/api/v1/schemas/transaction_note.py`:
```python
# app/api/v1/schemas/transaction_note.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class TransactionNoteCreate(BaseModel):
    content: str

class TransactionNoteResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    content: str

    model_config = ConfigDict(from_attributes=True)
```

### Step 6: Write the Application Service Use Case
Create a service in `app/application/services/transaction_note_service.py` to coordinate database actions:
```python
# app/application/services/transaction_note_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models.transaction_note import TransactionNote
from app.infrastructure.db.repositories.transaction_note_repo import TransactionNoteRepository

class TransactionNoteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TransactionNoteRepository(db)

    async def add_note(self, transaction_id: UUID, content: str) -> TransactionNote:
        note = await self.repo.create(transaction_id, content)
        await self.db.commit()
        return note
```

### Step 7: Expose API Routers
Create an endpoint in `app/api/v1/routers/transaction_notes.py`:
```python
# app/api/v1/routers/transaction_notes.py
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.database import get_db
from app.api.v1.schemas.transaction_note import TransactionNoteCreate, TransactionNoteResponse
from app.application.services.transaction_note_service import TransactionNoteService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/transactions/{transaction_id}/notes", tags=["Transaction Notes"])

@router.post("/", response_model=TransactionNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    transaction_id: UUID,
    payload: TransactionNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TransactionNoteService(db)
    return await service.add_note(transaction_id, payload.content)
```
Include this new router inside the main file `app/main.py`:
```python
from app.api.v1.routers import transaction_notes
app.include_router(transaction_notes.router)
```

### Step 8: Update User Interface and Templates
Connect HTMX actions to display notes dynamically in `app/templates/transactions/transactions.html`. For instance, you can use HTMX to post notes and swap the results into a sidebar block:
```html
<button hx-post="/api/v1/transactions/{{ txn_id }}/notes/"
        hx-vals='js:{content: document.getElementById("note-input").value}'
        hx-target="#notes-list"
        hx-swap="beforeend">
  Save Note
</button>
```

### Step 9: Write and Run Tests
Verify the code works correctly by adding unit tests in `tests/test_domain/test_notes.py` or similar:
```python
# tests/test_domain/test_notes.py
import pytest
from app.domain.models.transaction_note import TransactionNote

def test_note_creation():
    note = TransactionNote(content="Test note description")
    assert note.content == "Test note description"
```
Run your tests:
```bash
pytest tests/
```
