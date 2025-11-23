import pandas as pd
from income.models import Income
from datetime import date

FIXED_FILE = "data/fixed_income.csv"
VARIABLE_FILE = "data/variable_income.csv"

def load_income(is_fixed: bool) -> pd.DataFrame:
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["date", "name", "amount", "description"])
    return df


def load_income_by_month(is_fixed: bool, date_filter: date) -> pd.DataFrame:
    """
    Carga el archivo de ingresos (fijos o variables) y devuelve
    un DataFrame filtrado por el mes y año de `date_filter`.

    Args:
        is_fixed (bool): True para ingresos fijos, False para variables.
        date_filter (date): Fecha cuya combinación mes/año se usará para filtrar.

    Returns:
        pd.DataFrame: DataFrame con columnas ["date", "name", "amount", "description"]
                      filtrado por el mes y año.
    """
    file_path = FIXED_FILE if is_fixed else VARIABLE_FILE
    try:
        df = pd.read_csv(file_path, parse_dates=["date"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "name", "amount", "description"])

    # Asegurar parseo robusto de la columna de fecha (format="mixed" maneja formatos variados)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Opcional: eliminar filas con fechas no parseables
    df = df.dropna(subset=["date"])

    # Filtrar por mes y año
    filtered_df = df[df["date"].dt.month == date_filter.month]
    filtered_df = filtered_df[filtered_df["date"].dt.year == date_filter.year]

    return filtered_df


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