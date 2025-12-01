import streamlit as st
import plotly.graph_objects as go
from utils.projection_logic import get_projections, prepare_projection_data

def render() -> None:
    """Render the financial projection page."""

    st.title("Proyecciones Financieras")

    data_context = prepare_projection_data()

    # --- Sidebar Configuration ---
    st.sidebar.header("Configuración")
    num_months = st.sidebar.slider("Meses a proyectar", 1, 24, 6)
    
    st.subheader("1. Configuración de Ingresos")
    col1, col2 = st.columns(2)
    with col1:
        unique_inc_names = data_context["unique_fixed_inc_options"]["name"].tolist()
        selected_inc = st.multiselect(
            "Ingresos Fijos (Recurrentes)",
            options=unique_inc_names,
            default=unique_inc_names
        )
    with col2:
        var_inc_method = st.selectbox(
            "Ingresos Variables",
            options=["Promedio", "Máximo", "Mínimo", "Ninguno"],
            index=0
        )

    st.subheader("2. Configuración de Gastos")
    col3, col4 = st.columns(2)
    with col3:
        unique_exp_names = data_context["unique_fixed_exp_options"]["name"].tolist()
        selected_exp = st.multiselect(
            "Gastos Fijos (Recurrentes)",
            options=unique_exp_names,
            default=unique_exp_names
        )
    with col4:
        var_exp_method = st.selectbox(
            "Gastos Variables",
            options=["Promedio", "Máximo", "Mínimo", "Ninguno"],
            index=0
        )

    st.divider()

    # --- Obtener Proyecciones y Resumen ---
    projection_df, summary = get_projections(
        num_months=num_months,
        selected_fixed_inc_names=selected_inc,
        selected_fixed_exp_names=selected_exp,
        var_inc_method=var_inc_method,
        var_exp_method=var_exp_method,
        data_context=data_context
    )

    # --- Explicación de los números (Texto Corregido) ---
    
    # 1. Preparar texto para Gastos
    if summary['var_exp_method'] == "Ninguno":
        gastos_var_text = "ya que elegiste la opción de **ningún** gasto variable"
    else:
        # Convertimos a minúsculas para que fluya en la frase
        method_lower = summary['var_exp_method'].lower()
        gastos_var_text = f"cifra que equivale al **{method_lower}** de los gastos variables de los últimos 3 meses"

    # 2. Renderizar Mensaje de Gastos
    st.info(f"""
    **📊 Desglose de Gastos Proyectados:**
    
    * **Total Proyectado:** ${summary['total_expenses']:,.2f}
    * **Gastos Fijos:** ${summary['fixed_expenses']:,.2f} (suma de los ítems seleccionados).
    * **Gastos Variables:** ${summary['variable_expenses']:,.2f}, {gastos_var_text}.
    """)

    # 3. Preparar texto para Ingresos (Simétrico)
    if summary['var_inc_method'] == "Ninguno":
        ingresos_var_text = "ya que elegiste la opción de **ningún** ingreso variable"
    else:
        method_lower = summary['var_inc_method'].lower()
        ingresos_var_text = f"cifra que equivale al **{method_lower}** de los ingresos variables de los últimos 3 meses"

    with st.expander("Ver detalle de Ingresos Proyectados"):
        st.markdown(f"""
        * **Total Proyectado:** ${summary['total_income']:,.2f}
        * **Ingresos Fijos:** ${summary['fixed_income']:,.2f} (suma de los ítems seleccionados).
        * **Ingresos Variables:** ${summary['variable_income']:,.2f}, {ingresos_var_text}.
        """)

    # --- Plotting ---
    fig = go.Figure()

    # Colores
    colors_income = ['#A5D6A7' if t == "Histórico" else '#2E7D32' for t in projection_df.get("type", [])]
    colors_expense = ['#EF9A9A' if t == "Histórico" else '#C62828' for t in projection_df.get("type", [])]

    fig.add_trace(go.Bar(
        x=projection_df["month"],
        y=projection_df["total_income"],
        name="Ingresos",
        marker_color=colors_income
    ))

    fig.add_trace(go.Bar(
        x=projection_df["month"],
        y=projection_df["total_expenses"],
        name="Gastos",
        marker_color=colors_expense
    ))

    # Filtramos la línea de balance para que no conecte puntos vacíos del histórico
    balance_trace = projection_df.dropna(subset=["balance"])
    
    fig.add_trace(go.Scatter(
        x=balance_trace["month"],
        y=balance_trace["balance"],
        mode="lines+markers",
        name="Balance Proyectado",
        line=dict(color="blue", width=3)
    ))

    fig.update_layout(
        title="Historial (3 meses) y Proyección",
        xaxis_title="Mes",
        yaxis_title="Monto",
        barmode="group",
        legend_title="Indicadores"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen solo futuros
    st.subheader("Tabla de Proyección Futura")
    proj_only = projection_df[projection_df["type"] == "Proyectado"].copy()
    
    if not proj_only.empty:
        st.dataframe(proj_only[["month", "total_income", "total_expenses", "balance"]].style.format({
            "total_income": "${:,.2f}",
            "total_expenses": "${:,.2f}",
            "balance": "${:,.2f}"
        }))