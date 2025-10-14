import streamlit as st
from datetime import date
from spendings.models import Spending
from spendings.data_handler import load_spendings, add_spending, delete_spending, update_spending
import pandas as pd

def render() -> None:
    """Render the Spendings page."""
    st.title("Spendings")

    # Spending type selection
    is_fixed: bool = st.radio("Select Spending Type", [True, False], format_func=lambda x: "Fixed" if x else "Variable")

    # Load spendings
    df: pd.DataFrame = load_spendings(is_fixed)
    st.subheader("Current Spendings")
    st.dataframe(df)

    # Add spending
    st.subheader("Add New Spending")
    with st.form("add_form"):
        spending_date: date = st.date_input("Date", value=date.today())
        name: str = st.text_input("Name")
        amount: float = st.number_input("Amount", min_value=0.0)
        description: str = st.text_input("Description")
        submitted: bool = st.form_submit_button("Add")
        if submitted:
            new_spending = Spending(spending_date, name, amount, description, is_fixed)
            add_spending(new_spending)
            st.success("Spending added successfully.")
            st.rerun()

    # Update spending
    st.subheader("Update Spending")
    if not df.empty:
        update_index: int = st.number_input("Index to Update", min_value=0, max_value=len(df)-1, step=1)
        with st.form("update_form"):
            spending_date: date = st.date_input("New Date", value=date.today(), key="update_date")
            name: str = st.text_input("New Name", key="update_name")
            amount: float = st.number_input("New Amount", min_value=0.0, key="update_amount")
            description: str = st.text_input("New Description", key="update_description")
            submitted: bool = st.form_submit_button("Update")
            if submitted:
                updated_spending = Spending(spending_date, name, amount, description, is_fixed)
                update_spending(update_index, updated_spending)
                st.success("Spending updated successfully.")
                st.rerun()

    # Delete spending
    st.subheader("Delete Spending")
    if not df.empty:
        delete_index: int = st.number_input("Index to Delete", min_value=0, max_value=len(df)-1, step=1, key="delete_index")
        if st.button("Delete Spending"):
            delete_spending(delete_index, is_fixed)
            st.success("Spending deleted successfully.")
            st.rerun()