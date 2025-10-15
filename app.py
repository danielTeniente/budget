import streamlit as st

# Set page title
st.set_page_config(page_title="Spending Manager", layout="centered")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Spendings", "Earnings", "Analytics", "Spending Analysis", "Exchange Currency Spendings"
])

# Page routing
if page == "Spendings":
    from gui_pages import spendings
    spendings.render()
elif page == "Exchange Currency Spendings":
    from gui_pages import exchange_currency_spendings
    exchange_currency_spendings.render()
elif page == "Spending Analysis":
    from gui_pages import spending_analysis
    spending_analysis.render()

    