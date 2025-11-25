import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from gui_pages.frequent_expenses import render as render_frequent_expenses
from utils.summary_logic import (
    load_total_income,
    load_total_expenses,
    prepare_timeline_data,
    aggregate_daily_totals,
    calculate_net_total
)

def render() -> None:
    """Render the financial summary page with timelines and net balance."""

    st.title("Financial Summary")

    # Load data
    income_df = load_total_income()
    expenses_df = load_total_expenses()

    # Ensure date columns are datetime objects (just in case)
    income_df['date'] = pd.to_datetime(income_df['date'])
    expenses_df['date'] = pd.to_datetime(expenses_df['date'])

    # ---------------------------------------------------------
    # EXISTING CHART: Timeline
    # ---------------------------------------------------------
    
    # Prepare timeline
    timeline_df = prepare_timeline_data(income_df, expenses_df)

    # Prepare daily totals
    daily_income = aggregate_daily_totals(income_df)
    daily_income["type"] = "Daily Income"

    daily_expenses = aggregate_daily_totals(expenses_df)
    daily_expenses["type"] = "Daily Expenses"

    fig = go.Figure()

    # Add Daily Income trace
    fig.add_trace(go.Scatter(
        x=daily_income['date'],
        y=daily_income['amount'],
        mode='lines',
        name='Daily Income',
        line=dict(color='green')
    ))

    # Add Daily Expenses trace
    fig.add_trace(go.Scatter(
        x=daily_expenses['date'],
        y=daily_expenses['amount'],
        mode='lines',
        name='Daily Expenses',
        line=dict(color='red')
    ))

    # Add Cumulative Balance trace
    fig.add_trace(go.Scatter(
        x=timeline_df['date'],
        y=timeline_df['cumulative_amount'],
        mode='lines',
        name='Cumulative Balance',
        line=dict(color='blue')
    ))

    fig.update_layout(
        title='Income, Expenses, and Cumulative Balance Timeline',
        xaxis_title='Date',
        yaxis_title='Amount'
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # TOTALS SECTION
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    
    total_income = income_df["amount"].sum()
    total_expenses = expenses_df["amount"].sum()
    net_total = calculate_net_total(income_df, expenses_df)

    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Net Balance", f"${net_total:,.2f}", delta_color="normal")

    if net_total >= 0:
        st.success("You are in a positive balance!")
    else:
        st.error("You are in a negative balance!")

    st.divider()

    # ---------------------------------------------------------
    # NEW FEATURE 1: Monthly Summary Table (Current Year)
    # ---------------------------------------------------------
    st.subheader("Monthly Summary (Current Year)")

    current_year = datetime.now().year
    
    # Filter for current year
    inc_curr = income_df[income_df['date'].dt.year == current_year].copy()
    exp_curr = expenses_df[expenses_df['date'].dt.year == current_year].copy()

    if not inc_curr.empty or not exp_curr.empty:
        # Create Month column for grouping
        inc_curr['Month'] = inc_curr['date'].dt.month_name()
        inc_curr['Month_Num'] = inc_curr['date'].dt.month
        
        exp_curr['Month'] = exp_curr['date'].dt.month_name()
        exp_curr['Month_Num'] = exp_curr['date'].dt.month

        # Group by Month
        inc_grouped = inc_curr.groupby(['Month_Num', 'Month'])['amount'].sum().reset_index()
        exp_grouped = exp_curr.groupby(['Month_Num', 'Month'])['amount'].sum().reset_index()

        # Merge
        monthly_df = pd.merge(inc_grouped, exp_grouped, on=['Month_Num', 'Month'], how='outer', suffixes=('_Inc', '_Exp')).fillna(0)
        
        # Sort by month number
        monthly_df = monthly_df.sort_values('Month_Num')
        
        # Calculate Balance
        monthly_df['Net Balance'] = monthly_df['amount_Inc'] - monthly_df['amount_Exp']
        
        # Rename for display
        display_df = monthly_df[['Month', 'amount_Inc', 'amount_Exp', 'Net Balance']].copy()
        display_df.columns = ['Month', 'Total Income', 'Total Expenses', 'Net Balance']

        # Format as currency strings for cleaner table or use st.dataframe column config
        st.dataframe(
            display_df,
            column_config={
                "Total Income": st.column_config.NumberColumn(format="$%.2f"),
                "Total Expenses": st.column_config.NumberColumn(format="$%.2f"),
                "Net Balance": st.column_config.NumberColumn(format="$%.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info(f"No data available for the year {current_year}.")

    st.divider()

    render_frequent_expenses()

