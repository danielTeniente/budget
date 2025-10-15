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
    ("EUR", "USD"): 1.1,
    ("USD", "EUR"): 0.91,
    ("GBP", "USD"): 1.25,
    ("USD", "GBP"): 0.8,
    ("EUR", "GBP"): 0.87,
    ("GBP", "EUR"): 1.15,
}

def fetch_exchange_rate(from_currency: Currency, to_currency: Currency) -> float:
    """Fetch exchange rate from exchangerate.host or fallback to default."""
    try:
        url = f"https://api.exchangerate.host/latest?base={from_currency}&symbols={to_currency}"
        response = requests.get(url)
        data = response.json()
        return data["rates"][to_currency]
    except Exception:
        return DEFAULT_EXCHANGE_RATES.get((from_currency, to_currency), 1.0)

def convert_currency(amount: float, rate: float) -> float:
    """Convert amount using exchange rate."""
    return round(amount * rate, 2)

def render() -> None:
    """Render the Exchange Currency expenses page."""
    st.title("Exchange Currency expenses")

    # Select currencies
    from_currency: Currency = st.selectbox("expenses Currency", SUPPORTED_CURRENCIES)
    to_currency: Currency = st.selectbox("Budget Currency", SUPPORTED_CURRENCIES)

    # Fetch and allow manual override of exchange rate
    exchange_rate: float = fetch_exchange_rate(from_currency, to_currency)
    manual_rate: float = st.number_input("Exchange Rate", value=exchange_rate, min_value=0.01, format="%.4f")
    st.caption(f"Fetched rate from {from_currency} to {to_currency}: {exchange_rate:.4f}")

    # Input multiple expenses
    st.subheader("Enter expenses")
    num_expenses: int = st.number_input("Number of expenses", min_value=1, max_value=10, step=1)

    expenses: List[Expenses] = []
    total_original: float = 0.0
    total_converted: float = 0.0

    for i in range(num_expenses):
        with st.expander(f"expenses {i+1}"):
            expenses_date: date = st.date_input(f"Date", value=date.today(), key=f"date_{i}")
            name: str = st.text_input("Name", key=f"name_{i}")
            amount: float = st.number_input(f"Amount ({from_currency})", min_value=0.0, key=f"amount_{i}")
            description: str = st.text_input("Description", key=f"description_{i}")
            is_fixed: bool = st.radio("Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable", key=f"type_{i}")

            converted_amount = convert_currency(amount, manual_rate)
            st.info(f"{amount} {from_currency} ≈ {converted_amount} {to_currency}")

            if name and amount > 0:
                expenses.append(Expenses(expenses_date, name, converted_amount, description, is_fixed))
                total_original += amount
                total_converted += converted_amount

    # Show totals and confirmation
    if expenses:
        st.subheader("Summary")
        st.write(f"Total in {from_currency}: **{total_original:.2f}**")
        st.write(f"Total in {to_currency}: **{total_converted:.2f}**")

        confirm: bool = st.checkbox("Confirm and Save expenses")
        if confirm and st.button("Save All"):
            for ex in expenses:
                add_expenses(ex)
            st.success("All expenses saved successfully.")
            st.rerun()