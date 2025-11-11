import streamlit as st
import plotly.graph_objects as go
from utils.projection_logic import get_projections

def render() -> None:
    """Render the financial projection page."""

    st.title("Financial Projections")

    # User input: number of months to project
    num_months = st.slider("Select number of months to project", min_value=1, max_value=24, value=6)

    # Get projections
    projection_df = get_projections(num_months)

    # Plotting
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=projection_df["month"],
        y=projection_df["total_income"],
        name="Projected Income",
        marker_color="green"
    ))

    fig.add_trace(go.Bar(
        x=projection_df["month"],
        y=projection_df["total_expenses"],
        name="Projected Expenses",
        marker_color="red"
    ))

    fig.add_trace(go.Scatter(
        x=projection_df["month"],
        y=projection_df["balance"],
        mode="lines+markers",
        name="Projected Balance",
        line=dict(color="blue", width=3)
    ))

    fig.update_layout(
        title="Projected Income, Expenses, and Balance",
        xaxis_title="Month",
        yaxis_title="Amount",
        barmode="group"
    )

    st.plotly_chart(fig)

    # Display summary table
    st.subheader("Projection Summary")
    st.dataframe(projection_df.style.format({
        "total_income": "${:,.2f}",
        "total_expenses": "${:,.2f}",
        "balance": "${:,.2f}"
    }))