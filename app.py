import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y LOGIN ---
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered")

# ESCUDO ANTI-CIERRE ACCIDENTAL
js_warning = """
<script>
    window.addEventListener("beforeunload", function (e) {
        var confirmationMessage = 'Es posible que los cambios no se guarden.';
        (e || window.event).returnValue = confirmationMessage; 
        return confirmationMessage;
    });
</script>
"""
components.html(js_warning, height=0)

# ── ESTILOS PERSONALIZADOS ────────────────────────────────────────────────────
hide_st_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Lato:wght@300;400;700&display=swap');

/* Variables de paleta */
:root {
    --verde-oscuro: #2E4A2E;
    --verde-medio: #3D6B3D;
    --crema:        #F5F0E8;
    --arena:        #E8DCC8;
    --miel:         #C8954A;
    --miel-claro:   #E8B96A;
    --texto-oscuro: #1A2E1A;
    --texto-medio:  #4A5E4A;
    --blanco:       #FFFFFF;
    --sombra:       rgba(46,74,46,0.12);
}

/* Fondo general */
.stApp {
    background-color: var(--crema);
    background-image: 
        radial-gradient(ellipse at 10% 0%, rgba(200,149,74,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 90% 100%, rgba(46,74,46,0.06) 0%, transparent 60%);
    font-family: 'Lato', sans-serif;
}

/* Ocultar elementos default */
#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}
header    {visibility: hidden;}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 820px;
}

/* ── TÍTULO PRINCIPAL ── */
h1 {
    font-family: 'Playfair Display', serif !important;
    color: var(--verde-oscuro) !important;
    font-size: 2.2rem !important;
    letter-spacing: 0.02em;
    margin-bottom: 0.2rem !important;
}

