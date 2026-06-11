# tests/test_domain/test_double_entry.py
"""
Unit tests for the double-entry accounting domain rule.
These are pure Python tests — no database, no HTTP, no async.
"""
import pytest
from decimal import Decimal

from app.domain.rules.double_entry import DoubleEntryError, validate_double_entry


class TestValidateDoubleEntry:
    """Tests for validate_double_entry()"""

    # ── Happy path ────────────────────────────────────────────────────────────

    def test_two_entries_balanced(self):
        """Standard debit+credit pair must pass."""
        validate_double_entry([Decimal("50.00"), Decimal("-50.00")])

    def test_three_entries_split_balanced(self):
        """One debit split into two credits must pass."""
        validate_double_entry(
            [Decimal("100.00"), Decimal("-60.00"), Decimal("-40.00")]
        )

    def test_many_entries_balanced(self):
        """Multiple entries summing to zero must pass."""
        validate_double_entry(
            [
                Decimal("500.00"),
                Decimal("-200.00"),
                Decimal("-150.00"),
                Decimal("-100.00"),
                Decimal("-50.00"),
            ]
        )

    def test_high_precision_balanced(self):
        """High-precision decimals that balance must pass."""
        validate_double_entry(
            [Decimal("0.0000000001"), Decimal("-0.0000000001")]
        )

    def test_large_amounts_balanced(self):
        validate_double_entry([Decimal("999999.99"), Decimal("-999999.99")])

    # ── Failure: too few entries ──────────────────────────────────────────────

    def test_empty_list_raises(self):
        with pytest.raises(DoubleEntryError, match="at least 2 entries"):
            validate_double_entry([])

    def test_single_entry_raises(self):
        with pytest.raises(DoubleEntryError, match="at least 2 entries"):
            validate_double_entry([Decimal("100.00")])

    # ── Failure: imbalanced ───────────────────────────────────────────────────

    def test_two_entries_unbalanced(self):
        with pytest.raises(DoubleEntryError, match="balance to zero"):
            validate_double_entry([Decimal("50.00"), Decimal("-40.00")])

    def test_three_entries_unbalanced(self):
        with pytest.raises(DoubleEntryError, match="balance to zero"):
            validate_double_entry(
                [Decimal("100.00"), Decimal("-60.00"), Decimal("-30.00")]
            )

    def test_all_positive_raises(self):
        """All debits with no credits must fail."""
        with pytest.raises(DoubleEntryError):
            validate_double_entry([Decimal("50.00"), Decimal("50.00")])

    def test_all_negative_raises(self):
        """All credits with no debits must fail."""
        with pytest.raises(DoubleEntryError):
            validate_double_entry([Decimal("-50.00"), Decimal("-50.00")])

    # ── Error type ────────────────────────────────────────────────────────────

    def test_raises_double_entry_error_subclass_of_value_error(self):
        """DoubleEntryError must be a ValueError for Pydantic compatibility."""
        with pytest.raises(ValueError):
            validate_double_entry([Decimal("10")])


class TestAccountValidation:
    """Tests for account name validation rule."""

    def test_valid_simple_name(self):
        from app.domain.rules.account_validation import validate_account_name
        result = validate_account_name("assets:cash")
        assert result == "assets:cash"

    def test_valid_deep_hierarchy(self):
        from app.domain.rules.account_validation import validate_account_name
        result = validate_account_name("expenses:food:groceries")
        assert result == "expenses:food:groceries"

    def test_normalises_to_lowercase(self):
        from app.domain.rules.account_validation import validate_account_name
        result = validate_account_name("Assets:Bank")
        assert result == "assets:bank"

    def test_invalid_top_level(self):
        from app.domain.rules.account_validation import (
            AccountValidationError,
            validate_account_name,
        )
        with pytest.raises(AccountValidationError, match="recognised type"):
            validate_account_name("revenue:sales")

    def test_empty_name_raises(self):
        from app.domain.rules.account_validation import (
            AccountValidationError,
            validate_account_name,
        )
        with pytest.raises(AccountValidationError, match="empty"):
            validate_account_name("   ")

    def test_invalid_characters_raises(self):
        from app.domain.rules.account_validation import (
            AccountValidationError,
            validate_account_name,
        )
        with pytest.raises(AccountValidationError):
            validate_account_name("assets:bank account")  # space not allowed
