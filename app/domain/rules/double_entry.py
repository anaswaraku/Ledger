# app/domain/rules/double_entry.py
"""
Core double-entry accounting validation rule.

This is a DOMAIN RULE — it must be enforced here (domain layer) rather than
solely in the API schema layer. The schema validator calls this function so
that the rule is defined exactly once.
"""
from decimal import Decimal
from typing import Sequence


class DoubleEntryError(ValueError):
    """
    Raised when a set of transaction entries violates double-entry accounting.
    Double-entry requires:
      - At least two postings per transaction
      - The sum of all amounts equals exactly zero (debits == credits)
    """


def validate_double_entry(amounts: Sequence[Decimal]) -> None:
    """
    Validate that a sequence of amounts satisfies double-entry rules.

    Args:
        amounts: Monetary amounts for each posting. Positive = debit, negative = credit.

    Raises:
        DoubleEntryError: If fewer than 2 entries are given or the sum is non-zero.

    Example:
        >>> validate_double_entry([Decimal("50.00"), Decimal("-50.00")])  # OK
        >>> validate_double_entry([Decimal("100"), Decimal("-60"), Decimal("-40")])  # OK
        >>> validate_double_entry([Decimal("50"), Decimal("-40")])  # raises
    """
    if len(amounts) < 2:
        raise DoubleEntryError(
            f"A transaction must have at least 2 entries, got {len(amounts)}."
        )

    total = sum(amounts, Decimal(0))

    if total != Decimal(0):
        raise DoubleEntryError(
            f"Transaction entries must balance to zero (debits == credits). "
            f"Current imbalance: {total:+.10f}"
        )
