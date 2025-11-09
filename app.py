import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

st.set_page_config(page_title="Cierre de Caja", layout="wide", page_icon="💰")

# Estilos personalizados
st.markdown("""
<style>
    .big-metric {
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Cierre de Caja")
st.markdown("---")

# DATOS BÁSICOS
col_fecha, col_caja = st.columns(2)
with col_fecha:
    fecha = st.date_input("📅 Fecha", value=datetime.now())
with col_caja:
    nombre_caja = st.text_input("🏪 Nombre de Caja", placeholder="Ej: Caja Principal")

st.markdown("---")

# SECCIÓN: FACTURACIÓN
st.subheader("📊 Facturación del Día")
col1, col2, col3 = st.columns(3)
with col1:
    balanza = st.number_input("💵 BALANZA (Total Facturado)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col2:
    registradora = st.number_input("🧾 REGISTRADORA (Tickets Fiscales)", min_value=0.0, value=0.0, step=100.0, format="%.2f", help="Solo para comparar con pagos digitales")
with col3:
    somos_a = st.number_input("🎁 SOMOS A (Descuentos)", min_value=0.0, value=0.0, step=10.0, format="%.2f", help="Descuentos aplicados lunes y miércoles")

st.markdown("---")

# SECCIÓN: INGRESOS
st.subheader("💳 Ingresos de Dinero")
col4, col5 = st.columns(2)
with col4:
    cambio_ayer = st.number_input("💵 Cambio de AYER (a restar)", min_value=0.0, value=0.0, step=10.0, format="%.2f", help="Dinero que quedó ayer en la registradora")
    efectivo = st.number_input("💵 EFECTIVO", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    efectivo_neto = efectivo - cambio_ayer
    st.info(f"**Efectivo neto del día:** ${efectivo_neto:,.2f}")

with col5:
    vales = st.number_input("🎫 VALES", min_value=0.0, value=0.0, step=10.0, format="%.2f")
    transferencias = st.number_input("🏦 TRANSFERENCIAS", min_value=0.0, value=0.0, step=100.0, format="%.2f")

st.markdown("**Pagos Electrónicos:**")
col6, col7, col8 = st.columns(3)
with col6:
    mercadopago = st.number_input("📱 MERCADO PAGO", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col7:
    getnet = st.number_input("💳 GETNET", min_value=0.0, value=0.0, step=100.0, format="%.2f")
with col8:
    clover = st.number_input("💳 CLOVER (POSNET)", min_value=0.0, value=0.0, step=100.0, format="%.2f")

st.markdown("---")

# SECCIÓN: AJUSTES
st.subheader("⚙️ Ajustes y Salidas")
col9, col10 = st.columns(2)
with col9:
    errores = st.number_input("⚠️ ERRORES (Ajustes del día)", value=0.0, step=10.0, format="%.2f", help="Errores que surgieron durante el día")
with col10:
    salida_caja = st.number_input("📤 SALIDA DE CAJA", min_value=0.0, value=0.0, step=10.0, format="%.2f", help="Pagos a proveedores, compras, etc.")

st.markdown("---")

# SECCIÓN: CAMBIO PARA MAÑANA
st.subheader("🔄 Cambio para Mañana")
cambio_manana = st.number_input("💵 Dinero que queda para MAÑANA", min_value=0.0, value=0.0, step=10.0, format="%.2f", help="Dinero que quedará en la registradora")

st.markdown("---")

# ============= CÁLCULOS =============
total_pagos_digitales = mercadopago + getnet + clover
total_ingresos = efectivo_neto + mercadopago + getnet + clover + transferencias + vales

# FÓRMULA: CAJA REAL = BALANZA - SOMOS_A - ERRORES - INGRESOS + SALIDAS
caja_real = balanza - somos_a - errores - total_ingresos + salida_caja

# Comparación registradora vs pagos digitales
diferencia_registradora = registradora - total_pagos_digitales

dinero_a_retirar = efectivo_neto - cambio_manana

# ============= RESULTADOS =============
st.header("📈 RESULTADO DEL CIERRE")

# Métrica principal: CAJA REAL
if abs(caja_real) < 0.01:
    st.success("## ✅ ¡CAJA PERFECTA!")
    color_caja = "success"
elif caja_real < 0:
    st.warning(f"## ⚠️ SOBRAN ${abs(caja_real):,.2f}")
    color_caja = "warning"
else:
    st.error(f"## ❌ FALTAN ${caja_real:,.2f}")
    color_caja = "error"

st.markdown("---")

# Métricas adicionales
col_res1, col_res2, col_res3, col_res4 = st.columns(4)

with col_res1:
    st.metric("💰 Caja Real", f"${caja_real:,.2f}")
    
with col_res2:
    st.metric("💵 Efectivo Neto", f"${efectivo_neto:,.2f}")
    st.metric("💰 A Retirar Hoy", f"${dinero_a_retirar:,.2f}")

with col_res3:
    st.metric("💳 Pagos Digitales", f"${total_pagos_digitales:,.2f}")
    if abs(diferencia_registradora) < 0.01:
        st.success("✅ Registradora OK")
    else:
        st.info(f"ℹ️ Dif: ${diferencia_registradora:,.2f}")

with col_res4:
    st.metric("📊 Total Ingresos", f"${total_ingresos:,.2f}")
    st.metric("💵 Cambio Mañana", f"${cambio_manana:,.2f}")

st.markdown("---")

# ============= GENERAR PDF =============
def generar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('TituloCustom', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1f77b4'), spaceAfter=20, alignment=1)
    
    # Título
    titulo = Paragraph(f"<b>CIERRE DE CAJA</b>", titulo_style)
    elementos.append(titulo)
    
    fecha_texto = Paragraph(f"<b>Fecha:</b> {fecha.strftime('%d/%m/%Y')} | <b>Caja:</b> {nombre_caja}", styles['Normal'])
    elementos.append(fecha_texto)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Tabla de datos
    datos = [
        ['CONCEPTO', 'VALOR'],
        ['', ''],
        ['BALANZA', f'$ {balanza:,.2f}'],
        ['REGISTRADORA', f'$ {registradora:,.2f}'],
        ['SOMOS A (Descuentos)', f'$ {somos_a:,.2f}'],
        ['', ''],
        ['EFECTIVO', f'$ {efectivo:,.2f}'],
        ['Cambio de ayer', f'$ -{cambio_ayer:,.2f}'],
        ['EFECTIVO NETO', f'$ {efectivo_neto:,.2f}'],
        ['', ''],
        ['MERCADO PAGO', f'$ {mercadopago:,.2f}'],
        ['GETNET', f'$ {getnet:,.2f}'],
        ['CLOVER (POSNET)', f'$ {clover:,.2f}'],
        ['TOTAL PAGOS DIGITALES', f'$ {total_pagos_digitales:,.2f}'],
        ['', ''],
        ['TRANSFERENCIAS', f'$ {transferencias:,.2f}'],
        ['VALES', f'$ {vales:,.2f}'],
        ['', ''],
        ['ERRORES', f'$ {errores:,.2f}'],
        ['SALIDA DE CAJA', f'$ {salida_caja:,.2f}'],
        ['', ''],
        ['DIFERENCIA REGISTRADORA', f'$ {diferencia_registradora:,.2f}'],
        ['', ''],
        ['CAMBIO PARA MAÑANA', f'$ {cambio_manana:,.2f}'],
        ['DINERO A RETIRAR HOY', f'$ {dinero_a_retirar:,.2f}'],
        ['', ''],
        ['═══════════════', '═══════════════'],
        ['CAJA REAL', f'$ {caja_real:,.2f}'],
    ]
    
    tabla = Table(datos, colWidths=[3.5*inch, 2*inch])
    
    # Estilo de la tabla
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda') if abs(caja_real) < 0.01 else colors.HexColor('#f8d7da')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f0f0')]),
    ])
    
    tabla.setStyle(estilo_tabla)
    elementos.append(tabla)
    
    # Estado de la caja
    elementos.append(Spacer(1, 0.3*inch))
    if abs(caja_real) < 0.01:
        estado = Paragraph("<b style='color: green; font-size: 16px;'>✅ CAJA PERFECTA</b>", styles['Normal'])
    elif caja_real < 0:
        estado = Paragraph(f"<b style='color: orange; font-size: 16px;'>⚠️ SOBRAN $ {abs(caja_real):,.2f}</b>", styles['Normal'])
    else:
        estado = Paragraph(f"<b style='color: red; font-size: 16px;'>❌ FALTAN $ {caja_real:,.2f}</b>", styles['Normal'])
    
    elementos.append(estado)
    
    doc.build(elementos)
    buffer.seek(0)
    return buffer

# Botón de descarga PDF
st.subheader("📥 Descargar Cierre")
if st.button("📄 Generar PDF", type="primary", use_container_width=True):
    pdf_buffer = generar_pdf()
    st.download_button(
        label="💾 Descargar PDF",
        data=pdf_buffer,
        file_name=f"cierre_caja_{fecha.strftime('%Y%m%d')}_{nombre_caja.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )

# Nota para el día siguiente
st.markdown("---")
st.info(f"""
### 📌 Para mañana ({(fecha + datetime.timedelta(days=1)).strftime('%d/%m/%Y')}):
- **Cambio de ayer:** ${cambio_manana:,.2f}
- **Dinero a retirar hoy:** ${dinero_a_retirar:,.2f}
""")
