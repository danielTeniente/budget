import streamlit as st
from datetime import date

# Set page title
st.set_page_config(page_title="expenses Manager", layout="centered")

# Sidebar navigation
st.sidebar.title("Navigation")

# Date control (month selector)
selected_date = st.sidebar.date_input(
    "Select Month",
    value=date.today(),
    format="DD/MM/YYYY"
)

# Store in session state for access across pages
st.session_state["selected_date"] = selected_date

page = st.sidebar.radio("Go to", [
    "expenses", "Earnings", "Analytics", "expenses Analysis", "Exchange Currency expenses"
])

# Page routing
if page == "expenses":
    from gui_pages import expenses
    expenses.render()
elif page == "Exchange Currency expenses":
    from gui_pages import exchange_currency_expenses
    exchange_currency_expenses.render()
elif page == "expenses Analysis":
    from gui_pages import expenses_analysis
    expenses_analysis.render()

    