# app/infrastructure/external/csv_importer.py
"""
Parse bank-statement CSV files into structured row dicts.

Expected CSV columns: Date, Description, Amount
(header names are case-insensitive, whitespace-trimmed).
"""
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class ParsedRow:
    """A single successfully parsed CSV row."""

    date: date
    description: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class RowError:
    """A row that could not be parsed."""

    row: int
    message: str


@dataclass(frozen=True, slots=True)
class CSVParseResult:
    rows: list[ParsedRow]
    errors: list[RowError]


_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d")


def _parse_date(raw: str) -> date:
    """Try common date formats, raise ValueError on failure."""
    stripped = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(stripped, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: '{stripped}'")


def parse_csv(content: str) -> CSVParseResult:
    """
    Parse CSV text content into rows and errors.

    Returns:
        CSVParseResult with successfully parsed rows and any row-level errors.
    """
    reader = csv.DictReader(io.StringIO(content))

    # Normalise field names to lowercase stripped
    if reader.fieldnames is None:
        return CSVParseResult(rows=[], errors=[RowError(row=0, message="Empty CSV file or missing header.")])

    normalised_fields = {f.strip().lower(): f for f in reader.fieldnames}

    required = {"date", "description", "amount"}
    missing = required - normalised_fields.keys()
    if missing:
        return CSVParseResult(
            rows=[],
            errors=[RowError(row=0, message=f"Missing required columns: {sorted(missing)}")],
        )

    date_col = normalised_fields["date"]
    desc_col = normalised_fields["description"]
    amt_col = normalised_fields["amount"]

    rows: list[ParsedRow] = []
    errors: list[RowError] = []

    for i, raw_row in enumerate(reader, start=2):  # row 1 is header
        try:
            parsed_date = _parse_date(raw_row[date_col])
        except (ValueError, KeyError) as exc:
            errors.append(RowError(row=i, message=f"Invalid date: {exc}"))
            continue

        desc = (raw_row.get(desc_col) or "").strip()
        if not desc:
            errors.append(RowError(row=i, message="Empty description."))
            continue

        raw_amount = (raw_row.get(amt_col) or "").strip().replace(",", "")
        try:
            amount = Decimal(raw_amount)
        except (InvalidOperation, ValueError):
            errors.append(RowError(row=i, message=f"Invalid amount: '{raw_amount}'"))
            continue

        if amount == 0:
            errors.append(RowError(row=i, message="Amount must not be zero."))
            continue

        rows.append(ParsedRow(date=parsed_date, description=desc, amount=amount))

    return CSVParseResult(rows=rows, errors=errors)

@dataclass(frozen=True, slots=True)
class ParsedDoubleEntryRow:
    """A row containing two accounts and their amounts."""
    date: date
    payee: str
    description: str
    account1_name: str
    amount1: Decimal
    account2_name: str
    amount2: Decimal
    currency: str

@dataclass(frozen=True, slots=True)
class DoubleEntryCSVParseResult:
    rows: list[ParsedDoubleEntryRow]
    errors: list[RowError]

def parse_double_entry_csv(content: str) -> DoubleEntryCSVParseResult:
    """
    Parse CSV with columns: date, payee, description, account1name, amount1, account2name, amount2, currency
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return DoubleEntryCSVParseResult(rows=[], errors=[RowError(row=0, message="Empty CSV file or missing header.")])

    normalised_fields = {f.strip().lower(): f for f in reader.fieldnames}
    
    # We allow variations like account1name or account1, amount1 etc.
    # But let's look for exactly what the user specified
    required_keys = {"date", "payee", "description", "account1name", "amount1", "account2name", "amount2"}
    missing = required_keys - normalised_fields.keys()
    
    # If standard user keys are missing, we could try to guess, but let's strictly require them for now.
    if missing:
        return DoubleEntryCSVParseResult(
            rows=[],
            errors=[RowError(row=0, message=f"Missing required columns: {sorted(missing)}")]
        )

    date_col = normalised_fields["date"]
    payee_col = normalised_fields["payee"]
    desc_col = normalised_fields["description"]
    acc1_col = normalised_fields["account1name"]
    amt1_col = normalised_fields["amount1"]
    acc2_col = normalised_fields["account2name"]
    amt2_col = normalised_fields["amount2"]
    curr_col = normalised_fields.get("currency") # Optional

    rows: list[ParsedDoubleEntryRow] = []
    errors: list[RowError] = []

    for i, raw_row in enumerate(reader, start=2):
        try:
            parsed_date = _parse_date(raw_row[date_col])
        except (ValueError, KeyError) as exc:
            errors.append(RowError(row=i, message=f"Invalid date: {exc}"))
            continue

        desc = (raw_row.get(desc_col) or "").strip()
        payee = (raw_row.get(payee_col) or "").strip()
        acc1 = (raw_row.get(acc1_col) or "").strip()
        acc2 = (raw_row.get(acc2_col) or "").strip()
        currency = "USD"
        if curr_col:
            c = (raw_row.get(curr_col) or "").strip()
            if c:
                currency = c.upper()

        if not acc1 or not acc2:
            errors.append(RowError(row=i, message="Both account names must be provided."))
            continue

        raw_amt1 = (raw_row.get(amt1_col) or "").strip().replace(",", "")
        raw_amt2 = (raw_row.get(amt2_col) or "").strip().replace(",", "")
        
        try:
            amount1 = Decimal(raw_amt1)
            amount2 = Decimal(raw_amt2)
        except (InvalidOperation, ValueError):
            errors.append(RowError(row=i, message="Invalid amounts provided."))
            continue

        rows.append(ParsedDoubleEntryRow(
            date=parsed_date,
            payee=payee,
            description=desc,
            account1_name=acc1,
            amount1=amount1,
            account2_name=acc2,
            amount2=amount2,
            currency=currency
        ))

    return DoubleEntryCSVParseResult(rows=rows, errors=errors)

@dataclass(frozen=True, slots=True)
class ParsedAccountRow:
    """A row containing account name and type."""
    name: str
    account_type: str

@dataclass(frozen=True, slots=True)
class AccountCSVParseResult:
    rows: list[ParsedAccountRow]
    errors: list[RowError]

def parse_account_csv(content: str) -> AccountCSVParseResult:
    """
    Parse CSV with columns: name, type
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return AccountCSVParseResult(rows=[], errors=[RowError(row=0, message="Empty CSV file or missing header.")])

    normalised_fields = {f.strip().lower(): f for f in reader.fieldnames}
    
    required_keys = {"name", "type"}
    missing = required_keys - normalised_fields.keys()
    
    if missing:
        return AccountCSVParseResult(
            rows=[],
            errors=[RowError(row=0, message=f"Missing required columns: {sorted(missing)}")]
        )

    name_col = normalised_fields["name"]
    type_col = normalised_fields["type"]

    rows: list[ParsedAccountRow] = []
    errors: list[RowError] = []

    for i, raw_row in enumerate(reader, start=2):
        name = (raw_row.get(name_col) or "").strip()
        account_type = (raw_row.get(type_col) or "").strip()

        if not name:
            errors.append(RowError(row=i, message="Account name cannot be empty."))
            continue
            
        if not account_type:
            errors.append(RowError(row=i, message="Account type cannot be empty."))
            continue

        rows.append(ParsedAccountRow(
            name=name,
            account_type=account_type
        ))

    return AccountCSVParseResult(rows=rows, errors=errors)
