import streamlit as st
from datetime import date
from income.models import Income
from income.data_handler import load_income, add_income, delete_income, update_income
import pandas as pd

def render() -> None:
    """Render the income page."""
    st.title("Income")

    # Income type selection
    is_fixed: bool = st.radio("Select Income Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Load income
    df: pd.DataFrame = load_income(is_fixed)
    st.subheader("Current Income")
    st.dataframe(df)

    # Add income
    st.subheader("Add New Income")
    with st.form("add_form"):
        income_date: date = st.date_input("Date", value=date.today())
        name: str = st.text_input("Name")
        amount: float = st.number_input("Amount", min_value=0.0)
        description: str = st.text_input("Description")
        submitted: bool = st.form_submit_button("Add")
        if submitted:
            new_income = Income(income_date, name, amount, description, is_fixed)
            add_income(new_income)
            st.success("Income added successfully.")
            st.rerun()

    # Update income
    st.subheader("Update Income")
    if not df.empty:
        update_index: int = st.number_input("Index to Update", min_value=0, max_value=len(df)-1, step=1)
        with st.form("update_form"):
            income_date: date = st.date_input("New Date", value=date.today(), key="update_date")
            name: str = st.text_input("New Name", key="update_name")
            amount: float = st.number_input("New Amount", min_value=0.0, key="update_amount")
            description: str = st.text_input("New Description", key="update_description")
            submitted: bool = st.form_submit_button("Update")
            if submitted:
                updated_income = Income(income_date, name, amount, description, is_fixed)
                update_income(update_index, updated_income)
                st.success("Income updated successfully.")
                st.rerun()

    # Delete income
    st.subheader("Delete Income")
    if not df.empty:
        delete_index: int = st.number_input("Index to Delete", min_value=0, max_value=len(df)-1, step=1, key="delete_index")
        if st.button("Delete Income"):
            delete_income(delete_index, is_fixed)
            st.success("Income deleted successfully.")
            st.rerun()