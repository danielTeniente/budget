import pandas as pd
from datetime import date, datetime
from expenses.models import Expenses

FIXED_FILE = "data/fixed_expenses.csv"
VARIABLE_FILE = "data/variable_expenses.csv"

def load_expenses(is_fixed: bool) -> pd.DataFrame:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["date", "name", "amount", "description"])
    return df


def load_expenses_by_month(is_fixed: bool, date_filter: date) -> pd.DataFrame:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "name", "amount", "description"])
    
    df["date"] = pd.to_datetime(df["date"], format="mixed")

    # Filter by month and year
    filtered_df = df[df["date"].dt.month == date_filter.month]
    filtered_df = filtered_df[filtered_df["date"].dt.year == date_filter.year]
    
    return filtered_df

def save_expenses(df: pd.DataFrame, is_fixed: bool) -> None:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    df.to_csv(file_path, index=False)

def add_expenses(expenses: Expenses) -> None:
    df = load_expenses(expenses.is_fixed)
    new_row = {
        "date": expenses.date,
        "name": expenses.name,
        "amount": expenses.amount,
        "description": expenses.description
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_expenses(df, expenses.is_fixed)

def delete_expenses(index: int, is_fixed: bool) -> None:
    df = load_expenses(is_fixed)
    df = df.drop(index).reset_index(drop=True)
    save_expenses(df, is_fixed)

def update_expenses(index: int, expenses: Expenses) -> None:
    df = load_expenses(expenses.is_fixed)
    df.loc[index] = {
        "date": expenses.date,
        "name": expenses.name,
        "amount": expenses.amount,
        "description": expenses.description
    }
    save_expenses(df, expenses.is_fixed)