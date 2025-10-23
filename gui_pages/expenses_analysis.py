import streamlit as st
import pandas as pd
from datetime import date, datetime

from typing import Callable
from expenses import topic_analysis, topic_match
from widgets.expense_widgets import render_pie_chart, render_summary


def get_selected_date() -> date:
    selected_date = st.session_state.get("selected_date", datetime.today())
    return selected_date.date() if isinstance(selected_date, datetime) else selected_date


def get_expense_type() -> bool:
    return st.radio("Select expenses type:", ["Fixed", "Variable"]) == "Fixed"

def render_expense_section(
    data_fetcher: Callable[[bool, date], pd.DataFrame],
    is_fixed: bool,
    selected_date: date,
    pie_title: str,
    show_summary: bool = True,
    section_title: str | None = None,
    empty_warning: str = "No expenses data available."
) -> None:
    """Generic renderer for expense analysis sections."""
    df = data_fetcher(is_fixed, selected_date)
    if df.empty:
        st.warning(empty_warning)
        return

    if section_title:
        st.subheader(section_title)

    category_distribution = df.groupby('Category')['amount'].sum().reset_index()
    render_pie_chart(category_distribution, pie_title)

    if show_summary:
        df = df.sort_values(by='amount', ascending=False)
        # order by amount descending
        render_summary(df)

def render() -> None:
    st.title("Expenses Topic Analysis")

    selected_date = get_selected_date()
    is_fixed = get_expense_type()
    render_expense_section(
        data_fetcher=topic_match.get_category_distribution,
        is_fixed=is_fixed,
        selected_date=selected_date,
        pie_title="Expenses Distribution by Predefined Topics",
        show_summary=True,
        section_title="Predefined Topics",
        empty_warning="No expenses data available for topic matching."
    )

    render_expense_section(
        data_fetcher=topic_analysis.get_category_distribution,
        is_fixed=is_fixed,
        selected_date=selected_date,
        pie_title="Expenses Distribution by Category",
        show_summary=True
    )


if __name__ == "__main__":
    render()