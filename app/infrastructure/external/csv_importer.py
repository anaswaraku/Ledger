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
