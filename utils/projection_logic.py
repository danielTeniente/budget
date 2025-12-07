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

    # Normalizar nombres
    if not hist_fixed_exp.empty:
        hist_fixed_exp['name'] = hist_fixed_exp['name'].str.lower()
    
    # Obtener opciones únicas con su monto más reciente
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

def _get_historical_part(data_context):
    """Helper interno para construir la parte histórica común."""
    all_inc = pd.concat([data_context["hist_fixed_inc"], data_context["hist_var_inc"]])
    all_exp = pd.concat([data_context["hist_fixed_exp"], data_context["hist_var_exp"]])
    
    if all_inc.empty and all_exp.empty:
        return [], {}

    dates_hist = pd.concat([all_inc["date"], all_exp["date"]]).dt.to_period("M").unique()
    dates_hist = sorted(dates_hist)
    
    historical_rows = []
    actuals_map = {} 

    for period in dates_hist:
        inc_month = all_inc[all_inc["date"].dt.to_period("M") == period]["amount"].sum()
        exp_month = all_exp[all_exp["date"].dt.to_period("M") == period]["amount"].sum()
        
        month_str = str(period)
        
        actuals_map[month_str] = {
            "income": inc_month,
            "expenses": exp_month
        }

        historical_rows.append({
            "month": month_str,
            "total_income": inc_month,
            "total_expenses": exp_month,
            "balance": None, 
            "type": "Histórico"
        })
    return historical_rows, actuals_map

def get_projections(
    num_months: int,
    selected_fixed_inc_names: list,
    selected_fixed_exp_names: list,
    var_inc_method: str,
    var_exp_method: str,
    data_context: dict
) -> tuple[pd.DataFrame, dict]:
    """Proyección Simple (Misma configuración para todos los meses)"""
    
    unique_fixed_inc = data_context["unique_fixed_inc_options"]
    unique_fixed_exp = data_context["unique_fixed_exp_options"]
    hist_var_inc = data_context["hist_var_inc"]
    hist_var_exp = data_context["hist_var_exp"]

    # --- 1. Calcular Targets ---
    projected_fixed_inc_amount = unique_fixed_inc[unique_fixed_inc["name"].isin(selected_fixed_inc_names)]["amount"].sum()
    projected_fixed_exp_amount = unique_fixed_exp[unique_fixed_exp["name"].isin(selected_fixed_exp_names)]["amount"].sum()

    projected_var_inc_amount = calculate_variable_amount(hist_var_inc, var_inc_method)
    projected_var_exp_amount = calculate_variable_amount(hist_var_exp, var_exp_method)

    target_income = projected_fixed_inc_amount + projected_var_inc_amount
    target_expenses = projected_fixed_exp_amount + projected_var_exp_amount

    summary = {
        "fixed_income": projected_fixed_inc_amount,
        "variable_income": projected_var_inc_amount,
        "fixed_expenses": projected_fixed_exp_amount,
        "variable_expenses": projected_var_exp_amount,
        "total_income": target_income,
        "total_expenses": target_expenses,
        "var_inc_method": var_inc_method,
        "var_exp_method": var_exp_method
    }

    # --- 2. Historial ---
    historical_rows, actuals_map = _get_historical_part(data_context)
    
    # --- 3. Proyección ---
    current_balance = (
        data_context["raw_fixed_inc"]["amount"].sum() + data_context["raw_var_inc"]["amount"].sum()
    ) - (
        data_context["raw_fixed_exp"]["amount"].sum() + data_context["raw_var_exp"]["amount"].sum()
    )

    current_month_date = datetime.today().replace(day=1)
    current_month_str = current_month_date.strftime("%Y-%m")
    
    projection_rows = []
    running_balance = current_balance

    for i in range(num_months):
        month_date = current_month_date + pd.DateOffset(months=i)
        loop_month_str = month_date.strftime("%Y-%m")
        
        proj_inc_for_row = target_income
        proj_exp_for_row = target_expenses

        # Lógica de mes actual (Descuento de lo ya ejecutado)
        if loop_month_str == current_month_str:
            actual_data = actuals_map.get(loop_month_str, {"income": 0, "expenses": 0})
            remaining_inc = max(0, target_income - actual_data["income"])
            remaining_exp = max(0, target_expenses - actual_data["expenses"])
            proj_inc_for_row = remaining_inc
            proj_exp_for_row = remaining_exp

        running_balance += (proj_inc_for_row - proj_exp_for_row)

        projection_rows.append({
            "month": loop_month_str,
            "total_income": proj_inc_for_row,
            "total_expenses": proj_exp_for_row,
            "balance": running_balance,
            "type": "Proyectado"
        })

    final_df = pd.concat([pd.DataFrame(historical_rows), pd.DataFrame(projection_rows)], ignore_index=True)
    return final_df, summary

