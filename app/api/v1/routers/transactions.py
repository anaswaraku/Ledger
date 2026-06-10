from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.get("/")
def list_transaction():
    """List Transactions"""
    return "List Transactions"


@router.post("/")
def create_transaction():
    """Create Transactions"""
    return "Create Transaction"


@router.get("/{id}")
def get_transaction_details(id:int):
    """Get Transaction details"""
    # /api/v1/transactions/{id}
    return "get transaction details"


@router.put("{id}")
def update_transaction(id:int):
    """Update transaction"""
    # /api/v1/transactions/{id}
    return "update transaction"


@router.delete("/{id}")
def delete_transaction(id:int):
    """Delete Transaction"""
    # /api/v1/transactions/{id}
    return "delete transactions"