/* Subtítulo debajo del h1 */
.subtitulo-app {
    font-family: 'Lato', sans-serif;
    color: var(--miel);
    font-size: 0.85rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* ── CABECERA DECORATIVA ── */
.header-divider {
    border: none;
    border-top: 2px solid var(--miel);
    margin: 0.5rem 0 1.8rem 0;
    opacity: 0.6;
}

/* ── TARJETAS DE SECCIÓN ── */
.seccion-card {
    background: var(--blanco);
    border-radius: 12px;
    border: 1px solid var(--arena);
    padding: 1.4rem 1.6rem 1rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 12px var(--sombra);
}

.seccion-titulo {
    font-family: 'Playfair Display', serif;
    color: var(--verde-oscuro);
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.seccion-titulo .icono {
    background: var(--verde-oscuro);
    color: var(--blanco);
    border-radius: 6px;
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
    font-family: 'Lato', sans-serif;
}

/* ── LABELS ── */
.stSelectbox label,
.stNumberInput label,
.stDateInput label,
.stTextInput label {
    font-family: 'Lato', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    color: var(--verde-medio) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── INPUTS ── */
.stTextInput input,
.stNumberInput input,
.stSelectbox select,
.stDateInput input {
    border-radius: 8px !important;
    border: 1.5px solid var(--arena) !important;
    background: var(--crema) !important;
    color: var(--texto-oscuro) !important;
    font-family: 'Lato', sans-serif !important;
    transition: border-color 0.2s;
}
.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: var(--miel) !important;
    box-shadow: 0 0 0 3px rgba(200,149,74,0.15) !important;
}

/* ── BOTONES ── */
.stButton > button {
    font-family: 'Lato', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.1rem !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase;
}

/* Botón primario (Guardar en Drive) */
div[data-testid="column"]:nth-child(2) .stButton > button {
    background: var(--verde-oscuro) !important;
    color: var(--blanco) !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(46,74,46,0.25) !important;
}
div[data-testid="column"]:nth-child(2) .stButton > button:hover {
    background: var(--verde-medio) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 14px rgba(46,74,46,0.3) !important;
}

/* Botón secundario (Generar PDF) */
div[data-testid="column"]:nth-child(3) .stButton > button {
    background: transparent !important;
    color: var(--verde-oscuro) !important;
    border: 2px solid var(--verde-oscuro) !important;
}
div[data-testid="column"]:nth-child(3) .stButton > button:hover {
    background: var(--verde-oscuro) !important;
    color: var(--blanco) !important;
    transform: translateY(-1px) !important;
}

/* Botón de descarga */
.stDownloadButton > button {
    background: var(--miel) !important;
    color: var(--blanco) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-size: 0.82rem !important;
}
.stDownloadButton > button:hover {
    background: var(--miel-claro) !important;
    transform: translateY(-1px) !important;
}

/* ── METRIC (diferencia) ── */
div[data-testid="metric-container"] {
    background: var(--verde-oscuro);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    color: var(--blanco);
    box-shadow: 0 4px 16px rgba(46,74,46,0.2);
}
div[data-testid="metric-container"] label {
    color: var(--arena) !important;
    font-family: 'Lato', sans-serif !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}
div[data-testid="metric-container"] [data-testid="metric-value"] {
    color: var(--blanco) !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.6rem !important;
}

/* ── DATA EDITOR ── */
.stDataEditor {
    border-radius: 8px !important;
    border: 1px solid var(--arena) !important;
    overflow: hidden;
}
.stDataEditor [data-testid="data-grid-canvas"] {
    background: var(--blanco) !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: var(--crema) !important;
    border-radius: 8px !important;
    font-family: 'Lato', sans-serif !important;
    color: var(--verde-oscuro) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}

/* ── CAPTION ── */
.stCaption {
    color: var(--miel) !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
}

/* ── SEPARADOR ── */
hr {
    border-color: var(--arena) !important;
    margin: 1.5rem 0 !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    border-radius: 8px !important;
    border-color: var(--arena) !important;
    background: var(--crema) !important;
}

/* ── RESULTADO DEL CIERRE ── */
.resultado-header {
    font-family: 'Playfair Display', serif;
    color: var(--verde-oscuro);
    font-size: 1.3rem;
    font-weight: 700;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--miel);
    margin-bottom: 1.2rem;
}

/* ── TOTALES PILLBOX ── */
.totales-row {
    display: flex;
    gap: 0.8rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.totales-pill {
    background: var(--verde-oscuro);
    color: var(--crema);
    border-radius: 20px;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    font-family: 'Lato', sans-serif;
    font-weight: 700;
    letter-spacing: 0.05em;
}
.totales-pill span {
    color: var(--miel-claro);
}

/* ── LOGIN PAGE ── */
.login-container h1 {
    font-family: 'Playfair Display', serif !important;
}

/* ── SUCCESS / ERROR ── */
.stAlert {
    border-radius: 10px !important;
    font-family: 'Lato', sans-serif !important;
}

/* Numbros digitales más grandes */
.cobros-digitales-total {
    font-family: 'Playfair Display', serif;
    color: var(--verde-oscuro);
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 0.5rem;
}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("""
        <div style='text-align:center; padding: 3rem 0 1rem 0;'>
            <div style='font-family: Playfair Display, serif; font-size: 2rem; color: #2E4A2E; font-weight: 700;'>
                Estancia San Francisco
            </div>
            <div style='font-family: Lato, sans-serif; font-size: 0.78rem; color: #C8954A; 
                        letter-spacing: 0.2em; text-transform: uppercase; margin-top: 0.3rem;'>
                Sistema de Cierre de Caja
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.text_input("Contraseña del local", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Contraseña incorrecta")
    return False

if not check_password():
    st.stop()

# --- CONEXIÓN GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Error de conexión con Google Sheets")

# --- 2. CARGA DE DATOS MAESTROS ---
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
lista_empleados = ["Santiago", "Julieta", "Mariela", "Fernanda", "Brian", "Erika", "Oriana"]

df_directorio = pd.DataFrame()
if 'conn' in globals():
    try:
        df_directorio = conn.read(worksheet="Directorio", ttl=600)
        if not df_directorio.empty and "Proveedor" in df_directorio.columns:
            lista_proveedores = df_directorio["Proveedor"].dropna().unique().tolist()
            if "Otro" not in lista_proveedores: lista_proveedores.append("Otro")
    except:
        pass

# --- 3. VARIABLES DE SESIÓN ---
session_keys = {
    'df_salidas': ["Descripción", "Monto"],
    'df_transferencias': ["Monto"],
    'df_vales': ["Descripción", "Monto"],
    'df_errores': ["Monto"],
    'df_descuentos': ["Monto"],
    'df_proveedores': ["Proveedor", "Forma Pago", "Nro Factura", "Monto"],
    'df_empleados': ["Empleado", "Monto"]
}

for key, cols in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)

# --- 4. FUNCIONES DE GUARDADO ---
def guardar_todo_en_nube(datos_cierre, df_provs, df_empls):
    try:
        df_historial = conn.read(worksheet="Historial")
        fila_cierre = pd.DataFrame([datos_cierre])
        df_historial_upd = pd.concat([df_historial, fila_cierre], ignore_index=True).fillna("")
        conn.update(worksheet="Historial", data=df_historial_upd)
        
        pagos_reales = df_provs[df_provs["Monto"] > 0].copy()
        if not pagos_reales.empty:
            pagos_reales["Fecha"] = datos_cierre["Fecha"]
            pagos_reales["Cajero"] = datos_cierre["Cajero"]
            df_pagos_ant = conn.read(worksheet="Pagos_Proveedores")
            df_pagos_upd = pd.concat([df_pagos_ant, pagos_reales], ignore_index=True).fillna("")
            conn.update(worksheet="Pagos_Proveedores", data=df_pagos_upd)

        consumos_empl = df_empls[df_empls["Monto"] > 0].copy()
        if not consumos_empl.empty:
            consumos_empl["Fecha"] = datos_cierre["Fecha"]
            consumos_empl = consumos_empl[["Fecha", "Empleado", "Monto"]]
            df_empl_ant = conn.read(worksheet="Consumo_Empleados")
            df_empl_upd = pd.concat([df_empl_ant, consumos_empl], ignore_index=True).fillna("")
            conn.update(worksheet="Consumo_Empleados", data=df_empl_upd)
            
        return True
    except Exception as e:
        st.error(f"Error guardando en nube: {e}")
        return False

# --- 5. FUNCIÓN PDF ---
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto, 
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, 
                            df_proveedores, df_empleados, diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    fecha_texto = f"{dias_semana[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"

    pdf.set_xy(50, 12); pdf.set_font("Arial", 'B', 18); pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10); pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R')
    pdf.set_x(130); pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R')
    pdf.ln(15); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(3)

    def dibujar_kpi(titulo, monto):
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"{titulo}: $ {monto:,.2f}", ln=1, align='C', fill=True, border=1)
        pdf.ln(2) 

    dibujar_kpi("1. BALANZA", balanza)
    dibujar_kpi("2. EFECTIVO", efectivo_neto)
    dibujar_kpi("3. DIGITAL", total_digital)
    
    pdf.ln(2); pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {registradora:,.2f}", border=0, align='C', ln=1)
    pdf.ln(5)

    def dibujar_tabla(titulo, df, label_fijo=None):
        if df.empty or df['Monto'].sum() == 0: return
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 9)
        for _, row in df.iterrows():
            if row['Monto'] > 0:
                txt = str(row.get('Descripción', row.get('Empleado', label_fijo)))
                pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    dibujar_tabla("MERCADERÍA EMPLEADOS", df_empleados)
    dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transferencias, label_fijo="Transferencia")
    dibujar_tabla("GASTOS VARIOS / SALIDAS", df_salidas)
    dibujar_tabla("VALES / FIADOS", df_vales)
    
    pdf.ln(5)
    estado, color_texto = ("FALTANTE", (200, 0, 0)) if diferencia > 0 else ("SOBRANTE", (0, 100, 0))
    if diferencia == 0: estado, color_texto = ("OK", (0, 0, 0))
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color_texto)
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1)
    
    return pdf.output(dest="S").encode("latin-1")

# ── HELPERS UI ────────────────────────────────────────────────────────────────
def seccion(numero, titulo):
    """Renderiza el encabezado de una sección tipo tarjeta."""
    st.markdown(f"""
        <div class="seccion-titulo">
            <span class="icono">{numero}</span>
            {titulo}
        </div>
    """, unsafe_allow_html=True)

def input_tabla(titulo, key, solo_monto=False):
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)}
    if not solo_monto: cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}")
    return df, (df["Monto"].sum() if not df.empty else 0.0)

# ══════════════════════════════════════════════════════════════════════════════
#  ENCABEZADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
    <div style='margin-bottom: 0.2rem;'>
        <h1 style='margin-bottom:0;'>Estancia San Francisco</h1>
        <div class='subtitulo-app'>✦ Cierre de Caja Diario ✦</div>
    </div>
    <hr class='header-divider'>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 1 — ENCABEZADO DEL CIERRE
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("1", "Datos del Turno")
    col_enc1, col_enc2 = st.columns(2)
    with col_enc1:
        fecha_input = st.date_input("Fecha", datetime.today())
    with col_enc2:
        cajero = st.selectbox("Cajero de Turno", lista_empleados)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 2 — VALES Y TRANSFERENCIAS
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("2", "Vales / Fiados")
    df_vales, total_vales = input_tabla("", "df_vales")
    if total_vales > 0:
        st.caption(f"Total Vales: ${total_vales:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("3", "Transferencias Entrantes")
    df_transferencias, total_transf_in = input_tabla("", "df_transferencias", solo_monto=True)
    if total_transf_in > 0:
        st.caption(f"Total Transferencias: ${total_transf_in:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 3 — MERCADERÍA EMPLEADOS
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("4", "Mercadería de Empleados")
    cfg_emp = {
        "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True),
        "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0)
    }
    df_empleados = st.data_editor(
        st.session_state.df_empleados, column_config=cfg_emp,
        num_rows="dynamic", use_container_width=True, key="ed_emp"
    )
    total_empleados = df_empleados["Monto"].sum()
    if total_empleados > 0:
        st.caption(f"Total Empleados: ${total_empleados:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 4 — EFECTIVO Y COBROS DIGITALES
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("5", "Ingresos del Día")

    col_core1, col_core2 = st.columns(2)
    with col_core1:
        balanza_total     = st.number_input("Total Balanza (Venta Real)", 0.0, step=100.0)
        registradora_total = st.number_input("Registradora — Ticket Z", 0.0, step=100.0)

    with col_core2:
        with st.expander("🧮  Calculadora de Billetes", expanded=False):
            b20k = st.number_input("$20.000", 0)
            b10k = st.number_input("$10.000", 0)
            b2k  = st.number_input("$2.000",  0)
            b1k  = st.number_input("$1.000",  0)
            total_fisico = (b20k * 20000) + (b10k * 10000) + (b2k * 2000) + (b1k * 1000)
            if total_fisico > 0:
                st.caption(f"Subtotal billetes: ${total_fisico:,.2f}")
        efectivo_neto = st.number_input("Efectivo Total en Caja", value=float(total_fisico))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Cobros Digitales**")
    cd1, cd2, cd3, cd4 = st.columns(4)
    mp     = cd1.number_input("Mercado Pago", 0.0, step=100.0)
    nave   = cd2.number_input("Nave",         0.0, step=100.0)
    clover = cd3.number_input("Clover",        0.0, step=100.0)
    bbva   = cd4.number_input("BBVA",          0.0, step=100.0)
    total_digital = mp + nave + clover + bbva

    if total_digital > 0:
        st.caption(f"Total Digital: ${total_digital:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SECCIÓN 5 — PROVEEDORES Y SALIDAS
# ══════════════════════════════════════════════════════════════════════════════
with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("6", "Pago a Proveedores")
    cfg_prov = {
        "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True),
        "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"], required=True),
        "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0)
    }
    df_proveedores = st.data_editor(
        st.session_state.df_proveedores, column_config=cfg_prov,
        num_rows="dynamic", use_container_width=True, key="ed_prov"
    )
    total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum()
    if total_prov_efectivo > 0:
        st.caption(f"Total Proveedores (efectivo): ${total_prov_efectivo:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="seccion-card">', unsafe_allow_html=True)
    seccion("7", "Gastos Varios — Salidas de Caja")
    df_salidas, total_salidas = input_tabla("", "df_salidas")
    if total_salidas > 0:
        st.caption(f"Total Salidas: ${total_salidas:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  RESULTADO FINAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="resultado-header">Resultado del Cierre</div>', unsafe_allow_html=True)

total_justificado = (total_digital + efectivo_neto + total_transf_in
                     + total_salidas + total_prov_efectivo + total_vales + total_empleados)
diferencia = balanza_total - total_justificado

c1, c2, c3 = st.columns(3)
c1.metric("Diferencia de Caja", f"${diferencia:,.2f}", delta_color="inverse" if diferencia > 0 else "normal")

if c2.button("💾  Guardar en Drive", use_container_width=True):
    datos = {
        "Fecha": fecha_input.strftime("%d/%m/%Y"), "Cajero": cajero, "Balanza": balanza_total,
        "Digital": total_digital, "Efectivo": efectivo_neto, "Diferencia": diferencia
    }
    if guardar_todo_en_nube(datos, df_proveedores, df_empleados):
        st.success("✅  Cierre guardado exitosamente en Drive.")
        st.balloons()

if c3.button("📄  Generar PDF", use_container_width=True):
    desglose = {"MP": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
    pdf_bytes = generar_pdf_profesional(
        fecha_input, cajero, balanza_total, registradora_total,
        total_digital, efectivo_neto, df_salidas, df_transferencias,
        pd.DataFrame(), df_vales, pd.DataFrame(), df_proveedores,
        df_empleados, diferencia, desglose
    )
    st.download_button("⬇️  Descargar PDF", pdf_bytes, f"Cierre_{fecha_input}.pdf", "application/pdf")