def get_detailed_projections(
    num_months: int,
    monthly_selections: dict, # {0: {'inc': [], 'exp': []}, 1: ...}
    var_inc_method: str,
    var_exp_method: str,
    data_context: dict
) -> pd.DataFrame:
    """
    Proyección Detallada (Configuración específica mes a mes).
    No devuelve 'summary' global porque varía cada mes.
    """
    unique_fixed_inc = data_context["unique_fixed_inc_options"]
    unique_fixed_exp = data_context["unique_fixed_exp_options"]
    hist_var_inc = data_context["hist_var_inc"]
    hist_var_exp = data_context["hist_var_exp"]

    # Calcular variables (se asume constante el método, aunque se suma al total del mes)
    projected_var_inc_amount = calculate_variable_amount(hist_var_inc, var_inc_method)
    projected_var_exp_amount = calculate_variable_amount(hist_var_exp, var_exp_method)

    # --- Historial ---
    historical_rows, actuals_map = _get_historical_part(data_context)

    # --- Proyección ---
    current_balance = (
        data_context["raw_fixed_inc"]["amount"].sum() + data_context["raw_var_inc"]["amount"].sum()
    ) - (
        data_context["raw_fixed_exp"]["amount"].sum() + data_context["raw_var_exp"]["amount"].sum()
    )

    current_month_date = datetime.today().replace(day=1)
    current_month_str = current_month_date.strftime("%Y-%m")
    
    projection_rows = []
    running_balance = current_balance

    for i in range(num_months):
        month_date = current_month_date + pd.DateOffset(months=i)
        loop_month_str = month_date.strftime("%Y-%m")
        
        # Recuperar selección específica de este mes (i)
        month_config = monthly_selections.get(i, {'inc': [], 'exp': []})
        
        # Calcular totales target para ESTE mes
        month_fixed_inc = unique_fixed_inc[unique_fixed_inc["name"].isin(month_config['inc'])]["amount"].sum()
        month_fixed_exp = unique_fixed_exp[unique_fixed_exp["name"].isin(month_config['exp'])]["amount"].sum()
        
        target_income = month_fixed_inc + projected_var_inc_amount
        target_expenses = month_fixed_exp + projected_var_exp_amount

        proj_inc_for_row = target_income
        proj_exp_for_row = target_expenses

        # Lógica de mes actual
        if loop_month_str == current_month_str:
            actual_data = actuals_map.get(loop_month_str, {"income": 0, "expenses": 0})
            remaining_inc = max(0, target_income - actual_data["income"])
            remaining_exp = max(0, target_expenses - actual_data["expenses"])
            proj_inc_for_row = remaining_inc
            proj_exp_for_row = remaining_exp

        running_balance += (proj_inc_for_row - proj_exp_for_row)

        projection_rows.append({
            "month": loop_month_str,
            "total_income": proj_inc_for_row, # Aquí guardamos el neto proyectado/restante
            "total_expenses": proj_exp_for_row,
            "balance": running_balance,
            "type": "Proyectado"
        })

    final_df = pd.concat([pd.DataFrame(historical_rows), pd.DataFrame(projection_rows)], ignore_index=True)
    return final_df