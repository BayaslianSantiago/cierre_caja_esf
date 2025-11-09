import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cierre de Caja", layout="wide")

st.title("💰 Sistema de Cierre de Caja")

# Columnas principales
col1, col2 = st.columns(2)

with col1:
    st.header("📊 Facturación")
    balanza = st.number_input("BALANZA (Facturación Total)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    registradora = st.number_input("REGISTRADORA (Tickets Fiscales)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

with col2:
    st.header("💵 Caja Real")
    caja_real = st.number_input("CAJA REAL (Dinero físico contado)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

st.divider()

# Formas de pago
st.header("💳 Formas de Pago")

col3, col4, col5 = st.columns(3)

with col3:
    st.subheader("Pagos Físicos")
    vales = st.number_input("VALES", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    transferencias = st.number_input("TRANSFERENCIAS", min_value=0.0, value=0.0, step=100.0, format="%.2f")

with col4:
    st.subheader("Efectivo")
    efectivo = st.number_input("EFECTIVO", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

with col5:
    st.subheader("Pagos Electrónicos")
    mercadopago = st.number_input("MERCADOPAGO", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    getnet = st.number_input("GETNET", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
    posnet = st.number_input("POSNET", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

st.divider()

# Control de caja entre días
st.header("🔄 Control de Caja entre Días")
col_dias1, col_dias2 = st.columns(2)

with col_dias1:
    dinero_ayer = st.number_input("Dinero que quedó del día ANTERIOR", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    st.caption("Este dinero se resta del efectivo de hoy")

with col_dias2:
    dinero_manana = st.number_input("Dinero que QUEDA en caja para MAÑANA", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    st.caption("Este dinero queda en el local para el próximo día")

st.divider()

# Salidas de caja
st.header("📤 Salidas de Caja")
col6, col7, col8 = st.columns(3)

with col6:
    salida_1 = st.number_input("Salida 1", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col7:
    salida_2 = st.number_input("Salida 2", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col8:
    salida_3 = st.number_input("Salida 3", min_value=0.0, value=0.0, step=100.0, format="%.2f")

st.divider()

# CÁLCULOS
efectivo_neto = efectivo - dinero_ayer
salidas_total = salida_1 + salida_2 + salida_3
pagos_digitales_total = mercadopago + getnet + posnet

suma_total = (vales + transferencias + efectivo + 
              mercadopago + getnet + posnet + salidas_total)

dinero_a_retirar = efectivo_neto - dinero_manana

errores = caja_real - suma_total
balanza_menos_errores = balanza - errores

# Verificación de registradora vs pagos digitales
diferencia_registradora = registradora - pagos_digitales_total

# RESULTADOS
st.header("📈 Resultados del Cierre")

col9, col10, col11, col12 = st.columns(4)

with col9:
    st.metric("EFECTIVO", f"${efectivo:,.2f}")
    st.metric("Efectivo del día anterior", f"-${dinero_ayer:,.2f}")
    st.metric("EFECTIVO NETO", f"${efectivo_neto:,.2f}")

with col10:
    st.metric("Queda para mañana", f"${dinero_manana:,.2f}")
    st.metric("💵 DINERO A RETIRAR", f"${dinero_a_retirar:,.2f}")
    st.metric("SALIDAS TOTAL", f"${salidas_total:,.2f}")

with col11:
    st.metric("PAGOS DIGITALES", f"${pagos_digitales_total:,.2f}")
    if abs(diferencia_registradora) < 0.01:
        st.success("✅ Registradora OK")
    else:
        st.warning(f"⚠️ Dif: ${diferencia_registradora:,.2f}")

with col12:
    st.metric("SUMA TOTAL", f"${suma_total:,.2f}")
    if errores > 0:
        st.metric("ERRORES (Sobrante)", f"${errores:,.2f}", delta=f"+${errores:,.2f}")
    elif errores < 0:
        st.metric("ERRORES (Faltante)", f"${errores:,.2f}", delta=f"${errores:,.2f}")
    else:
        st.metric("ERRORES", f"${errores:,.2f}")
    
    st.metric("BALANZA - ERRORES", f"${balanza_menos_errores:,.2f}")

st.divider()

# TABLA RESUMEN
st.header("📋 Resumen Detallado")

datos_resumen = {
    "Concepto": [
        "BALANZA",
        "REGISTRADORA",
        "CAJA REAL",
        "━━━━━━━━━━━━━━━━━",
        "VALES",
        "TRANSFERENCIAS",
        "EFECTIVO",
        "Dinero día anterior",
        "EFECTIVO NETO",
        "MERCADOPAGO",
        "GETNET",
        "POSNET",
        "━━━━━━━━━━━━━━━━━",
        "PAGOS DIGITALES TOTAL",
        "DIFERENCIA REGISTRADORA",
        "ERRORES",
        "SALIDA DE CAJA",
        "SUMA TOTAL",
        "BALANZA MENOS ERRORES",
        "━━━━━━━━━━━━━━━━━",
        "Dinero para MAÑANA",
        "💵 DINERO A RETIRAR HOY"
    ],
    "Monto ($)": [
        f"{balanza:,.2f}",
        f"{registradora:,.2f}",
        f"{caja_real:,.2f}",
        "",
        f"{vales:,.2f}",
        f"{transferencias:,.2f}",
        f"{efectivo:,.2f}",
        f"-{dinero_ayer:,.2f}",
        f"{efectivo_neto:,.2f}",
        f"{mercadopago:,.2f}",
        f"{getnet:,.2f}",
        f"{posnet:,.2f}",
        "",
        f"{pagos_digitales_total:,.2f}",
        f"{diferencia_registradora:,.2f}",
        f"{errores:,.2f}",
        f"{salidas_total:,.2f}",
        f"{suma_total:,.2f}",
        f"{balanza_menos_errores:,.2f}",
        "",
        f"{dinero_manana:,.2f}",
        f"{dinero_a_retirar:,.2f}"
    ]
}

df_resumen = pd.DataFrame(datos_resumen)
st.dataframe(df_resumen, use_container_width=True, hide_index=True)

# Verificación final
st.divider()

col_verif1, col_verif2 = st.columns(2)

with col_verif1:
    st.subheader("🎫 Verificación Registradora")
    if abs(diferencia_registradora) < 0.01:
        st.success(f"✅ ¡CORRECTO! La registradora (${registradora:,.2f}) coincide con los pagos digitales (${pagos_digitales_total:,.2f})")
    else:
        if diferencia_registradora > 0:
            st.error(f"❌ La registradora tiene ${abs(diferencia_registradora):,.2f} MÁS que los pagos digitales")
        else:
            st.error(f"❌ La registradora tiene ${abs(diferencia_registradora):,.2f} MENOS que los pagos digitales")

with col_verif2:
    st.subheader("💰 Verificación Caja")
    if abs(balanza - caja_real - salidas_total) < 0.01:
        st.success("✅ ¡Cierre CORRECTO! La balanza coincide con caja real + salidas")
    else:
        diferencia_final = balanza - (caja_real + salidas_total)
        if diferencia_final > 0:
            st.error(f"❌ FALTAN ${abs(diferencia_final):,.2f} en la caja")
        else:
            st.warning(f"⚠️ SOBRAN ${abs(diferencia_final):,.2f} en la caja")
