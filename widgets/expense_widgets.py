import streamlit as st
import pandas as pd
import plotly.express as px

def render_pie_chart(df: pd.DataFrame, title: str) -> None:
    """Render a pie chart from a category distribution DataFrame."""
    fig = px.pie(df, names='Category', values='amount', title=title)
    st.plotly_chart(fig)

def render_summary(df: pd.DataFrame) -> None:
    """Render a summary of expenses grouped by category."""
    st.subheader("Summary by Category")
    summary_df = (
        df.groupby('Category', sort=False)
        .agg(
            amount=('amount', 'sum'),
            name=('name', lambda names: ', '.join(names))
        )
        .reset_index()
    )
    summary_df = summary_df.sort_values(by='amount', ascending=False)

    for _, row in summary_df.iterrows():
        # if amount is very large, make it bold
        st.markdown(f"**{row['Category']}** — **{row['amount']:.2f}**\n\n{row['name']}")