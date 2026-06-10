from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])

@router.get("/")
def list_accounts():
    """List Accounts"""
    pass

@router.post("/")
def create_account():
    """Create Account"""
    pass

@router.get("/{name}/register")
async def get_account_register_report(name: str):
    pass
