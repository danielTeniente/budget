import pandas as pd
from datetime import datetime
from expenses.data_handler import load_expenses
from income.data_handler import load_income

def get_last_n_months_data(df: pd.DataFrame, n_months: int = 3) -> pd.DataFrame:
    """Filter data for the last n months relative to the current date."""
    if df.empty:
        return df
    
    df["date"] = pd.to_datetime(df["date"], format='mixed')
    today = datetime.today()
    # Fecha de corte: primer día del mes, n meses atrás
    start_date = (today - pd.DateOffset(months=n_months)).replace(day=1)
    
    mask = df["date"] >= start_date
    return df.loc[mask].copy()

def prepare_projection_data():
    """Loads data and prepares lists for the UI selection."""
    fixed_inc = load_income(is_fixed=True)
    var_inc = load_income(is_fixed=False)
    fixed_exp = load_expenses(is_fixed=True)
    var_exp = load_expenses(is_fixed=False)

    hist_fixed_inc = get_last_n_months_data(fixed_inc, 3)
    hist_var_inc = get_last_n_months_data(var_inc, 3)
    hist_fixed_exp = get_last_n_months_data(fixed_exp, 3)
    hist_var_exp = get_last_n_months_data(var_exp, 3)

    hist_fixed_exp['name'] = hist_fixed_exp['name'].str.lower()
    hist_fixed_exp['name'] = hist_fixed_exp['name'].str.lower()

    unique_fixed_inc = hist_fixed_inc.sort_values("date", ascending=False).drop_duplicates(subset=["name"])
    unique_fixed_exp = hist_fixed_exp.sort_values("date", ascending=False).drop_duplicates(subset=["name"])

    return {
        "hist_fixed_inc": hist_fixed_inc,
        "hist_var_inc": hist_var_inc,
        "hist_fixed_exp": hist_fixed_exp,
        "hist_var_exp": hist_var_exp,
        "unique_fixed_inc_options": unique_fixed_inc,
        "unique_fixed_exp_options": unique_fixed_exp,
        "raw_fixed_inc": fixed_inc,
        "raw_var_inc": var_inc,
        "raw_fixed_exp": fixed_exp,
        "raw_var_exp": var_exp
    }

def calculate_variable_amount(df: pd.DataFrame, method: str) -> float:
    """Calculates variable amount based on method."""
    if df.empty or method == "Ninguno":
        return 0.0
    
    df["month_period"] = df["date"].dt.to_period("M")
    monthly_totals = df.groupby("month_period")["amount"].sum()
    
    if method == "Promedio":
        return monthly_totals.mean()
    elif method == "Máximo":
        return monthly_totals.max()
    elif method == "Mínimo":
        return monthly_totals.min()
    return 0.0

def get_projections(
    num_months: int,
    selected_fixed_inc_names: list,
    selected_fixed_exp_names: list,
    var_inc_method: str,
    var_exp_method: str,
    data_context: dict
):
    """
    Returns:
        tuple: (DataFrame con proyecciones, dict con resumen de montos base)
    """
    unique_fixed_inc = data_context["unique_fixed_inc_options"]
    unique_fixed_exp = data_context["unique_fixed_exp_options"]
    hist_var_inc = data_context["hist_var_inc"]
    hist_var_exp = data_context["hist_var_exp"]

    # --- 1. Calcular valores base para proyección ---
    projected_fixed_inc_amount = unique_fixed_inc[unique_fixed_inc["name"].isin(selected_fixed_inc_names)]["amount"].sum()
    projected_fixed_exp_amount = unique_fixed_exp[unique_fixed_exp["name"].isin(selected_fixed_exp_names)]["amount"].sum()

    projected_var_inc_amount = calculate_variable_amount(hist_var_inc, var_inc_method)
    projected_var_exp_amount = calculate_variable_amount(hist_var_exp, var_exp_method)

    total_projected_income = projected_fixed_inc_amount + projected_var_inc_amount
    total_projected_expenses = projected_fixed_exp_amount + projected_var_exp_amount

    # Guardar resumen para explicar al usuario de dónde salen los números
    summary = {
        "fixed_income": projected_fixed_inc_amount,
        "variable_income": projected_var_inc_amount,
        "fixed_expenses": projected_fixed_exp_amount,
        "variable_expenses": projected_var_exp_amount,
        "total_income": total_projected_income,
        "total_expenses": total_projected_expenses,
        "var_inc_method": var_inc_method,
        "var_exp_method": var_exp_method
    }

    # --- 2. Construir Historial ---
    all_inc = pd.concat([data_context["hist_fixed_inc"], data_context["hist_var_inc"]])
    all_exp = pd.concat([data_context["hist_fixed_exp"], data_context["hist_var_exp"]])
    
    dates_hist = pd.concat([all_inc["date"], all_exp["date"]]).dt.to_period("M").unique()
    dates_hist = sorted(dates_hist)
    
    historical_rows = []
    
    # Calcular balance actual real para iniciar la proyección
    current_balance = (
        data_context["raw_fixed_inc"]["amount"].sum() + data_context["raw_var_inc"]["amount"].sum()
    ) - (
        data_context["raw_fixed_exp"]["amount"].sum() + data_context["raw_var_exp"]["amount"].sum()
    )

    for period in dates_hist:
        inc_month = all_inc[all_inc["date"].dt.to_period("M") == period]["amount"].sum()
        exp_month = all_exp[all_exp["date"].dt.to_period("M") == period]["amount"].sum()
        
        historical_rows.append({
            "month": str(period),
            "total_income": inc_month,
            "total_expenses": exp_month,
            "balance": None, 
            "type": "Histórico"
        })
        
    # --- 3. Construir Proyección ---
    current_month_date = datetime.today().replace(day=1)
    
    projection_rows = []
    running_balance = current_balance

    for i in range(num_months):
        month_date = current_month_date + pd.DateOffset(months=i)
        running_balance += (total_projected_income - total_projected_expenses)

        projection_rows.append({
            "month": month_date.strftime("%Y-%m"),
            "total_income": total_projected_income,
            "total_expenses": total_projected_expenses,
            "balance": running_balance,
            "type": "Proyectado"
        })

    final_df = pd.concat([pd.DataFrame(historical_rows), pd.DataFrame(projection_rows)], ignore_index=True)
    
    return final_df, summary