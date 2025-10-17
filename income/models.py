from datetime import date

class Income:
    def __init__(self, date: date, name: str, amount: float, description: str, is_fixed: bool):
        self.date = date
        self.name = name
        self.amount = amount
        self.description = description
        self.is_fixed = is_fixed
