import pandas as pd
from typing import List
from spendings.models import Spending

FIXED_FILE = "data/fixed_spendings.csv"
VARIABLE_FILE = "data/variable_spendings.csv"

def load_spendings(is_fixed: bool) -> pd.DataFrame:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["date", "name", "amount", "description"])
    return df

def save_spendings(df: pd.DataFrame, is_fixed: bool) -> None:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    df.to_csv(file_path, index=False)

def add_spending(spending: Spending) -> None:
    df = load_spendings(spending.is_fixed)
    new_row = {
        "date": spending.date,
        "name": spending.name,
        "amount": spending.amount,
        "description": spending.description
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_spendings(df, spending.is_fixed)

def delete_spending(index: int, is_fixed: bool) -> None:
    df = load_spendings(is_fixed)
    df = df.drop(index).reset_index(drop=True)
    save_spendings(df, is_fixed)

def update_spending(index: int, spending: Spending) -> None:
    df = load_spendings(spending.is_fixed)
    df.loc[index] = {
        "date": spending.date,
        "name": spending.name,
        "amount": spending.amount,
        "description": spending.description
    }
    save_spendings(df, spending.is_fixed)