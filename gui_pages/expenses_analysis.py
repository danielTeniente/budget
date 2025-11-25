import streamlit as st
import pandas as pd
from datetime import date, datetime
from expenses import topic_analysis
from widgets.expense_widgets import render_pie_chart, render_summary

def get_selected_date() -> date:
    """Get the selected date from session state."""
    selected_date = st.session_state.get("selected_date", datetime.today())
    return selected_date.date() if isinstance(selected_date, datetime) else selected_date


def get_expense_type() -> bool:
    """Get expense type selection (Fixed/Variable)."""
    return st.radio("Select expenses type:", ["Fixed", "Variable"]) == "Fixed"


def render_category_pie_chart(
    df: pd.DataFrame,
    title: str,
    category_column: str = "Category"
) -> None:
    """Render pie chart for category distribution."""
    if df.empty:
        return
    
    category_distribution = df.groupby(category_column)['amount'].sum().reset_index()
    category_distribution.columns = ['Category', 'amount']
    render_pie_chart(category_distribution, title)


def render_expense_summary(df: pd.DataFrame) -> None:
    """Render expense summary table sorted by amount."""
    if df.empty:
        return
    df_sorted = df.sort_values(by='amount', ascending=False)
    render_summary(df_sorted)


def render() -> None:
    st.title("Expenses Topic Analysis")

    selected_date = get_selected_date()
    is_fixed = get_expense_type()

    # =====================================================
    # SECTION 1: Classification by Predefined Topics
    # =====================================================
    st.subheader("📊 Classification by Predefined Topics")
    
    main_df = topic_analysis.get_category_distribution(is_fixed, selected_date)
    
    if main_df.empty:
        st.warning("No expenses data available for the selected period.")
        return

    # Render main pie chart with all categories
    render_category_pie_chart(
        df=main_df,
        title="Expenses Distribution by Category",
        category_column="Category"
    )
    
    # Show summary of all expenses
    with st.expander("View All Expenses Details", expanded=False):
        render_expense_summary(main_df)

    # =====================================================
    # SECTION 2: Subcategorization Analysis (K-Means)
    # =====================================================
    st.divider()
    st.subheader("🔍 Subcategory Analysis")
    
    # Get available categories sorted by total amount
    available_categories = topic_analysis.get_available_categories(main_df)
    default_category = topic_analysis.get_top_category(main_df)
    
    # Category selector
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_category = st.selectbox(
            "Select category to analyze:",
            options=available_categories,
            index=available_categories.index(default_category) if default_category in available_categories else 0,
            help="Choose a category to see its subcategorization"
        )
    
    with col2:
        # K-Means parameters (Number of clusters selector)
        with st.expander("⚙️ K-Means Settings"):
            n_clusters = st.number_input(
                "Number of Clusters",
                min_value=2,
                max_value=10,
                value=3,
                step=1,
                help="Define how many subcategories you want to generate."
            )
    
    # Get subcategorization for selected category
    subcategory_df = topic_analysis.get_subcategory_distribution(
        df=main_df,
        category=selected_category,
        n_clusters=int(n_clusters)
    )
    
    if subcategory_df.empty:
        st.info(f"No expenses found in category '{selected_category}'.")
        return
    
    # Show category total
    category_total = subcategory_df['amount'].sum()
    st.metric(
        label=f"Total in '{selected_category}'",
        value=f"${category_total:,.2f}"
    )
    
    # Render subcategory pie chart
    render_category_pie_chart(
        df=subcategory_df,
        title=f"Subcategories within '{selected_category}'",
        category_column="Subcategory"
    )
    
    # CAMBIO PRINCIPAL AQUÍ:
    # Mostramos los detalles agrupados por subcategoría en lugar de una tabla plana
    with st.expander(f"View '{selected_category}' Expenses Details", expanded=True):
        
        # Agrupamos por la subcategoría (etiqueta generada por KMeans)
        # Ordenamos los grupos por monto total descendente para mostrar lo más relevante primero
        grouped = subcategory_df.groupby('Subcategory')
        sorted_groups = sorted(grouped, key=lambda x: x[1]['amount'].sum(), reverse=True)

        for subcat_name, group_data in sorted_groups:
            # Calculamos el total de este grupo
            group_total = group_data['amount'].sum()
            
            # Mostramos Título: Nombre Subcategoría (Total)
            st.markdown(f"#### 🔹 {subcat_name} <span style='color:gray; font-size:0.8em'>(${group_total:,.2f})</span>", unsafe_allow_html=True)
            
            # Preparamos la tabla para este grupo
            # Seleccionamos 'name' y 'amount' para dar contexto, pero mantenemos foco en el nombre
            items_display = group_data[['name', 'amount']].sort_values(by='amount', ascending=False)
            items_display.columns = ['Item Name', 'Amount']
            
            # Renderizamos la tabla limpia sin índice
            st.dataframe(
                items_display,
                use_container_width=True,
                hide_index=True
            )
            # Añadimos un pequeño separador visual
            st.write("") 

if __name__ == "__main__":
    render()