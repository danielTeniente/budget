import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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

    # Prepare timeline
    timeline_df = prepare_timeline_data(income_df, expenses_df)

    
    # Prepare daily totals
    daily_income = aggregate_daily_totals(income_df)
    daily_income["type"] = "Daily Income"

    daily_expenses = aggregate_daily_totals(expenses_df)
    daily_expenses["type"] = "Daily Expenses"

    # Assuming daily_income, daily_expenses, and timeline_df are already defined
    # and each has 'date' and 'amount' columns
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

    # Update layout
    fig.update_layout(
        title='Income, Expenses, and Cumulative Balance Timeline',
        xaxis_title='Date',
        yaxis_title='Amount'
    )

    # Display the plot
    st.plotly_chart(fig)

    # Display total amounts
    total_income = income_df["amount"].sum()
    total_expenses = expenses_df["amount"].sum()
    # Display totals with plain text without subheaders
    st.write(f"Total Income: ${total_income:.2f}")
    st.write(f"Total Expenses: ${total_expenses:.2f}")
    
    # Calculate and display net total
    net_total = calculate_net_total(income_df, expenses_df)
    st.subheader(f"Net Total Balance: ${net_total:.2f}")
    if net_total >= 0:
        st.success("You are in a positive balance!")
    else:
        st.error("You are in a negative balance!")


