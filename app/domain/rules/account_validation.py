# app/domain/rules/account_validation.py
"""
Validation rules for hierarchical account names (hledger-compatible format).

Valid examples:
  assets:bank:checking
  liabilities:creditcard:visa
  expenses:food:groceries
  income:salary
  equity:opening-balances
"""
import re

VALID_TOP_LEVELS = frozenset({"assets", "liabilities", "equity", "income", "expenses"})

# Each segment: starts with letter, then letters/digits/hyphens/underscores
_SEGMENT = r"[a-zA-Z][a-zA-Z0-9_\-]*"
ACCOUNT_NAME_RE = re.compile(rf"^{_SEGMENT}(?::{_SEGMENT})*$")


class AccountValidationError(ValueError):
    """Raised when an account name fails structural validation."""


def validate_account_name(name: str) -> str:
    """
    Validate and normalise an hledger-style hierarchical account name.

    Returns:
        The normalised (lowercase, stripped) account name.

    Raises:
        AccountValidationError: If the name is empty, malformed, or has an
            unrecognised top-level account type.
    """
    if not name or not name.strip():
        raise AccountValidationError("Account name cannot be empty.")

    normalised = name.strip().lower()

    if not ACCOUNT_NAME_RE.match(normalised):
        raise AccountValidationError(
            f"Invalid account name: '{name}'. "
            "Use lowercase letters, digits, hyphens, and underscores, "
            "with ':' as the hierarchy separator "
            "(e.g. 'assets:bank:checking')."
        )

    top_level = normalised.split(":")[0]
    if top_level not in VALID_TOP_LEVELS:
        raise AccountValidationError(
            f"Account name must begin with a recognised type. "
            f"Got '{top_level}', expected one of: "
            f"{sorted(VALID_TOP_LEVELS)}."
        )

    return normalised
