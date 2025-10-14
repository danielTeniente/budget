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
    category_distribution: pd.DataFrame = topic_analysis.get_category_distribution(is_fixed, n_categories)

    if category_distribution.empty:
        st.warning("No spendings data available.")
        return

    # Display pie chart
    fig = px.pie(category_distribution, names='Category', values='amount',
                 title='Spending Distribution by Category')
    st.plotly_chart(fig)

# Optional: for direct execution
if __name__ == "__main__":
    render()