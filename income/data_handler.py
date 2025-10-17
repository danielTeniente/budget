import pandas as pd
from income.models import Income
FIXED_FILE = "data/fixed_income.csv"
VARIABLE_FILE = "data/variable_income.csv"

def load_income(is_fixed: bool) -> pd.DataFrame:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["date", "name", "amount", "description"])
    return df

def add_income(income: Income) -> None:
    df = load_income(income.is_fixed)
    new_row = {
        "date": income.date,
        "name": income.name,
        "amount": income.amount,
        "description": income.description
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    file_path = FIXED_FILE if income.is_fixed else VARIABLE_FILE
    df.to_csv(file_path, index=False)

def update_income(index: int, income: Income) -> None:
    df = load_income(income.is_fixed)
    if 0 <= index < len(df):
        df.loc[index] = [income.date, income.name, income.amount, income.description]
        file_path = FIXED_FILE if income.is_fixed else VARIABLE_FILE
        df.to_csv(file_path, index=False)

def delete_income(index: int, is_fixed: bool) -> None:
    df = load_income(is_fixed)
    if 0 <= index < len(df):
        df = df.drop(index).reset_index(drop=True)
        file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
        df.to_csv(file_path, index=False)