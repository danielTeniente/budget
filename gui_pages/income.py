import streamlit as st
from datetime import date, timedelta
from income.models import Income
from income.data_handler import load_income, add_income, delete_income, update_income
import pandas as pd

def get_current_month_range():
    """Calcula el primer y último día del mes actual."""
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_day_current_month = (first_day_current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first_day_current_month, last_day_current_month

def render() -> None:
    """Render the income page."""
    st.title("Income")

    # Selección de tipo
    is_fixed: bool = st.radio("Select Income Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Cargar datos
    df: pd.DataFrame = load_income(is_fixed)

    # Guardar índice original
    if not df.empty:
        df['original_index'] = df.index

    # 1. FILTRADO: Mostrar solo mes anterior
    st.subheader("Income")
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'], format='mixed').dt.date
        start_date, end_date = get_current_month_range()
        
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if filtered_df.empty:
            st.info(f"No income found for the previous month ({start_date.strftime('%B %Y')}). Showing all data instead.")
            display_df = df
        else:
            display_df = filtered_df
            
        st.dataframe(display_df.drop(columns=['original_index'], errors='ignore'))
    else:
        st.info("No income records found.")
        display_df = pd.DataFrame()

    # 2. AGREGAR: Limpieza automática
    st.subheader("Add New Income")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            income_date: date = st.date_input("Date", value=date.today())
            name: str = st.text_input("Name")
        with col2:
            amount: float = st.number_input("Amount", min_value=0.0)
            description: str = st.text_input("Description")
            
        submitted: bool = st.form_submit_button("Add")
        if submitted:
            new_income = Income(income_date, name, amount, description, is_fixed)
            add_income(new_income)
            st.success("Income added successfully.")
            st.rerun()

    # SECCIÓN DE EDICIÓN Y BORRADO
    if not display_df.empty:
        st.divider()
        st.subheader("Manage Income")
        
        options = display_df['original_index'].tolist()
        
        def format_option(idx):
            row = df.loc[idx]
            return f"{row['date']} - {row['name']} (${row['amount']})"

        selected_index = st.selectbox("Select Income to Update/Delete", options=options, format_func=format_option)
        
        # Datos actuales para pre-llenar
        current_data = df.loc[selected_index]

        # 3. ACTUALIZAR: Pre-llenado y cambio de tipo
        st.write("### Update Selected")
        with st.form("update_form"):
            new_date = st.date_input("Date", value=current_data['date'])
            new_name = st.text_input("Name", value=current_data['name'])
            new_amount = st.number_input("Amount", min_value=0.0, value=float(current_data['amount']))
            new_description = st.text_input("Description", value=current_data['description'])
            
            target_type_label = "Variable" if is_fixed else "Fixed"
            move_type = st.checkbox(f"Move to {target_type_label} Income?")
            
            submitted: bool = st.form_submit_button("Update")
            
            if submitted:
                if move_type:
                    # Lógica de movimiento
                    delete_income(selected_index, is_fixed)
                    
                    switched_income = Income(new_date, new_name, new_amount, new_description, not is_fixed)
                    add_income(switched_income)
                    
                    st.success(f"Income moved to {target_type_label} and updated.")
                    st.rerun()
                else:
                    updated_income = Income(new_date, new_name, new_amount, new_description, is_fixed)
                    update_income(selected_index, updated_income)
                    st.success("Income updated successfully.")
                    st.rerun()

    # 4. BORRAR
        st.write("### Delete Selected")
        if st.button("Delete Income", type="primary"):
            delete_income(selected_index, is_fixed)
            st.success("Income deleted successfully.")
            st.rerun()