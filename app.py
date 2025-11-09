import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Cierre de Caja", layout="wide")

st.title("💰 Sistema de Cierre de Caja")

# Fecha y Caja
col_header1, col_header2 = st.columns(2)
with col_header1:
    fecha = st.date_input("FECHA", value=datetime.now())
with col_header2:
    nombre_caja = st.text_input("CAJA", value="")

st.divider()

# Resto y Somos A
col1, col2 = st.columns(2)
with col1:
    resto_para_ayer = st.number_input("RESTO x OVP (Último)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    st.caption("Dinero que quedó del día anterior")
with col2:
    somos_a = st.number_input("SOMOS A (Dejo Hoy)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    st.caption("Dinero que queda para mañana")

st.divider()

# Vales y Transferencias
col3, col4 = st.columns(2)
with col3:
    vales = st.number_input("VALES", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col4:
    transferencias = st.number_input("TRANSFERENCIAS", min_value=0.0, value=0.0, step=100.0, format="%.2f")

st.divider()

# Registradora, Balanza y Efectivo
st.header("📊 Facturación")
col5, col6, col7 = st.columns(3)
with col5:
    registradora = st.number_input("REGISTRADORA", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
with col6:
    balanza = st.number_input("BALANZA", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
with col7:
    efectivo = st.number_input("EFECTIVO", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

st.divider()

# Pagos Electrónicos
st.header("💳 Pagos Electrónicos")
col8, col9, col10 = st.columns(3)
with col8:
    mercadopago = st.number_input("MERCADO PAGO", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
with col9:
    getnet = st.number_input("GETNET", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
with col10:
    clover = st.number_input("CLOVER (POSNET)", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

st.divider()

# Errores y Salida de Caja
col12, col13 = st.columns(2)
with col12:
    errores = st.number_input("ERRORES", value=0.0, step=100.0, format="%.2f")
    st.caption("Diferencias o ajustes del día")
with col13:
    salida_caja = st.number_input("SALIDA DE CAJA", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    st.caption("Retiros realizados durante el día")

st.divider()

# Caja Real
caja_real_input = st.number_input("CAJA REAL", value=0.0, step=1000.0, format="%.2f")
st.caption("Dinero físico total contado (se mostrará como negativo en el resumen)")

st.divider()

# CÁLCULOS
total_pagos_digitales = mercadopago + getnet + clover
diferencia_registradora = registradora - total_pagos_digitales

# La caja real se muestra negativa en el formato
caja_real = -abs(caja_real_input)

# Suma para verificación: todo lo que ingresó - caja real (que es negativa)
suma_total = vales + transferencias + efectivo + total_pagos_digitales + salida_caja + caja_real

# Efectivo neto del día
efectivo_neto = efectivo - resto_para_ayer

# RESULTADOS
st.header("📈 Resultados del Cierre")

col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.metric("TOTAL PAGOS DIGITALES", f"${total_pagos_digitales:,.2f}")
    if abs(diferencia_registradora) < 0.01:
        st.success("✅ Registradora OK")
    else:
        if diferencia_registradora > 0:
            st.warning(f"⚠️ Registradora tiene ${diferencia_registradora:,.2f} MÁS")
        else:
            st.warning(f"⚠️ Registradora tiene ${abs(diferencia_registradora):,.2f} MENOS")

with col_res2:
    st.metric("RESTO PARA MAÑANA", f"${somos_a:,.2f}")
    st.metric("EFECTIVO NETO (hoy)", f"${efectivo_neto:,.2f}")
    dinero_a_retirar = efectivo_neto - somos_a
    st.metric("💵 DINERO A RETIRAR", f"${dinero_a_retirar:,.2f}")

with col_res3:
    st.metric("SUMA TOTAL", f"${suma_total:,.2f}")
    if abs(suma_total) < 0.01:
        st.success("✅ Caja perfectamente cuadrada")
    elif suma_total > 0:
        st.error(f"❌ FALTAN ${suma_total:,.2f}")
    else:
        st.warning(f"⚠️ SOBRAN ${abs(suma_total):,.2f}")

st.divider()

# TABLA RESUMEN PARA IMPRIMIR
st.header("📋 Resumen para Imprimir")

# HTML para imprimir
html_content = f"""
<style>
    @media print {{
        body {{ margin: 20px; }}
        .no-print {{ display: none; }}
    }}
    .cierre-caja {{
        font-family: 'Courier New', monospace;
        border: 2px solid black;
        padding: 20px;
        max-width: 800px;
        margin: 0 auto;
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        border-bottom: 2px solid black;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }}
    .linea {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px dotted #ccc;
    }}
    .linea.destacado {{
        font-weight: bold;
        background-color: #f0f0f0;
    }}
    .separador {{
        border-top: 2px solid black;
        margin: 15px 0;
    }}
    .titulo-seccion {{
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 5px;
        text-decoration: underline;
    }}
</style>

<div class="cierre-caja">
    <div class="header">
        <div><strong>FECHA:</strong> {fecha.strftime('%d/%m/%Y')}</div>
        <div><strong>CAJA:</strong> {nombre_caja}</div>
    </div>
    
    <div class="linea">
        <span>RESTO x OVP (Último):</span>
        <span>$ {resto_para_ayer:,.2f}</span>
    </div>
    <div class="linea destacado">
        <span>SOMOS A (Dejo Hoy):</span>
        <span>$ {somos_a:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="linea">
        <span>VALES:</span>
        <span>$ {vales:,.2f}</span>
    </div>
    <div class="linea">
        <span>TRANSFERENCIAS:</span>
        <span>$ {transferencias:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="linea destacado">
        <span>REGISTRADORA:</span>
        <span>$ {registradora:,.2f}</span>
    </div>
    <div class="linea destacado">
        <span>BALANZA:</span>
        <span>$ {balanza:,.2f}</span>
    </div>
    <div class="linea destacado">
        <span>EFECTIVO:</span>
        <span>$ {efectivo:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="titulo-seccion">PAGOS ELECTRÓNICOS:</div>
    <div class="linea">
        <span>MERCADO PAGO:</span>
        <span>$ {mercadopago:,.2f}</span>
    </div>
    <div class="linea">
        <span>GETNET:</span>
        <span>$ {getnet:,.2f}</span>
    </div>
    <div class="linea">
        <span>CLOVER:</span>
        <span>$ {clover:,.2f}</span>
    </div>
    <div class="linea destacado">
        <span>TOTAL:</span>
        <span>$ {total_pagos_digitales:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="linea">
        <span>ERRORES:</span>
        <span>$ {errores:,.2f}</span>
    </div>
    <div class="linea">
        <span>SALIDA DE CAJA:</span>
        <span>$ {salida_caja:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="linea destacado">
        <span>CAJA REAL:</span>
        <span>$ {caja_real:,.2f}</span>
    </div>
    
    <div class="separador"></div>
    
    <div class="linea destacado" style="background-color: #e8f4f8;">
        <span>DIFERENCIA REGISTRADORA:</span>
        <span>$ {diferencia_registradora:,.2f}</span>
    </div>
    
    <div class="linea destacado" style="background-color: {'#d4edda' if abs(suma_total) < 0.01 else '#f8d7da'};">
        <span>SUMA TOTAL:</span>
        <span>$ {suma_total:,.2f}</span>
    </div>
</div>
"""

st.markdown(html_content, unsafe_allow_html=True)

# Botón de imprimir
st.markdown('<div class="no-print">', unsafe_allow_html=True)
if st.button("🖨️ IMPRIMIR CIERRE", type="primary", use_container_width=True):
    st.markdown("""
    <script>
    window.print();
    </script>
    """, unsafe_allow_html=True)

st.divider()

# Preparar datos para el día siguiente
st.header("📅 Preparar Caja para Mañana")
fecha_manana = fecha + timedelta(days=1)

st.info(f"""
**Para el cierre del {fecha_manana.strftime('%d/%m/%Y')}:**
- Usar como "RESTO x OVP (Último)": **${somos_a:,.2f}**
- Este monto ya está guardado como el dinero que quedó en caja hoy
- Dinero a retirar hoy: **${dinero_a_retirar:,.2f}**
""")

# Exportar a Excel (opcional)
if st.button("📊 Descargar Resumen en Excel"):
    datos_excel = {
        "Concepto": [
            "FECHA",
            "CAJA",
            "",
            "RESTO x OVP (Último)",
            "SOMOS A (Dejo Hoy)",
            "",
            "VALES",
            "TRANSFERENCIAS",
            "",
            "REGISTRADORA",
            "BALANZA",
            "EFECTIVO",
            "",
            "MERCADO PAGO",
            "GETNET",
            "CLOVER (POSNET)",
            "TOTAL PAGOS DIGITALES",
            "",
            "ERRORES",
            "SALIDA DE CAJA",
            "",
            "CAJA REAL",
            "",
            "DIFERENCIA REGISTRADORA",
            "SUMA TOTAL"
        ],
        "Valor": [
            fecha.strftime('%d/%m/%Y'),
            nombre_caja,
            "",
            f"{resto_para_ayer:,.2f}",
            f"{somos_a:,.2f}",
            "",
            f"{vales:,.2f}",
            f"{transferencias:,.2f}",
            "",
            f"{registradora:,.2f}",
            f"{balanza:,.2f}",
            f"{efectivo:,.2f}",
            "",
            f"{mercadopago:,.2f}",
            f"{getnet:,.2f}",
            f"{clover:,.2f}",
            f"{total_pagos_digitales:,.2f}",
            "",
            f"{errores:,.2f}",
            f"{salida_caja:,.2f}",
            "",
            f"{caja_real:,.2f}",
            "",
            f"{diferencia_registradora:,.2f}",
            f"{suma_total:,.2f}"
        ]
    }
    
    df = pd.DataFrame(datos_excel)
    csv = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="💾 Descargar CSV",
        data=csv,
        file_name=f"cierre_caja_{fecha.strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
st.markdown('</div>', unsafe_allow_html=True)
