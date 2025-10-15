import streamlit as st
import pandas as pd
import plotly.express as px

# Import backend logic
from spendings import topic_analysis
def render() -> None:
    """Render the topic analysis page in Streamlit."""

    st.title("Spending Topic Analysis")

    # Spending type selection
    is_fixed: bool = st.radio("Select spending type:", ["Fixed", "Variable"]) == "Fixed"

    # Number of categories
    n_categories: int = st.slider("Select number of categories:", min_value=2, max_value=10, value=3)

    # Run analysis
    labeled_df: pd.DataFrame = topic_analysis.get_category_distribution(is_fixed, n_categories)
    category_distribution: pd.DataFrame = labeled_df.groupby('Category')['amount'].sum().reset_index()

    if category_distribution.empty:
        st.warning("No spendings data available.")
        return

    # Display pie chart
    fig = px.pie(category_distribution, names='Category', values='amount',
                 title='Spending Distribution by Category')
    st.plotly_chart(fig)

    # Create summary table
    summary_df = labeled_df.groupby('Category').agg({
        'amount': 'sum',
        'name': lambda names: ', '.join(names)
    }).reset_index()

    # Create and display summary as formatted text
    st.subheader("Summary by Category")

    for _, row in summary_df.iterrows():
        st.markdown(f"**{row['Category']}** — **{row['amount']:.2f}**\n\n{row['name']}")

# Optional: for direct execution
if __name__ == "__main__":
    render()