import pandas as pd
import os
from datetime import date
from dataclasses import dataclass
import uuid

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
    debt_id: str = None

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
        df = pd.DataFrame(columns=["id", "name", "amount", "description", "last_update", "is_current"])
    return df

def save_debts(df: pd.DataFrame, is_fixed: bool) -> None:
    file_path = FIXED_DEBT_FILE if is_fixed else VARIABLE_DEBT_FILE
    df.to_csv(file_path, index=False)

def add_debt(debt: Debt) -> str:
    df = load_debts(debt.is_fixed)
    unique_id = str(uuid.uuid4())[:8]
    
    new_row = {
        "id": unique_id,
        "name": debt.name,
        "amount": debt.amount,
        "description": debt.description,
        "last_update": debt.last_update,
        "is_current": 1
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_debts(df, debt.is_fixed)
    return unique_id

def update_debt_status(debt_id: str, payment: float, is_fixed: bool) -> bool:
    df = load_debts(is_fixed)
    # Buscamos la fila vigente (1) de ese ID
    mask = (df["id"] == debt_id) & (df["is_current"] == 1)
    
    if not df[mask].empty:
        idx = df[mask].index[0]
        # 1. El registro actual pasa a ser histórico
        df.at[idx, "is_current"] = 0
        
        # 2. Creamos la nueva fila vigente con el saldo restado
        new_row = df.loc[idx].copy()
        new_row["amount"] = max(0.0, float(new_row["amount"]) - payment)
        new_row["last_update"] = date.today()
        new_row["is_current"] = 1
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_debts(df, is_fixed)
        return True
    return False

def delete_debt(debt_id: str, is_fixed: bool) -> None:
    df = load_debts(is_fixed)
    # Eliminamos tanto la vigente como el histórico asociado a ese ID
    df = df[df["id"] != debt_id].reset_index(drop=True)
    save_debts(df, is_fixed)

def get_projected_amount(amount: float, is_fixed: bool) -> float:
    return amount if is_fixed else amount * (1 + MONTHLY_INTEREST_RATE)