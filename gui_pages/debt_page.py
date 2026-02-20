import streamlit as st
import pandas as pd
from deuda.data_handler import (
    load_debts, add_debt, update_debt_status, 
    delete_debt, get_projected_amount, Debt, MONTHLY_INTEREST_RATE
)

def render() -> None:
    st.title("💰 Control de Deudas")
    
    # 1. Configuración de Visualización
    is_fixed = st.radio("Tipo de Deuda", [True, False], 
                        format_func=lambda x: "Fija (Amortización)" if x else "Variable (Con Interés 16%)")
    
    df_all = load_debts(is_fixed)
    
    # IMPORTANTE: Filtrar solo las deudas vigentes para el resumen y proyecciones
    if not df_all.empty:
        df = df_all[df_all["is_current"] == 1].copy()
    else:
        df = df_all

    # 2. Resumen y Proyecciones
    if not df.empty:
        st.subheader("Estado de Deudas Actuales")
        
        df_display = df.copy()
        df_display["Proyección Mes Prox."] = df_display["amount"].apply(lambda x: get_projected_amount(x, is_fixed))
        df_display["Interés Estimado"] = df_display["Proyección Mes Prox."] - df_display["amount"]
        
        total_actual = df_display["amount"].sum()
        total_proyectado = df_display["Proyección Mes Prox."].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Deuda Total Hoy", f"${total_actual:,.2f}")
        if not is_fixed:
            col_m2.metric("Proyección Próx. Mes", f"${total_proyectado:,.2f}", 
                          delta=f"${total_proyectado - total_actual:,.2f}", delta_color="inverse")
            col_m3.metric("Tasa Mensual", f"{MONTHLY_INTEREST_RATE*100:.2f}%")

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No hay deudas vigentes en esta categoría.")

    st.divider()

    # 3. Acciones: Actualizar o Agregar
    tab1, tab2 = st.tabs(["Registrar Pago / Actualizar", "Crear Nueva Deuda"])

    with tab1:
        if not df.empty:
            # Usamos el ID como identificador detrás de escena
            selected_debt_id = st.selectbox(
                "Selecciona la deuda", 
                options=df["id"], 
                format_func=lambda x: f"{df[df['id']==x]['name'].values[0]} (Saldo: ${df[df['id']==x]['amount'].values[0]:,.2f})"
            )
            
            with st.form("payment_form"):
                st.write("### Registrar un pago")
                payment = st.number_input("Cantidad pagada este mes", min_value=0.0, step=10.0)
                
                if st.form_submit_button("Actualizar Saldo"):
                    update_debt_status(selected_debt_id, payment, is_fixed)
                    st.success("¡Saldo actualizado! (Historial guardado)")
                    st.rerun()
            
            if st.button("Eliminar Deuda Seleccionada", type="secondary"):
                delete_debt(selected_debt_id, is_fixed)
                st.rerun()
        else:
            st.caption("No hay deudas para actualizar.")

    with tab2:
        with st.form("add_debt_form"):
            st.write("### Nueva Deuda")
            new_name = st.text_input("Nombre de la Deuda")
            new_amount = st.number_input("Monto Inicial / Actual", min_value=0.0)
            new_desc = st.text_input("Descripción / Entidad")
            
            if st.form_submit_button("Guardar Deuda"):
                if new_name and new_amount > 0:
                    new_debt = Debt(new_name, new_amount, new_desc, is_fixed)
                    add_debt(new_debt)
                    st.success("Deuda agregada correctamente")
                    st.rerun()
                else:
                    st.error("Nombre y monto son obligatorios.")

    # --- SECCIÓN: GRÁFICO DE EVOLUCIÓN ---
    st.divider()
    st.subheader("📈 Evolución del Saldo en el Tiempo")

    # Cargamos todos los datos (incluyendo históricos)
    # Si quieres ver la evolución de AMBAS carteras al tiempo, puedes concatenarlas
    df_fixed = load_debts(is_fixed=True)
    df_var = load_debts(is_fixed=False)
    df_plot = pd.concat([df_fixed, df_var], ignore_index=True)

    if not df_plot.empty:
        import plotly.express as px

        # 1. Preparación de datos
        df_plot["last_update"] = pd.to_datetime(df_plot["last_update"])
        # Ordenamos por fecha para que la línea siga una secuencia lógica
        df_plot = df_plot.sort_values(by=["last_update"])

        # 2. Creación del gráfico
        # Usamos 'id' o 'name' en color para que cada deuda sea una línea distinta
        fig = px.line(
            df_plot, 
            x="last_update", 
            y="amount", 
            color="name",
            markers=True,
            line_shape="linear",
            labels={
                "last_update": "Fecha de Actualización",
                "amount": "Monto Pendiente ($)",
                "name": "Obligación"
            },
            template="plotly_white"
        )

        # 3. Ajustes estéticos
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar la evolución.")                