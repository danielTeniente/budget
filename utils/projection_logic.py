import pandas as pd
from datetime import datetime
from expenses.data_handler import load_expenses
from income.data_handler import load_income

def get_current_month_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter data for the current month."""
    df["date"] = pd.to_datetime(df["date"], format='mixed')
    current_month_period = pd.Period(datetime.today(), freq="M")
    return df[df["date"].dt.to_period("M") == current_month_period]


def get_projections(num_months: int) -> pd.DataFrame:
    # Load data
    fixed_income = load_income(is_fixed=True)
    variable_income = load_income(is_fixed=False)
    fixed_expenses = load_expenses(is_fixed=True)
    variable_expenses = load_expenses(is_fixed=False)

    # Initial balance from all available data
    balance = (
        fixed_income["amount"].sum() if not fixed_income.empty else 0
    ) + (
        variable_income["amount"].sum() if not variable_income.empty else 0
    ) - (
        fixed_expenses["amount"].sum() if not fixed_expenses.empty else 0
    ) - (
        variable_expenses["amount"].sum() if not variable_expenses.empty else 0
    )

    # Get current month's data
    current_fixed_income = get_current_month_data(fixed_income)
    current_variable_income = get_current_month_data(variable_income)
    current_fixed_expenses = get_current_month_data(fixed_expenses)
    current_variable_expenses = get_current_month_data(variable_expenses)

    # Monthly values (default to 0 if no data)
    fixed_income_total = current_fixed_income["amount"].sum() if not current_fixed_income.empty else 0
    variable_income_mean = current_variable_income["amount"].mean() if not current_variable_income.empty else 0
    fixed_expenses_total = current_fixed_expenses["amount"].sum() if not current_fixed_expenses.empty else 0
    variable_expenses_mean = current_variable_expenses["amount"].mean() if not current_variable_expenses.empty else 0

    # Start from current month
    current_month = datetime.today().replace(day=1)

    projections = []
    for i in range(num_months):
        month = current_month + pd.DateOffset(months=i)
        total_income = fixed_income_total + variable_income_mean
        total_expenses = fixed_expenses_total + variable_expenses_mean
        balance += total_income - total_expenses

        projections.append({
            "month": month.strftime("%Y-%m"),
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance
        })

    return pd.DataFrame(projections)
