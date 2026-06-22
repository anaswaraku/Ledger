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
Create an endpoint in `app/api/v1/routers/transaction_notes.py`. Following the project's DI pattern, add the service factory in `app/dependencies.py` first:

```python
# app/dependencies.py  — add this factory function
async def get_transaction_note_service(db: AsyncSession = Depends(get_db)):
    from app.application.services.transaction_note_service import TransactionNoteService
    from app.infrastructure.db.repositories.transaction_note_repo import TransactionNoteRepository
    return TransactionNoteService(TransactionNoteRepository(db))
```

Then create the router, injecting the service via `Depends()`:

```python
# app/api/v1/routers/transaction_notes.py
from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.api.v1.schemas.transaction_note import TransactionNoteCreate, TransactionNoteResponse
from app.application.services.transaction_note_service import TransactionNoteService
from app.dependencies import get_current_user, get_transaction_note_service
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/transactions/{transaction_id}/notes", tags=["Transaction Notes"])

@router.post("/", response_model=TransactionNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    transaction_id: UUID,
    payload: TransactionNoteCreate,
    service: TransactionNoteService = Depends(get_transaction_note_service),
    current_user: User = Depends(get_current_user),
):
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

---

## Guide 3: How to Add a New API Router

This guide shows the exact steps to wire up a brand new API router into the application, matching the pattern used in `app/main.py`.

### Step 1: Create the Router File

Create a new file in `app/api/v1/routers/`, e.g. `app/api/v1/routers/tags.py`:

```python
# app/api/v1/routers/tags.py
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.domain.models.user import User

router = APIRouter(prefix="/api/v1/tags", tags=["Tags"])

@router.get("/", summary="List all tags")
async def list_tags(current_user: User = Depends(get_current_user)) -> list[str]:
    """Returns a list of all unique tags used across transactions."""
    return []
```

> [!IMPORTANT]
> If your router needs a service (e.g. a database query), **do not** create a local `_make_service(db)` factory. Instead, add a factory function to `app/dependencies.py` following the existing pattern:
> ```python
> # app/dependencies.py
> async def get_tag_service(db: AsyncSession = Depends(get_db)):
>     from app.application.services.tag_service import TagService
>     return TagService(db)
> ```
> Then inject it via `Depends(get_tag_service)` in your router handler.

### Step 2: Register the Router in `app/main.py`

Import and include the router in `app/main.py` alongside the existing routers:

```python
# app/main.py

# Add the import alongside existing router imports (line 48)
from app.api.v1.routers import auth, transactions, accounts, reports, files, journals, currencies, budgets, plot, tags

# Add the include_router call after the existing include_router() calls (currently ending at line 58)
app.include_router(tags.router)
```

### Step 3: Verify in Swagger UI

Restart the application and open [http://localhost:8000/docs](http://localhost:8000/docs). Your new `Tags` section should appear with its endpoints listed.

```bash
# If running locally
uvicorn app.main:app --reload

# If running in Docker
docker compose restart app
```

> [!IMPORTANT]
> The router's `prefix` must start with `/api/v1/` to remain consistent with all other API routes in this application.

---

## Guide 4: How to Write and Run Tests

The test suite uses `pytest` with `pytest-asyncio` and an in-memory SQLite database (via `aiosqlite`) so no running PostgreSQL instance is required during testing.

### Test Configuration

Tests are configured in `pytest.ini` at the project root:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

`asyncio_mode = auto` means all `async def` test functions are automatically treated as async tests — no `@pytest.mark.asyncio` decorator is needed.

### Test Database Override

The test suite overrides the `get_db` dependency with an in-memory SQLite session. This is already set up in `tests/conftest.py`. No PostgreSQL connection is required when running tests.

### Writing a New Test

Add tests to the appropriate directory under `tests/`:

```
tests/
├── test_api/        ← HTTP endpoint tests using httpx TestClient
├── test_services/   ← Application service unit tests
└── test_domain/     ← Domain rule unit tests (pure Python, no DB)
```

**Example — API test:**

```python
# tests/test_api/test_tags.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_tags_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/tags/")
    assert response.status_code == 401
```

**Example — Domain rule test (no DB needed):**

```python
# tests/test_domain/test_double_entry.py
from decimal import Decimal
from app.domain.rules.double_entry import validate_balance

def test_balanced_entries_pass():
    entries = [Decimal("50.00"), Decimal("-50.00")]
    assert validate_balance(entries) is True

def test_unbalanced_entries_raise():
    entries = [Decimal("50.00"), Decimal("-30.00")]
    with pytest.raises(ValueError):
        validate_balance(entries)
```

### Running Tests

```bash
# Run the full test suite
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_api/test_transactions.py

# Run a single test function
pytest tests/test_api/test_transactions.py::test_create_transaction

# Run and show print output
pytest -s
```

> [!NOTE]
> Tests use `aiosqlite` (SQLite in-memory) instead of PostgreSQL. If you see `OperationalError` relating to SQLite syntax, it is likely a Postgres-specific SQL construct that needs a test-compatible alternative.
