from dataclasses import dataclass
from datetime import date

@dataclass
class Spending:
    date: date
    name: str
    amount: float
    description: str
    is_fixed: bool