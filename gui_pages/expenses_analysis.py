import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime

# Import backend logic
from expenses import topic_analysis, topic_match


def render() -> None:
    """Render the topic analysis page in Streamlit."""

    st.title("expenses Topic Analysis")

    selected_date = st.session_state.get("selected_date", datetime.today())
    # cast to date if it's datetime
    if isinstance(selected_date, datetime):
        selected_date = selected_date.date()
    # expenses type selection
    is_fixed: bool = st.radio("Select expenses type:", ["Fixed", "Variable"]) == "Fixed"

    # Number of categories
    n_categories: int = st.slider("Select number of categories:", min_value=2, max_value=10, value=3)

    # Run analysis
    labeled_df: pd.DataFrame = topic_analysis.get_category_distribution(
        is_fixed, n_categories, selected_date
    )
    category_distribution: pd.DataFrame = labeled_df.groupby('Category')['amount'].sum().reset_index()

    if category_distribution.empty:
        st.warning("No expenses data available.")
        return

    # Display pie chart
    fig = px.pie(category_distribution, names='Category', values='amount',
                 title='expenses Distribution by Category')
    st.plotly_chart(fig)


    # Sort labeled_df by amount descending
    labeled_df = labeled_df.sort_values(by='amount', ascending=False)

    # Group by Category and aggregate
    summary_df = (
        labeled_df
        .groupby('Category', sort=False)
        .agg(
            amount=('amount', 'sum'),
            name=('name', lambda names: ', '.join(names))
        )
        .reset_index()
        .sort_values(by='amount', ascending=False)
    )

    # Create and display summary as formatted text
    st.subheader("Summary by Category")

    for _, row in summary_df.iterrows():
        st.markdown(f"**{row['Category']}** — **{row['amount']:.2f}**\n\n{row['name']}")

    # Preselected topics
    st.subheader("Predefined Topics")
    matched_df: pd.DataFrame = topic_match.get_category_distribution(
        is_fixed, selected_date
    )
    if matched_df.empty:
        st.warning("No expenses data available for topic matching.")
        return
    topic_distribution: pd.DataFrame = matched_df.groupby('Category')['amount'].sum().reset_index()
    fig2 = px.pie(topic_distribution, names='Category', values='amount',
                  title='expenses Distribution by Predefined Topics')
    st.plotly_chart(fig2)
    
# Optional: for direct execution
if __name__ == "__main__":
    render()