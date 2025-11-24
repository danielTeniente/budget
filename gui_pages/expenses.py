import streamlit as st
from datetime import date, timedelta
from expenses.models import Expenses
from expenses.data_handler import load_expenses, add_expenses, delete_expenses, update_expenses
import pandas as pd

def get_current_month_range():
    """Calcula el primer y último día del mes actual."""
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_day_current_month = (first_day_current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first_day_current_month, last_day_current_month

def render() -> None:
    """Render the expenses page."""
    st.title("Expenses")

    # Selección de tipo
    is_fixed: bool = st.radio("Select Expenses Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Cargar todos los datos
    df: pd.DataFrame = load_expenses(is_fixed)
    
    # Crear una columna con el índice original para poder hacer CRUD correctamente después de filtrar
    if not df.empty:
        df['original_index'] = df.index

    # 1. FILTRADO: Mostrar solo mes anterior (o todos si está vacío)
    st.subheader("Expenses")
    
    if not df.empty:
        # Asegurarse de que la columna fecha sea tipo fecha
        df['date'] = pd.to_datetime(df['date'],format='mixed').dt.date
        
        start_date, end_date = get_current_month_range()
        
        # Filtramos para la vista visual
        filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if filtered_df.empty:
            st.info(f"No expenses found for the previous month ({start_date.strftime('%B %Y')}). Showing all data instead.")
            display_df = df
        else:
            display_df = filtered_df
            
        st.dataframe(display_df.drop(columns=['original_index'], errors='ignore'))
    else:
        st.info("No expenses records found.")
        display_df = pd.DataFrame()

    # 2. AGREGAR: Limpieza automática con clear_on_submit=True
    st.subheader("Add New Expense")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expenses_date: date = st.date_input("Date", value=date.today())
            name: str = st.text_input("Name")
        with col2:
            amount: float = st.number_input("Amount", min_value=0.0)
            description: str = st.text_input("Description")
            
        submitted: bool = st.form_submit_button("Add")
        if submitted:
            new_expenses = Expenses(expenses_date, name, amount, description, is_fixed)
            add_expenses(new_expenses)
            st.success("Expense added successfully!")
            st.rerun()

    # SECCIÓN DE EDICIÓN Y BORRADO
    # Usamos un selectbox para elegir qué editar en lugar de escribir el índice manualmente
    if not display_df.empty:
        st.divider()
        st.subheader("Manage Expenses")
        
        # Crear una lista de opciones basada en el DataFrame filtrado
        # El valor del selectbox será el 'original_index' para que el backend sepa cuál tocar
        options = display_df['original_index'].tolist()
        
        # Función para mostrar texto amigable en el selectbox
        def format_option(idx):
            row = df.loc[idx]
            return f"{row['date']} - {row['name']} (${row['amount']})"

        selected_index = st.selectbox("Select Expense to Update/Delete", options=options, format_func=format_option)
        
        # Obtener los datos actuales de la selección para pre-llenar el formulario
        current_data = df.loc[selected_index]

        # 3. ACTUALIZAR: Pre-llenado de datos y cambio de tipo
        st.write("### Update Selected")
        with st.form("update_form"):
            # Pre-llenamos los campos con current_data
            new_date = st.date_input("Date", value=current_data['date'])
            new_name = st.text_input("Name", value=current_data['name'])
            new_amount = st.number_input("Amount", min_value=0.0, value=float(current_data['amount']))
            new_description = st.text_input("Description", value=current_data['description'])
            
            # Opción para mover de Fijo a Variable (o viceversa)
            target_type_label = "Variable" if is_fixed else "Fixed"
            move_type = st.checkbox(f"Move to {target_type_label} expenses?")
            
            update_submitted = st.form_submit_button("Update Expense")
            
            if update_submitted:
                if move_type:
                    # Alerta: Tu data_handler original `load_expenses(is_fixed)` sugiere que se guardan separados.
                    # Vamos a intentar hacerlo borrando primero y agregando después.
                    delete_expenses(selected_index, is_fixed) # Borrar del actual
                    switched_expense = Expenses(new_date, new_name, new_amount, new_description, not is_fixed)
                    add_expenses(switched_expense) 
                    
                    st.success(f"Expense moved to {target_type_label} and updated!")
                    st.rerun()
                else:
                    # Actualización normal
                    updated_expense = Expenses(new_date, new_name, new_amount, new_description, is_fixed)
                    update_expenses(selected_index, updated_expense)
                    st.success("Expense updated successfully.")
                    st.rerun()

        # 4. BORRAR
        st.write("### Delete Selected")
        if st.button("Delete Expense", type="primary"):
            delete_expenses(selected_index, is_fixed)
            st.success("Expense deleted successfully.")
            st.rerun()