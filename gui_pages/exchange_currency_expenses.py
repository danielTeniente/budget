import streamlit as st
from datetime import date
from typing import List, Literal
import requests

from expenses.models import Expenses
from expenses.data_handler import add_expenses

# Define supported currencies
Currency = Literal["USD", "EUR", "GBP"]
SUPPORTED_CURRENCIES: List[Currency] = ["USD", "EUR", "GBP"]

# Default fallback exchange rates
DEFAULT_EXCHANGE_RATES = {
    ("EUR", "USD"): 1.17,
    ("USD", "EUR"): 0.91,
    ("GBP", "USD"): 1.25,
    ("USD", "GBP"): 0.8,
    ("EUR", "GBP"): 0.87,
    ("GBP", "EUR"): 1.15,
}

def fetch_exchange_rate(from_currency: Currency, to_currency: Currency) -> float:
    """Fetch exchange rate from exchangerate.host or fallback to default."""
    # Aquí podrías añadir una llamada real a API si lo deseas
    return DEFAULT_EXCHANGE_RATES.get((from_currency, to_currency), 1.0)

def convert_currency(amount: float, rate: float) -> float:
    """Convert amount using exchange rate."""
    return round(amount * rate, 2)

def render() -> None:
    """Render the Exchange Currency expenses page."""
    st.title("Exchange Currency Expenses")

    # 1. MENSAJE DE ÉXITO PERSISTENTE
    # Verificamos si venimos de un guardado exitoso
    if st.session_state.get("saved_success"):
        st.success("All expenses saved successfully and form cleared.")
        # Reiniciamos la bandera para que el mensaje no salga siempre
        st.session_state["saved_success"] = False

    # Select currencies
    col1, col2 = st.columns(2)
    with col1:
        from_currency: Currency = st.selectbox("Expenses Currency", SUPPORTED_CURRENCIES)
    with col2:
        to_currency: Currency = st.selectbox("Budget Currency", SUPPORTED_CURRENCIES)

    # Fetch and allow manual override of exchange rate
    exchange_rate: float = fetch_exchange_rate(from_currency, to_currency)
    manual_rate: float = st.number_input("Exchange Rate", value=exchange_rate, min_value=0.01, format="%.4f")
    st.caption(f"Fetched rate from {from_currency} to {to_currency}: {exchange_rate:.4f}")

    st.divider()

    # Input multiple expenses
    st.subheader("Enter Expenses")
    # Usamos una key para el número de gastos para poder resetearlo si fuera necesario, aunque es opcional
    num_expenses: int = st.number_input("Number of expenses items", min_value=1, max_value=20, step=1)

    expenses: List[Expenses] = []
    total_original: float = 0.0
    total_converted: float = 0.0

    # Generación dinámica de formulario
    for i in range(num_expenses):
        with st.expander(f"Expense Item #{i+1}", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                # Asignamos keys únicos basados en el índice 'i'
                expenses_date: date = st.date_input(f"Date", value=date.today(), key=f"date_{i}")
                name: str = st.text_input("Name", key=f"name_{i}")
            with c2:
                amount: float = st.number_input(f"Amount ({from_currency})", min_value=0.0, key=f"amount_{i}")
                description: str = st.text_input("Description", key=f"description_{i}")
            
            is_fixed: bool = st.radio("Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable", key=f"type_{i}", horizontal=True)

            converted_amount = convert_currency(amount, manual_rate)
            if amount > 0:
                st.info(f"💱 {amount} {from_currency} = **{converted_amount} {to_currency}**")

            # Solo agregamos a la lista de guardado si tiene nombre y monto
            if name and amount > 0:
                expenses.append(Expenses(expenses_date, name, converted_amount, description, is_fixed))
                total_original += amount
                total_converted += converted_amount

    # Show totals and confirmation
    st.divider()
    if expenses:
        st.subheader("Summary")
        st.write(f"Total in {from_currency}: **{total_original:.2f}**")
        st.write(f"Total in {to_currency}: **{total_converted:.2f}**")

        confirm: bool = st.checkbox("Confirm and Save Expenses")
        
        if confirm and st.button("Save All", type="primary"):
            try:
                # Guardar datos
                for ex in expenses:
                    add_expenses(ex)
                
                # LIMPIEZA DE CAMPOS (Reset form)
                # Iteramos sobre los índices y borramos las keys del session_state
                for i in range(num_expenses):
                    keys_to_clear = [
                        f"date_{i}", 
                        f"name_{i}", 
                        f"amount_{i}", 
                        f"description_{i}", 
                        f"type_{i}"
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                
                # Activamos la bandera de éxito y recargamos la página
                st.session_state["saved_success"] = True
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred while saving: {e}")
    elif num_expenses > 0:
        st.caption("Fill in the fields above (Name and Amount required) to see the summary.")