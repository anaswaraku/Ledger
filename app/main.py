from fastapi import FastAPI

app = FastAPI(title="Ledger Web Application")

@app.get("/")
def home():
    return{"Ledger Web Running"}

@app.post("/api/v1/register")
def user_registration():
    """User registration"""
    return "User registration"

@app.post("api/v1/login")
def user_login():
    """User Login (JWT)"""
    return "User Login"

@app.post("/api/v1/auth/logout")
def logout():
    """Logout"""
    return "Logout"

@app.get("/api/v1/transactions")
def list_transaction():
    """List Transactions"""
    return "List Transactions"

@app.post("/api/v1/transactions")
def create_transaction():
    """Create Transactions"""
    return "Create Transaction"

@app.get("/api/v1/transactions")
def get_transaction_details():
    """Get Transaction details"""
    #/api/v1/transactions/{id}
    return "get transaction details"

@app.put("/api/v1/transactions")
def update_transaction():
    """Update transaction"""
    #/api/v1/transactions/{id}
    return "update transaction"

@app.delete("/api/v1/transactions")
def delete_transaction():
    """Delete Transaction"""
    #/api/v1/transactions/{id}
    return "delete transactions"

@app.get("/api/v1/accounts")
def list_accounts():
    """List accounts"""
    return "list accounts"

@app.post("/api/v1/accounts")
def create_account():
    """Create account"""
    return "create account"

@app.get("/api/v1/accounts/")
def get_account_register_report():
    """	Account register report"""
    #/api/v1/accounts/{name}/register
    return "Account register report"

@app.get("/api/v1/reports/")
def get_balance_report():
    """Balance sheet"""
    #/api/v1/reports/balance-sheet
    return "balance sheet"

@app.get("/api/v1/reports")
def get_income_statement():
    """Income Statement"""
    #/api/v1/reports/balance-sheet
    return "income statement"

@app.get("/api/v1/reports/")
def get_cash_flow():
    """Cash Flow Report"""
    #/api/v1/reports/cash-flow
    return "cash flow"

@app.post("/api/v1/files")
def upload_file():
    """Upload Journal File"""
    return "upload files"

@app.post("/api/v1/files")
def import_csv():
    """Import CSV"""
    #/api/v1/files/import-csv
    return "import csv"

@app.get("/api/v1/files/export")
def export_journal():
    """Export Journal (CSV/JSON)"""
    return "export journal file"