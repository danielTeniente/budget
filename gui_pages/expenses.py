import streamlit as st
from datetime import date, timedelta
from expenses.models import Expenses
from expenses.data_handler import load_expenses, add_expenses, delete_expenses, update_expenses
import pandas as pd

# --- HELPER FUNCTIONS ---

def get_current_month_range():
    """Calcula el primer y último día del mes actual."""
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_day_current_month = (first_day_current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first_day_current_month, last_day_current_month

def get_previous_month_range():
    """Calcula el primer y último día del mes pasado."""
    today = date.today()
    first_day_current = today.replace(day=1)
    last_day_prev = first_day_current - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    return first_day_prev, last_day_prev

def get_variable_suggestions_details(df: pd.DataFrame) -> list[dict]:
    """
    Analiza gastos variables frecuentes y devuelve detalles del último registro encontrado.
    Retorna lista de diccionarios: {'name', 'amount', 'description', 'label'}
    """
    if df.empty:
        return []
    
    # Crear copia y normalizar nombres
    temp_df = df.copy()
    temp_df['clean_name'] = temp_df['name'].astype(str).str.lower().str.strip()
    
    # 1. Identificar frecuentes (> 1 vez)
    counts = temp_df['clean_name'].value_counts()
    frequent_clean_names = counts[counts > 1].index.tolist()
    
    if not frequent_clean_names:
        return []

    # 2. Obtener los detalles del REGISTRO MÁS RECIENTE para cada frecuente
    # Ordenamos por fecha descendente
    temp_df = temp_df.sort_values('date', ascending=False)
    
    suggestions = []
    seen = set()
    
    for _, row in temp_df.iterrows():
        c_name = row['clean_name']
        if c_name in frequent_clean_names and c_name not in seen:
            suggestions.append({
                'label': f"{row['name']} (Last: ${row['amount']})",
                'name': row['name'],
                'amount': row['amount'],
                'description': row['description']
            })
            seen.add(c_name)
            
    return suggestions

# --- MAIN RENDER ---

def render() -> None:
    """Render the expenses page."""
    st.title("Expenses")

    # Inicializar claves del formulario en session_state si no existen
    if "expense_name" not in st.session_state:
        st.session_state["expense_name"] = ""
    if "expense_amount" not in st.session_state:
        st.session_state["expense_amount"] = 0.0
    if "expense_desc" not in st.session_state:
        st.session_state["expense_desc"] = ""
        
    # Variable para controlar la lógica de "pre-llenado"
    # Usamos esto para detectar cambios en el selectbox
    if "last_applied_suggestion_id" not in st.session_state:
        st.session_state["last_applied_suggestion_id"] = None

    # Selección de tipo (Fijo vs Variable)
    is_fixed: bool = st.radio("Select Expenses Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Cargar datos
    df: pd.DataFrame = load_expenses(is_fixed)
    if not df.empty:
        df['original_index'] = df.index
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date


    # ---------------------------------------------------------
    # LISTA VISUAL (Mes Actual)
    # ---------------------------------------------------------
    st.subheader("Current Month Expenses")
    if not df.empty:
        start_date, end_date = get_current_month_range()
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        display_df = filtered_df if not filtered_df.empty else df
        if filtered_df.empty:
            st.caption("Showing all data (Current month is empty).")
            
        st.dataframe(display_df.drop(columns=['original_index'], errors='ignore'))
    else:
        st.info("No records found.")
        display_df = pd.DataFrame()

    st.divider()
    # ---------------------------------------------------------
    # AGREGAR (FORMULARIO)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # SECCIÓN DE SUGERENCIAS
    # ---------------------------------------------------------
    with st.container():
        suggestion_data = None # Almacenará {name, amount, desc} para llenar

        if is_fixed:
            # === LOGICA FIJA (Mes Anterior) ===
            prev_start, prev_end = get_previous_month_range()
            st.info(f"💡 Tip: Select a fixed expense from {prev_start.strftime('%B')} to autofill.")
            
            if not df.empty:
                prev_month_df = df[(df['date'] >= prev_start) & (df['date'] <= prev_end)]
                
                if not prev_month_df.empty:
                    # Crear diccionario: ID -> Row Data
                    # Usamos el índice original como ID único
                    options_map = {}
                    for idx, row in prev_month_df.iterrows():
                        options_map[idx] = row
                    
                    def format_fixed(idx):
                        r = options_map[idx]
                        return f"{r['name']} - ${r['amount']} ({r['description']})"
                    
                    selected_idx = st.selectbox(
                        "Copy from Last Month:", 
                        options=[None] + list(options_map.keys()), 
                        format_func=lambda x: "Select an expense..." if x is None else format_fixed(x),
                        key="sb_fixed_fill"
                    )
                    
                    if selected_idx is not None:
                        row = options_map[selected_idx]
                        suggestion_data = {
                            'id': f"fixed_{selected_idx}", # ID único para controlar cambios
                            'name': row['name'],
                            'amount': float(row['amount']),
                            'description': row['description']
                        }
                else:
                    st.caption("No fixed expenses found in the previous month.")
            else:
                st.caption("No data available.")

        else:
            # === LOGICA VARIABLE (Frecuentes) ===
            st.info("💡 Tip: Select a frequent expense to autofill.")
            if not df.empty:
                suggestions_list = get_variable_suggestions_details(df)
                
                if suggestions_list:
                    # Mapear label -> objeto datos
                    sug_map = {item['label']: item for item in suggestions_list}
                    
                    selected_label = st.selectbox(
                        "Frequent Suggestions:",
                        options=["Select..."] + list(sug_map.keys()),
                        key="sb_var_fill"
                    )
                    
                    if selected_label != "Select...":
                        item = sug_map[selected_label]
                        suggestion_data = {
                            'id': f"var_{selected_label}", # ID único
                            'name': item['name'],
                            'amount': float(item['amount']),
                            'description': item['description']
                        }
                else:
                    st.caption("Add more expenses to see suggestions here.")
            else:
                st.caption("No data available.")

        # === APLICAR SUGERENCIA AL FORMULARIO ===
        # Si hay una sugerencia seleccionada Y es diferente a la última aplicada
        if suggestion_data:
            if st.session_state["last_applied_suggestion_id"] != suggestion_data['id']:
                st.session_state["expense_name"] = suggestion_data['name']
                st.session_state["expense_amount"] = suggestion_data['amount']
                st.session_state["expense_desc"] = suggestion_data['description']
                
                # Marcar como aplicada para no re-escribir si el usuario edita manualmente después
                st.session_state["last_applied_suggestion_id"] = suggestion_data['id']
                # Recargar para mostrar los valores en los inputs
                st.rerun()
    st.subheader("Add New Expense")

    # Formulario manual
    with st.form("add_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            expenses_date = st.date_input("Date", value=date.today())
            # Inputs vinculados al session_state
            name = st.text_input("Name", key="expense_name") 
        with col2:
            amount = st.number_input("Amount", min_value=0.0, key="expense_amount")
            description = st.text_input("Description", key="expense_desc")
            
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            if name and amount > 0:
                new_expenses = Expenses(expenses_date, name, amount, description, is_fixed)
                add_expenses(new_expenses)
                st.success("Expense added successfully!")
                
                # Limpiar todo
                st.session_state["expense_name"] = ""
                st.session_state["expense_amount"] = 0.0
                st.session_state["expense_desc"] = ""
                st.session_state["last_applied_suggestion_id"] = None
                
                st.rerun()
            else:
                st.error("Please enter a name and an amount greater than 0.")

    # ---------------------------------------------------------
    # EDICIÓN Y BORRADO (CRUD)
    # ---------------------------------------------------------
    if not display_df.empty:
        st.divider()
        with st.expander("Manage Existing Expenses"):
            options = display_df['original_index'].tolist()
            
            def format_option(idx):
                row = df.loc[idx]
                return f"{row['date']} - {row['name']} (${row['amount']})"

            selected_index = st.selectbox("Select Expense", options=options, format_func=format_option)
            current_data = df.loc[selected_index]

            st.write("---")
            with st.form("update_form"):
                u_date = st.date_input("Date", value=current_data['date'])
                u_name = st.text_input("Name", value=current_data['name'])
                u_amount = st.number_input("Amount", min_value=0.0, value=float(current_data['amount']))
                u_desc = st.text_input("Description", value=current_data['description'])
                
                target_label = "Variable" if is_fixed else "Fixed"
                move_type = st.checkbox(f"Move to {target_label}?")
                
                col_up, col_del = st.columns([1, 4])
                with col_up:
                    update_submitted = st.form_submit_button("Update")
                
                if update_submitted:
                    if move_type:
                        delete_expenses(selected_index, is_fixed)
                        switched = Expenses(u_date, u_name, u_amount, u_desc, not is_fixed)
                        add_expenses(switched)
                        st.success(f"Moved to {target_label}!")
                    else:
                        updated = Expenses(u_date, u_name, u_amount, u_desc, is_fixed)
                        update_expenses(selected_index, updated)
                        st.success("Updated!")
                    st.rerun()

            st.write("Or delete:")
            if st.button("Delete Selected Expense", type="primary"):
                delete_expenses(selected_index, is_fixed)
                st.success("Deleted!")
                st.rerun()