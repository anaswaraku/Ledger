#raise  error

from dataclasses import dataclass
from decimal import Decimal
from datetime import date

class CurrencyMismatchError(ValueError):
    def __init__(self, cur1:str,cur2:str):
        super().__init__(f"Cannot operate across currencies without conversion: {cur1} vs {cur2}")
        self.cur1 = cur1
        self.cur2 = cur2

class UnbalancedTransactionError(ValueError):
    pass

class MissingExchangeRateError(ValueError):
    def __init__(self, from_currency: str, to_currency: str, as_of: date, amount: Decimal) -> None:
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.as_of = as_of
        self.amount = amount
        super().__init__(f"Missing exchange rate: {from_currency} -> {to_currency} on {as_of}")

    def to_dict(self) -> dict:
        return {
            "from": self.from_currency,
            "to": self.to_currency,
            "date": str(self.as_of),
        }

class MissingExchangeRatesCollectedError(ValueError):
    """Raised by report service when one or more exchange rates are missing."""
    def __init__(self, missing_rates: list[dict]) -> None:
        self.missing_rates = missing_rates
        super().__init__(f"{len(missing_rates)} exchange rate(s) missing")

@dataclass(frozen=True)
class Money:
    amount:Decimal
    currency:str
    
    def __add__(self, other:"Money")->"Money":
        if self.currency!=other.currency:
            raise CurrencyMismatchError(self.currency,other.currency)
        return Money(self.amount+other.amount,self.currency)
    def __sub__(self, other:"Money")->"Money":
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency,other.currency)
        return Money(self.amount-other.amount,self.currency)
    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)
    def __mul__(self, other: Decimal) -> "Money":
        if not isinstance(other, (int, Decimal)):
            return NotImplemented
        return Money(self.amount * other, self.currency)
    def __rmul__(self, other: Decimal) -> "Money":
        return self.__mul__(other)
    def __truediv__(self, other: Decimal) -> "Money":
        if not isinstance(other, (int, Decimal)):
            return NotImplemented
        return Money(self.amount / other, self.currency)
    def convert(self, rate: Decimal, target_currency: str) -> "Money":
        return Money(self.amount * rate, target_currency)