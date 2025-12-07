import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from utils.projection_logic import get_projections, get_detailed_projections, prepare_projection_data

def plot_projections(projection_df, title_suffix=""):
    """Helper para graficar los resultados."""
    if projection_df.empty:
        st.warning("No hay datos para proyectar.")
        return

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

    # Línea de balance
    balance_trace = projection_df.dropna(subset=["balance"])
    fig.add_trace(go.Scatter(
        x=balance_trace["month"],
        y=balance_trace["balance"],
        mode="lines+markers",
        name="Balance Proyectado",
        line=dict(color="blue", width=3)
    ))

    fig.update_layout(
        title=f"Flujo de Caja y Proyección {title_suffix}",
        xaxis_title="Mes",
        yaxis_title="Monto",
        barmode="group",
        legend_title="Indicadores"
    )

    st.plotly_chart(fig, use_container_width=True)

def render_simple_tab(data_context):
    """Renderiza la pestaña de proyección simple (Global)."""
    st.markdown("##### Configuración General (Aplica a todos los meses)")
    
    col_months, _ = st.columns([1, 2])
    with col_months:
        num_months = st.slider("Meses a proyectar", 1, 24, 6, key="simple_slider")

    col1, col2 = st.columns(2)
    with col1:
        unique_inc_names = data_context["unique_fixed_inc_options"]["name"].tolist()
        selected_inc = st.multiselect(
            "Ingresos Fijos",
            options=unique_inc_names,
            default=unique_inc_names,
            key="simple_inc"
        )
        var_inc_method = st.selectbox(
            "Método Ingresos Variables",
            options=["Promedio", "Máximo", "Mínimo", "Ninguno"],
            index=0,
            key="simple_var_inc"
        )

    with col2:
        unique_exp_names = data_context["unique_fixed_exp_options"]["name"].tolist()
        selected_exp = st.multiselect(
            "Gastos Fijos",
            options=unique_exp_names,
            default=unique_exp_names,
            key="simple_exp"
        )
        var_exp_method = st.selectbox(
            "Método Gastos Variables",
            options=["Promedio", "Máximo", "Mínimo", "Ninguno"],
            index=0,
            key="simple_var_exp"
        )

    if st.button("Generar Proyección Simple"):
        projection_df, summary = get_projections(
            num_months=num_months,
            selected_fixed_inc_names=selected_inc,
            selected_fixed_exp_names=selected_exp,
            var_inc_method=var_inc_method,
            var_exp_method=var_exp_method,
            data_context=data_context
        )
    
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
        # Resumen rápido
        st.info(f"**Resumen Mensual Promedio:** Ingresos: ${summary['total_income']:,.2f} | Gastos: ${summary['total_expenses']:,.2f}")
        
        plot_projections(projection_df, "(Simple)")
        
        with st.expander("Ver tabla de datos"):
            st.dataframe(projection_df)

def render_detailed_tab(data_context):
    """Renderiza la pestaña de proyección detallada (Mes a Mes)."""
    st.info("💡 Aquí puedes seleccionar qué ingresos y gastos aplicar específicamente para cada mes futuro.")

    # Variables globales para la proyección fina (Variables se mantienen por método para simplificar UI)
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    with col_cfg1:
        num_months = st.number_input("Meses a proyectar", min_value=1, max_value=24, value=6, step=1, key="detail_months")
    with col_cfg2:
        var_inc_method = st.selectbox("Ing. Variables (Base)", ["Promedio", "Máximo", "Mínimo", "Ninguno"], key="detail_var_inc")
    with col_cfg3:
        var_exp_method = st.selectbox("Gas. Variables (Base)", ["Promedio", "Máximo", "Mínimo", "Ninguno"], key="detail_var_exp")

    unique_inc_names = data_context["unique_fixed_inc_options"]["name"].tolist()
    unique_exp_names = data_context["unique_fixed_exp_options"]["name"].tolist()

    st.divider()
    st.markdown("###### Selección Mensual")

    monthly_selections = {}
    
    current_date = datetime.today().replace(day=1)

    # Creamos un contenedor scrolleable o simplemente iteramos
    for i in range(num_months):
        month_date = current_date + pd.DateOffset(months=i)
        month_label = month_date.strftime("%B %Y").capitalize()
        
        # Usamos expander para que no ocupe tanto espacio visual
        with st.expander(f"Mes {i+1}: {month_label}", expanded=(i == 0)):
            col_a, col_b = st.columns(2)
            with col_a:
                sel_inc = st.multiselect(
                    f"Ingresos {month_label}", 
                    options=unique_inc_names, 
                    default=unique_inc_names, # Por defecto todos
                    key=f"inc_{i}"
                )
            with col_b:
                sel_exp = st.multiselect(
                    f"Gastos {month_label}", 
                    options=unique_exp_names, 
                    default=unique_exp_names, # Por defecto todos
                    key=f"exp_{i}"
                )
            
            monthly_selections[i] = {
                'inc': sel_inc,
                'exp': sel_exp
            }

    if st.button("Generar Proyección Detallada", type="primary"):
        projection_df = get_detailed_projections(
            num_months=num_months,
            monthly_selections=monthly_selections,
            var_inc_method=var_inc_method,
            var_exp_method=var_exp_method,
            data_context=data_context
        )
        
        plot_projections(projection_df, "(Detallada)")

        # Tabla de solo futuros para revisión fina
        st.subheader("Detalle Futuro")
        proj_only = projection_df[projection_df["type"] == "Proyectado"].copy()
        st.dataframe(proj_only[["month", "total_income", "total_expenses", "balance"]].style.format({
            "total_income": "${:,.2f}",
            "total_expenses": "${:,.2f}",
            "balance": "${:,.2f}"
        }))

def render() -> None:
    """Render the financial projection page."""
    st.title("Proyecciones Financieras")

    # Cargar datos una sola vez
    data_context = prepare_projection_data()

    tab1, tab2 = st.tabs(["🚀 Proyección Simple", "🧐 Proyección Fina (Mes a Mes)"])

    with tab1:
        render_simple_tab(data_context)
    
    with tab2:
        render_detailed_tab(data_context)