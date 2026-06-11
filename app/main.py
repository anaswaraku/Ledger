# app/main.py
"""
Ledger Web Application — FastAPI entry point.

Start the server:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Application lifecycle: startup → serve → shutdown."""
    setup_logging()
    logger = logging.getLogger("ledger")
    logger.info("Ledger Web Application starting up…")
    yield
    # Graceful shutdown: dispose the async engine connection pool
    from app.infrastructure.db.database import engine
    await engine.dispose()
    logger.info("Ledger Web Application shut down cleanly.")


app = FastAPI(
    title="Ledger Web Application",
    description=(
        "A modern web application for plain-text double-entry accounting, "
        "inspired by hledger."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

from app.api.v1.routers import auth, transactions, accounts, reports, files, journals  # noqa: E402

app.include_router(auth.router)
app.include_router(journals.router)
app.include_router(transactions.router)
app.include_router(accounts.router)
app.include_router(reports.router)
app.include_router(files.router)

# ── Root endpoints ────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="Application root")
async def home() -> dict[str, Any]:
    return {
        "message": "Ledger Web Application is running",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health() -> dict[str, str]:
    """Used by Docker, load-balancers, and uptime monitors."""
    return {"status": "ok"}
