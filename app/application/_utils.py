# app/application/_utils.py
"""
Shared helpers used across multiple application services.

Centralises logic that was previously copy-pasted into each service:
  - Journal ownership guard  (was repeated 13+ times)
  - Currency conversion      (was duplicated in ReportService & BudgetService)
  - Missing-rate deduplication (was in ReportService, imported by BudgetService)
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status

from app.domain.money import MissingExchangeRateError


# ── Journal guard ─────────────────────────────────────────────────────────────

async def get_journal_or_404(journal_repo, journal_id, owner_id):
    """
    Return the journal if it exists and belongs to owner_id.

    Raises:
        HTTPException 404: journal missing or not owned by the user.
    """
    journal = await journal_repo.get_by_id_and_owner(journal_id, owner_id)
    if not journal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal not found.",
        )
    return journal


# ── Currency conversion ────────────────────────────────────────────────────────

async def convert_amount(
    market_price_repo,
    amount: Decimal,
    from_currency: str,
    to_currency: str,
    as_of: date,
) -> Decimal:
    """
    Convert *amount* from *from_currency* to *to_currency* using the closest
    historical market price on or before *as_of*.

    Returns the original amount unchanged when both currencies are the same.

    Raises:
        MissingExchangeRateError: no rate is available for this pair / date.
    """
    if from_currency.upper() == to_currency.upper():
        return amount

    rate = await market_price_repo.get_rate(from_currency, to_currency, as_of)
    if rate is None:
        raise MissingExchangeRateError(from_currency, to_currency, as_of, amount)

    return amount * rate


# ── Rate-error deduplication ───────────────────────────────────────────────────

def deduplicate_rates(missing: list[dict]) -> list[dict]:
    """
    Collapse duplicate missing-rate dicts (same from/to/date) into one entry
    with a *transaction_count* field showing how many rows were affected.
    """
    grouped: dict[tuple, int] = defaultdict(int)
    for r in missing:
        grouped[(r["from"], r["to"], r["date"])] += 1
    return [
        {"from": k[0], "to": k[1], "date": k[2], "transaction_count": v}
        for k, v in grouped.items()
    ]
