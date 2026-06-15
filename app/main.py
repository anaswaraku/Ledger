# app/main.py


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging

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

#  Middleware 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Routers ─

from app.api.v1.routers import auth, transactions, accounts, reports, files, journals, currencies, charts, budgets  # noqa: E402

app.include_router(auth.router)
app.include_router(journals.router)
app.include_router(transactions.router)
app.include_router(accounts.router)
app.include_router(reports.router)
app.include_router(files.router) 
app.include_router(currencies.router)
app.include_router(charts.router)
app.include_router(budgets.router)

#  Root endpoints 

from uuid import UUID

from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


@app.get("/", tags=["Web"], summary="Application root")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/auth/login", tags=["Web"], summary="Login Page")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/login.html")


@app.get("/auth/register", tags=["Web"], summary="Register Page")
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/register.html")


@app.get("/dashboard", tags=["Web"], summary="Dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard/dashboard.html")


@app.get("/journals", tags=["Web"], summary="Journals list")
async def journals_page(request: Request):
    return templates.TemplateResponse(request=request, name="journals/journals.html")


@app.get("/journals/{journal_id}", tags=["Web"], summary="Journal detail")
async def journal_detail_page(request: Request, journal_id: UUID):
    return templates.TemplateResponse(
        request=request,
        name="journals/detail.html",
        context={"journal_id": str(journal_id)},
    )


@app.get("/accounts", tags=["Web"], summary="Accounts page")
async def accounts_page(request: Request):
    return templates.TemplateResponse(request=request, name="accounts/accounts.html")


@app.get("/transactions", tags=["Web"], summary="Transactions page")
async def transactions_page(request: Request):
    return templates.TemplateResponse(request=request, name="transactions/transactions.html")


@app.get("/reports", tags=["Web"], summary="Reports page")
async def reports_page(request: Request):
    return templates.TemplateResponse(request=request, name="reports/reports.html")


@app.get("/health", tags=["Health"], summary="Health check")
async def health() -> dict[str, str]:
    """Used by Docker, load-balancers, and uptime monitors."""
    return {"status": "ok"}
