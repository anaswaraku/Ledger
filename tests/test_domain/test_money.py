import pytest
from decimal import Decimal
from app.domain.money import Money, CurrencyMismatchError

def test_money_creation():
    m = Money(Decimal("100.50"), "USD")
    assert m.amount == Decimal("100.50")
    assert m.currency == "USD"

def test_money_addition():
    m1 = Money(Decimal("100.00"), "USD")
    m2 = Money(Decimal("50.00"), "USD")
    res = m1 + m2
    assert res.amount == Decimal("150.00")
    assert res.currency == "USD"

def test_money_addition_mismatch():
    m1 = Money(Decimal("100.00"), "USD")
    m2 = Money(Decimal("50.00"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        _ = m1 + m2

def test_money_subtraction():
    m1 = Money(Decimal("100.00"), "USD")
    m2 = Money(Decimal("40.00"), "USD")
    res = m1 - m2
    assert res.amount == Decimal("60.00")
    assert res.currency == "USD"

def test_money_subtraction_mismatch():
    m1 = Money(Decimal("100.00"), "USD")
    m2 = Money(Decimal("40.00"), "EUR")
    with pytest.raises(CurrencyMismatchError):
        _ = m1 - m2

def test_money_negation():
    m = Money(Decimal("100.00"), "USD")
    res = -m
    assert res.amount == Decimal("-100.00")
    assert res.currency == "USD"

def test_money_multiplication():
    m = Money(Decimal("100.00"), "USD")
    res = m * Decimal("1.5")
    assert res.amount == Decimal("150.00")
    assert res.currency == "USD"

    res_int = m * 2
    assert res_int.amount == Decimal("200.00")

    res_r = Decimal("2.5") * m
    assert res_r.amount == Decimal("250.00")

def test_money_division():
    m = Money(Decimal("100.00"), "USD")
    res = m / Decimal("2.5")
    assert res.amount == Decimal("40.00")
    assert res.currency == "USD"

    res_int = m / 4
    assert res_int.amount == Decimal("25.00")

def test_money_conversion():
    m = Money(Decimal("100.00"), "USD")
    res = m.convert(Decimal("0.92"), "EUR")
    assert res.amount == Decimal("92.00")
    assert res.currency == "EUR"
