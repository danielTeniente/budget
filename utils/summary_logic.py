import pandas as pd
from expenses.data_handler import load_expenses
from income.data_handler import load_income

def load_total_income() -> pd.DataFrame:
    """Load and combine fixed and variable income data."""
    fixed_income_df = load_income(is_fixed=True)
    variable_income_df = load_income(is_fixed=False)
    total_income_df = pd.concat([fixed_income_df, variable_income_df], ignore_index=True)
    total_income_df["date"] = pd.to_datetime(total_income_df["date"], format='mixed')
    return total_income_df

def load_total_expenses() -> pd.DataFrame:
    """Load and combine fixed and variable expenses data."""
    fixed_expenses_df = load_expenses(is_fixed=True)
    variable_expenses_df = load_expenses(is_fixed=False)
    total_expenses_df = pd.concat([fixed_expenses_df, variable_expenses_df], ignore_index=True)
    total_expenses_df["date"] = pd.to_datetime(total_expenses_df["date"], format='mixed')
    return total_expenses_df

def aggregate_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily totals from a given dataframe."""
    return df.groupby("date")["amount"].sum().reset_index()

def prepare_timeline_data(income_df: pd.DataFrame, expenses_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare combined timeline data with income as positive and expenses as negative."""
    income_timeline = aggregate_daily_totals(income_df)
    income_timeline["type"] = "Income"

    expenses_timeline = aggregate_daily_totals(expenses_df)
    expenses_timeline["amount"] *= -1
    expenses_timeline["type"] = "Expenses"

    combined_df = pd.concat([income_timeline, expenses_timeline], ignore_index=True)
    combined_df = combined_df.sort_values("date")
    combined_df["cumulative_amount"] = combined_df["amount"].cumsum()

    # Final timeline showing how money changes over time
    timeline_df = combined_df[["date", "cumulative_amount"]].copy()
    timeline_df["type"] = "Balance"

    return timeline_df

def calculate_net_total(income_df: pd.DataFrame, expenses_df: pd.DataFrame) -> float:
    """Calculate net total balance from income and expenses."""
    total_income = income_df["amount"].sum()
    total_expenses = expenses_df["amount"].sum()
    return total_income - total_expenses