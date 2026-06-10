from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/files", tags=["Files"])


@router.post("/")
def upload_file():
    """Upload Journal File"""
    return "upload files"


@router.post("/import-csv")
def import_csv():
    """Import CSV"""
    # /api/v1/files/import-csv
    return "import csv"


@router.get("/export")
def export_journal():
    """Export Journal (CSV/JSON)"""
    return "export journal file"
