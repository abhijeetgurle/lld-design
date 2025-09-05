class Money:
    def __init__(self, amount: float, currency: str = "INR"):
        if amount < 0:
            raise ValueError("Money amount cannot be negative")
        self.amount = round(amount, 2)
        self.currency = currency.upper()

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currency doesn't match")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)

    def __str__(self):
        return f"Money({self.amount}, {self.currency})"

    def __eq__(self, other: 'Money') -> bool:
        return self.amount == other.amount and self.currency == other.currency
