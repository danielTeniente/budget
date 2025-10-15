import streamlit as st
from datetime import date
from expenses.models import Expenses
from expenses.data_handler import load_expenses, add_expenses, delete_expenses, update_expenses
import pandas as pd

def render() -> None:
    """Render the expenses page."""
    st.title("expenses")

    # expenses type selection
    is_fixed: bool = st.radio("Select expenses Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Load expenses
    df: pd.DataFrame = load_expenses(is_fixed)
    st.subheader("Current expenses")
    st.dataframe(df)

    # Add expenses
    st.subheader("Add New expenses")
    with st.form("add_form"):
        expenses_date: date = st.date_input("Date", value=date.today())
        name: str = st.text_input("Name")
        amount: float = st.number_input("Amount", min_value=0.0)
        description: str = st.text_input("Description")
        submitted: bool = st.form_submit_button("Add")
        if submitted:
            new_expenses = Expenses(expenses_date, name, amount, description, is_fixed)
            add_expenses(new_expenses)
            st.success("expenses added successfully.")
            st.rerun()

    # Update expenses
    st.subheader("Update expenses")
    if not df.empty:
        update_index: int = st.number_input("Index to Update", min_value=0, max_value=len(df)-1, step=1)
        with st.form("update_form"):
            expenses_date: date = st.date_input("New Date", value=date.today(), key="update_date")
            name: str = st.text_input("New Name", key="update_name")
            amount: float = st.number_input("New Amount", min_value=0.0, key="update_amount")
            description: str = st.text_input("New Description", key="update_description")
            submitted: bool = st.form_submit_button("Update")
            if submitted:
                updated_expenses = Expenses(expenses_date, name, amount, description, is_fixed)
                update_expenses(update_index, updated_expenses)
                st.success("expenses updated successfully.")
                st.rerun()

    # Delete expenses
    st.subheader("Delete expenses")
    if not df.empty:
        delete_index: int = st.number_input("Index to Delete", min_value=0, max_value=len(df)-1, step=1, key="delete_index")
        if st.button("Delete expenses"):
            delete_expenses(delete_index, is_fixed)
            st.success("expenses deleted successfully.")
            st.rerun()