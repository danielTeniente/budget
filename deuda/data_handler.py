import pandas as pd
import os
from datetime import date
from dataclasses import dataclass

# Configuración
FIXED_DEBT_FILE = "deuda/fixed_debts.csv"
VARIABLE_DEBT_FILE = "deuda/variable_debts.csv"
ANNUAL_INTEREST_RATE = 0.16
MONTHLY_INTEREST_RATE = ANNUAL_INTEREST_RATE / 12

@dataclass
class Debt:
    name: str
    amount: float
    description: str
    is_fixed: bool
    last_update: date = date.today()

def ensure_files():
    if not os.path.exists("deuda"):
        os.makedirs("deuda")

def load_debts(is_fixed: bool) -> pd.DataFrame:
    ensure_files()
    file_path = FIXED_DEBT_FILE if is_fixed else VARIABLE_DEBT_FILE
    try:
        df = pd.read_csv(file_path)
        df["last_update"] = pd.to_datetime(df["last_update"]).dt.date
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df = pd.DataFrame(columns=["name", "amount", "description", "last_update"])
    return df

def save_debts(df: pd.DataFrame, is_fixed: bool) -> None:
    file_path = FIXED_DEBT_FILE if is_fixed else VARIABLE_DEBT_FILE
    df.to_csv(file_path, index=False)

def add_debt(debt: Debt) -> None:
    df = load_debts(debt.is_fixed)
    new_row = {
        "name": debt.name,
        "amount": debt.amount,
        "description": debt.description,
        "last_update": debt.last_update
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_debts(df, debt.is_fixed)

def update_debt_status(index: int, payment: float, is_fixed: bool) -> None:
    """Resta el pago al monto actual y actualiza la fecha."""
    df = load_debts(is_fixed)
    if index in df.index:
        current_amount = df.at[index, "amount"]
        df.at[index, "amount"] = max(0.0, current_amount - payment)
        df.at[index, "last_update"] = date.today()
        save_debts(df, is_fixed)

def delete_debt(index: int, is_fixed: bool) -> None:
    df = load_debts(is_fixed)
    df = df.drop(index).reset_index(drop=True)
    save_debts(df, is_fixed)

def get_projected_amount(amount: float, is_fixed: bool) -> float:
    """Calcula el valor del próximo mes."""
    if is_fixed:
        return amount
    return amount * (1 + MONTHLY_INTEREST_RATE)