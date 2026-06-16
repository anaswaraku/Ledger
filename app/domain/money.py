from dataclasses import dataclass
from decimal import Decimal 

class CurrencyMismatchError(ValueError):
    def __init__(self, cur1:str,cur2:str):
        super().__init__(f"Cannot operate across currencies without conversion: {cur1} vs {cur2}")
        self.cur1 = cur1
        self.cur2 = cur2

class UnbalancedTransactionError(ValueError):
    pass

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