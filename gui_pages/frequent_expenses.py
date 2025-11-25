import streamlit as st
import plotly.express as px
import pandas as pd
import calendar
from datetime import datetime
from utils.summary_logic import load_total_expenses
# Importamos nuestra nueva lógica separada
from utils.analysis_logic import (
    get_available_years,
    filter_data_by_year,
    get_monthly_frequent_items,
    get_yearly_top_expenses
)

def render() -> None:
    """Render the detailed expense analysis page (Frequency and Top Expenses)."""

    st.title("Expense Analysis")
    st.markdown("Analyze your spending habits: **Frequency** vs **Magnitude**.")

    # 1. Load Data
    expenses_df = load_total_expenses()
    
    if expenses_df.empty:
        st.warning("No expense data found. Please add expenses to view analysis.")
        return

    # --- GLOBAL FILTERS ---
    col1, col2 = st.columns(2)
    
    # Year Selector
    with col1:
        available_years = get_available_years(expenses_df)
        selected_year = st.selectbox("Select Year", available_years)

    # Month Selector (Logic for default month selection)
    with col2:
        months_list = list(calendar.month_name)[1:] # ['January', 'February', ...]
        current_month_index = datetime.now().month - 1
        
        # If selected year is current year, default to current month, else January
        default_index = current_month_index if selected_year == datetime.now().year else 0
        
        selected_month_name = st.selectbox("Select Month", months_list, index=default_index)
        selected_month_num = months_list.index(selected_month_name) + 1

    # Filter main dataframe by year first (optimization)
    df_year = filter_data_by_year(expenses_df, selected_year)

    st.divider()

    # ==============================================================================
    # PART 1: FREQUENT EXPENSES (Monthly Calendar View)
    # ==============================================================================
    st.header(f"1. Frequent Expenses in {selected_month_name}")
    st.caption("Items purchased **more than once** this month, ordered by frequency.")

    # Get processed data from LOGIC file
    freq_data, sorted_names = get_monthly_frequent_items(df_year, selected_month_num)

    if not freq_data.empty:
        # Create Scatter Plot (Calendar Style)
        fig_freq = px.scatter(
            freq_data,
            x="date",
            y="Display Name",
            size="amount",
            color="Display Name",
            hover_data=["amount", "name"], 
            title=f"Recurring Purchases in {selected_month_name} {selected_year}",
            labels={"date": "Day of Month", "Display Name": "Item", "amount": "Cost"},
            # Dynamic height calculation
            height=max(400, len(sorted_names) * 50), 
            
            # IMPORTANT: Force the order of Y-axis based on logic result
            category_orders={"Display Name": sorted_names}
        )

        fig_freq.update_layout(
            xaxis_title="Date",
            yaxis_title="Item (Ordered by Frequency)",
            showlegend=False,
            yaxis=dict(categoryorder='array', categoryarray=sorted_names)
        )
        
        fig_freq.update_xaxes(
            dtick="D1", 
            tickformat="%d"
        )

        st.plotly_chart(fig_freq, use_container_width=True)
        
        # Optional: Show frequency summary
        with st.expander("See frequency details"):
            counts = freq_data['Display Name'].value_counts().reindex(sorted_names)
            st.dataframe(counts.reset_index(name="Count"), hide_index=True)

    else:
        st.info(f"No items were purchased more than once in {selected_month_name}.")

    st.divider()

    # ==============================================================================
    # PART 2: TOP 5 LARGEST EXPENSES (Year Overview)
    # ==============================================================================
    st.header("2. Top 5 Largest Expenses (Year Context)")
    st.caption(f"The 5 most expensive single purchases per month in {selected_year}.")

    # Get processed data from LOGIC file
    top_5_df = get_yearly_top_expenses(df_year)

    if not top_5_df.empty:
        fig_top = px.bar(
            top_5_df,
            x="amount",
            y="Month Name",
            text="name",
            orientation='h',
            color="amount",
            color_continuous_scale="Reds",
            title=f"Top 5 Expenses by Month ({selected_year})",
            labels={"amount": "Cost ($)", "Month Name": "Month"},
            height=600
        )

        fig_top.update_traces(
            textposition='inside', 
            texttemplate='%{text} ($%{x:.0f})'
        )
        
        fig_top.update_layout(
            yaxis={'categoryorder':'array', 'categoryarray': list(calendar.month_name)[1:]}
        )

        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info(f"No expenses found for the year {selected_year}.")