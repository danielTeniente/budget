import streamlit as st
from deuda.data_handler import (
    load_debts, add_debt, update_debt_status, 
    delete_debt, get_projected_amount, Debt, MONTHLY_INTEREST_RATE
)

def render() -> None:
    st.title("💰 Control de Deudas")
    
    # 1. Configuración de Visualización
    is_fixed = st.radio("Tipo de Deuda", [True, False], 
                        format_func=lambda x: "Fija (Amortización)" if x else "Variable (Con Interés 16%)")
    
    df = load_debts(is_fixed)
    
    # 2. Resumen y Proyecciones
    if not df.empty:
        st.subheader("Estado de Deudas Actuales")
        
        # Calcular proyecciones para la tabla
        df_display = df.copy()
        df_display["Proyección Mes Prox."] = df_display["amount"].apply(lambda x: get_projected_amount(x, is_fixed))
        df_display["Interés Estimado"] = df_display["Proyección Mes Prox."] - df_display["amount"]
        
        # Métricas principales
        total_actual = df_display["amount"].sum()
        total_proyectado = df_display["Proyección Mes Prox."].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Deuda Total Hoy", f"${total_actual:,.2f}")
        if not is_fixed:
            col_m2.metric("Proyección Próx. Mes", f"${total_proyectado:,.2f}", 
                          delta=f"${total_proyectado - total_actual:,.2f}", delta_color="inverse")
            col_m3.metric("Tasa Mensual", f"{MONTHLY_INTEREST_RATE*100:.2f}%")

        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No hay deudas registradas en esta categoría.")

    st.divider()

    # 3. Acciones: Actualizar o Agregar
    tab1, tab2 = st.tabs(["Registrar Pago / Actualizar", "Crear Nueva Deuda"])

    with tab1:
        if not df.empty:
            debt_index = st.selectbox("Selecciona la deuda", options=df.index, 
                                        format_func=lambda x: f"{df.loc[x, 'name']} (Saldo: ${df.loc[x, 'amount']})")
            with st.form("payment_form"):
                st.write("### Registrar un pago")
                payment = st.number_input("Cantidad pagada este mes", min_value=0.0, step=10.0)
                
                if st.form_submit_button("Actualizar Saldo"):
                    update_debt_status(debt_index, payment, is_fixed)
                    st.success("¡Saldo actualizado!")
                    st.rerun()
            
            if st.button("Eliminar Deuda Seleccionada", type="secondary"):
                delete_debt(debt_index, is_fixed)
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