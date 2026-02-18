import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y LOGIN ---
st.set_page_config(
    page_title="Cierre de Caja - Estancia San Francisco",
    layout="wide",
    page_icon="🏡"
)

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

# =============================================
# ESTILO VISUAL - ESTANCIA SAN FRANCISCO
# Paleta: Verde oscuro + Dorado + Crema/Marfil
# Tipografía: Serif elegante (Playfair Display)
# Estética: Artesanal premium / campo / delicatessen
# =============================================
esf_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Lato:wght@300;400;600&display=swap');

:root {
    --verde-oscuro:    #1A3A2A;
    --verde-medio:     #2C5F3E;
    --verde-claro:     #3D7A52;
    --dorado:          #C8993A;
    --dorado-claro:    #E8B85A;
    --crema:           #F5EDD8;
    --crema-oscuro:    #EAD9B8;
    --marfil:          #FAF6EE;
    --texto-oscuro:    #1A1A1A;
    --texto-medio:     #3D3D3D;
    --texto-suave:     #7A7060;
    --rojo-error:      #8B2020;
    --verde-ok:        #1A5C2A;
}

/* ── RESET GENERAL ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: var(--marfil);
    font-family: 'Lato', sans-serif;
    color: var(--texto-oscuro);
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 1200px;
}

/* ── HEADER PRINCIPAL ── */
.esf-header {
    background: linear-gradient(135deg, var(--verde-oscuro) 0%, var(--verde-medio) 70%, var(--verde-claro) 100%);
    padding: 2rem 3rem;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 4px solid var(--dorado);
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}

.esf-header-left {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.esf-escudo {
    width: 64px;
    height: 64px;
    background: var(--dorado);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    flex-shrink: 0;
}

.esf-titulo {
    font-family: 'Playfair Display', serif;
    color: var(--crema) !important;
    font-size: 1.9rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    line-height: 1.1;
    letter-spacing: 0.5px;
}

.esf-subtitulo {
    color: var(--dorado-claro);
    font-size: 0.85rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.2rem;
    font-weight: 300;
}

.esf-fecha-badge {
    background: rgba(255,255,255,0.1);
    border: 1px solid var(--dorado);
    border-radius: 6px;
    padding: 0.6rem 1.2rem;
    color: var(--crema);
    font-family: 'Playfair Display', serif;
    font-size: 0.95rem;
    text-align: right;
}

.esf-fecha-badge span {
    display: block;
    color: var(--dorado-claro);
    font-size: 0.7rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-family: 'Lato', sans-serif;
    font-weight: 300;
}

/* ── SECCIONES ── */
.esf-seccion {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--verde-oscuro);
    color: var(--crema);
    padding: 0.6rem 1.2rem;
    border-radius: 6px;
    margin: 1.8rem 0 0.8rem 0;
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    border-left: 4px solid var(--dorado);
    box-shadow: 0 2px 8px rgba(26,58,42,0.2);
}

.esf-seccion-icono {
    font-size: 1.1rem;
}

/* ── PANEL RESULTADO ── */
.esf-resultado-panel {
    background: var(--verde-oscuro);
    border: 2px solid var(--dorado);
    border-radius: 10px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 6px 24px rgba(26,58,42,0.3);
}

.esf-resultado-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.esf-kpi {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(200,153,58,0.3);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}

.esf-kpi-label {
    color: var(--dorado-claro);
    font-size: 0.7rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.esf-kpi-valor {
    color: var(--crema);
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    font-weight: 700;
}

.esf-diferencia {
    text-align: center;
    padding: 1.2rem;
    border-radius: 8px;
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.esf-diferencia.ok {
    background: rgba(26,92,42,0.4);
    border: 2px solid #4CAF50;
    color: #81C784;
}

.esf-diferencia.faltante {
    background: rgba(139,32,32,0.4);
    border: 2px solid #EF5350;
    color: #EF9A9A;
}

.esf-diferencia.sobrante {
    background: rgba(26,58,42,0.6);
    border: 2px solid var(--dorado);
    color: var(--dorado-claro);
}

/* ── INPUTS ── */
.stNumberInput input,
.stTextInput input,
.stSelectbox > div > div {
    border-radius: 5px !important;
    border-color: var(--crema-oscuro) !important;
    background: white !important;
}

.stNumberInput input:focus,
.stTextInput input:focus {
    border-color: var(--verde-medio) !important;
    box-shadow: 0 0 0 2px rgba(44,95,62,0.2) !important;
}

/* ── DATA EDITOR ── */
.stDataFrame,
.stDataEditor {
    border: 1px solid var(--crema-oscuro);
    border-radius: 6px;
    overflow: hidden;
}

/* ── BOTONES ── */
.stButton > button {
    background: var(--verde-oscuro) !important;
    color: var(--crema) !important;
    border: 1px solid var(--dorado) !important;
    border-radius: 5px !important;
    font-family: 'Lato', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase !important;
    font-size: 0.82rem !important;
}

.stButton > button:hover {
    background: var(--verde-medio) !important;
    border-color: var(--dorado-claro) !important;
    box-shadow: 0 3px 12px rgba(26,58,42,0.3) !important;
    transform: translateY(-1px) !important;
}

/* Botón de descarga */
.stDownloadButton > button {
    background: var(--dorado) !important;
    color: var(--verde-oscuro) !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    font-size: 0.82rem !important;
}

.stDownloadButton > button:hover {
    background: var(--dorado-claro) !important;
    transform: translateY(-1px) !important;
}

/* ── EXPANDER ── */
.stExpander {
    border: 1px solid var(--crema-oscuro) !important;
    border-radius: 6px !important;
    background: white;
}

.stExpander > div > div > div > div {
    color: var(--verde-oscuro) !important;
    font-weight: 600;
}

/* ── MÉTRICAS ── */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid var(--crema-oscuro);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

[data-testid="metric-container"] label {
    color: var(--texto-suave) !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}

[data-testid="metric-container"] [data-testid="metric-value"] {
    color: var(--verde-oscuro) !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.4rem !important;
}

/* ── SELECTBOX / INPUTS LABELS ── */
label {
    color: var(--texto-medio) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px;
}

/* ── CAPTION ── */
.stCaption {
    color: var(--texto-suave) !important;
    font-style: italic;
}

/* ── ALERTS ── */
.stSuccess {
    background: rgba(26,92,42,0.1) !important;
    border-color: var(--verde-claro) !important;
}

.stError {
    background: rgba(139,32,32,0.1) !important;
}

/* ── DIVISOR DECORATIVO ── */
.esf-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--dorado), transparent);
    margin: 1.5rem 0;
}

/* ── LOGIN PAGE ── */
.esf-login-container {
    max-width: 420px;
    margin: 4rem auto;
    background: white;
    border-radius: 12px;
    padding: 3rem 2.5rem;
    border: 1px solid var(--crema-oscuro);
    box-shadow: 0 8px 32px rgba(26,58,42,0.12);
    text-align: center;
}

.esf-login-escudo {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}

.esf-login-titulo {
    font-family: 'Playfair Display', serif;
    color: var(--verde-oscuro);
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}

.esf-login-sub {
    color: var(--texto-suave);
    font-size: 0.85rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
</style>
"""
st.markdown(esf_style, unsafe_allow_html=True)


# ── SISTEMA DE LOGIN ──────────────────────────────────────────────
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
        <div class="esf-login-container">
            <div class="esf-login-escudo">🏡</div>
            <div class="esf-login-titulo">Estancia San Francisco</div>
            <div class="esf-login-sub">Sistema de Cierre de Caja</div>
        </div>
    """, unsafe_allow_html=True)

    col_c, col_inp, col_d = st.columns([1, 2, 1])
    with col_inp:
        st.text_input("Contraseña de acceso", type="password",
                      on_change=password_entered, key="password",
                      placeholder="Ingresá la contraseña...")
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Contraseña incorrecta. Intentá de nuevo.")
    return False

if not check_password():
    st.stop()


# ── CONEXIÓN GOOGLE SHEETS ────────────────────────────────────────
conn = None
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Error de conexión con Google Sheets: {e}")


# ── DATOS MAESTROS ────────────────────────────────────────────────
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira",
                     "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
lista_empleados = ["Santiago", "Julieta", "Mariela", "Fernanda",
                   "Brian", "Erika", "Oriana"]

if conn is not None:
    try:
        df_directorio = conn.read(worksheet="Directorio", ttl=600)
        if not df_directorio.empty and "Proveedor" in df_directorio.columns:
            lista_proveedores = df_directorio["Proveedor"].dropna().unique().tolist()
            if "Otro" not in lista_proveedores:
                lista_proveedores.append("Otro")
    except Exception as e:
        st.warning(f"No se pudo cargar el directorio de proveedores: {e}")


# ── VARIABLES DE SESIÓN ───────────────────────────────────────────
session_keys = {
    'df_salidas':        ["Descripción", "Monto"],
    'df_transferencias': ["Monto"],
    'df_vales':          ["Descripción", "Monto"],
    'df_proveedores':    ["Proveedor", "Forma Pago", "Nro Factura", "Monto"],
    'df_empleados':      ["Empleado", "Monto"],
}
for key, cols in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)


# ── FUNCIONES GUARDADO ────────────────────────────────────────────
def guardar_historial(datos_cierre):
    df_historial = conn.read(worksheet="Historial")
    fila = pd.DataFrame([datos_cierre])
    df_upd = pd.concat([df_historial, fila], ignore_index=True).fillna("")
    conn.update(worksheet="Historial", data=df_upd)

def guardar_proveedores(df_provs, datos_cierre):
    pagos = df_provs[df_provs["Monto"] > 0].copy()
    if pagos.empty:
        return
    pagos["Fecha"] = datos_cierre["Fecha"]
    pagos["Cajero"] = datos_cierre["Cajero"]
    df_ant = conn.read(worksheet="Pagos_Proveedores")
    df_upd = pd.concat([df_ant, pagos], ignore_index=True).fillna("")
    conn.update(worksheet="Pagos_Proveedores", data=df_upd)

def guardar_empleados(df_empls, datos_cierre):
    consumos = df_empls[df_empls["Monto"] > 0].copy()
    if consumos.empty:
        return
    consumos["Fecha"] = datos_cierre["Fecha"]
    consumos = consumos[["Fecha", "Empleado", "Monto"]]
    df_ant = conn.read(worksheet="Consumo_Empleados")
    df_upd = pd.concat([df_ant, consumos], ignore_index=True).fillna("")
    conn.update(worksheet="Consumo_Empleados", data=df_upd)

def guardar_todo_en_nube(datos_cierre, df_provs, df_empls):
    try:
        guardar_historial(datos_cierre)
        guardar_proveedores(df_provs, datos_cierre)
        guardar_empleados(df_empls, datos_cierre)
        return True
    except Exception as e:
        st.error(f"Error al guardar en la nube: {e}")
        return False


# ── FUNCIÓN PDF ───────────────────────────────────────────────────
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital,
                            efectivo_neto, df_salidas, df_transferencias,
                            df_vales, df_proveedores, df_empleados,
                            diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    if os.path.exists("logo.png"):
        try:
            pdf.image("logo.png", 15, 10, 30)
        except Exception:
            pass

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    fecha_texto = f"{dias_semana[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"

    # Encabezado
    pdf.set_xy(50, 12)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
    pdf.set_xy(130, 12)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R')
    pdf.set_x(130)
    pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R')
    pdf.ln(15)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)

    def dibujar_kpi(titulo, monto):
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"{titulo}: $ {monto:,.2f}", ln=1, align='C', fill=True, border=1)
        pdf.ln(2)

    dibujar_kpi("1. BALANZA", balanza)
    dibujar_kpi("2. EFECTIVO", efectivo_neto)
    dibujar_kpi("3. DIGITAL", total_digital)
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {registradora:,.2f}", border=0, align='C', ln=1)
    pdf.ln(5)

    def dibujar_tabla(titulo, df, label_fijo=None):
        if df.empty or df['Monto'].sum() == 0:
            return
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True)
        pdf.set_font("Arial", '', 9)
        for _, row in df.iterrows():
            if row['Monto'] > 0:
                txt = str(row.get('Descripción', row.get('Empleado', label_fijo)))
                pdf.cell(130, 5, f"      - {txt}")
                pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    dibujar_tabla("MERCADERÍA EMPLEADOS", df_empleados)
    dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transferencias, label_fijo="Transferencia")
    dibujar_tabla("GASTOS VARIOS / SALIDAS", df_salidas)
    dibujar_tabla("VALES / FIADOS", df_vales)

    pdf.ln(5)
    if diferencia > 0:
        estado, color_texto = "FALTANTE", (200, 0, 0)
    elif diferencia < 0:
        estado, color_texto = "SOBRANTE", (0, 100, 0)
    else:
        estado, color_texto = "OK ✓", (0, 0, 0)

    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*color_texto)
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1)

    return pdf.output(dest="S").encode("latin-1")


# ── HELPERS UI ────────────────────────────────────────────────────
def seccion(titulo, icono=""):
    st.markdown(f"""
        <div class="esf-seccion">
            <span class="esf-seccion-icono">{icono}</span>
            {titulo}
        </div>
    """, unsafe_allow_html=True)

def divider():
    st.markdown('<hr class="esf-divider">', unsafe_allow_html=True)

def input_tabla(titulo, key, solo_monto=False):
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)}
    if not solo_monto:
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    df = st.data_editor(
        st.session_state[key],
        column_config=cfg,
        num_rows="dynamic",
        use_container_width=True,
        key=f"ed_{key}"
    )
    total = df["Monto"].sum() if not df.empty else 0.0
    st.caption(f"Subtotal: **${total:,.2f}**")
    return df, total


# ════════════════════════════════════════════════════════
#  INTERFAZ PRINCIPAL
# ════════════════════════════════════════════════════════

# ── HEADER ───────────────────────────────────────────────────────
hoy = datetime.today()
dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_texto = f"{dias_es[hoy.weekday()]}, {hoy.strftime('%d/%m/%Y')}"

st.markdown(f"""
    <div class="esf-header">
        <div class="esf-header-left">
            <div class="esf-escudo">🏡</div>
            <div>
                <div class="esf-titulo">Estancia San Francisco</div>
                <div class="esf-subtitulo">Sistema de Cierre de Caja</div>
            </div>
        </div>
        <div class="esf-fecha-badge">
            <span>Fecha del sistema</span>
            {dia_texto}
        </div>
    </div>
""", unsafe_allow_html=True)


# ── SECCIÓN 1: DATOS DEL TURNO ────────────────────────────────────
seccion("Datos del Turno", "📋")
col_enc1, col_enc2, col_enc3 = st.columns([2, 2, 3])
with col_enc1:
    fecha_input = st.date_input("Fecha del Cierre", datetime.today())
with col_enc2:
    cajero = st.selectbox("Cajero de Turno", lista_empleados)
with col_enc3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Turno registrado el {hoy.strftime('%d/%m/%Y')} a las {hoy.strftime('%H:%M')} hs")

divider()


# ── SECCIÓN 2: MOVIMIENTOS ────────────────────────────────────────
seccion("Movimientos de Caja", "💵")

col_mov1, col_mov2 = st.columns(2)

with col_mov1:
    st.markdown("**Vales / Fiados**")
    cfg_vales = {
        "Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0),
        "Descripción": st.column_config.TextColumn("Detalle", required=True)
    }
    df_vales = st.data_editor(st.session_state['df_vales'], column_config=cfg_vales,
                               num_rows="dynamic", use_container_width=True, key="ed_df_vales")
    total_vales = df_vales["Monto"].sum() if not df_vales.empty else 0.0
    st.caption(f"Subtotal: **${total_vales:,.2f}**")

with col_mov2:
    st.markdown("**Transferencias Entrantes**")
    cfg_transf = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)}
    df_transferencias = st.data_editor(st.session_state['df_transferencias'], column_config=cfg_transf,
                                        num_rows="dynamic", use_container_width=True, key="ed_df_transferencias")
    total_transf_in = df_transferencias["Monto"].sum() if not df_transferencias.empty else 0.0
    st.caption(f"Subtotal: **${total_transf_in:,.2f}**")

divider()


# ── SECCIÓN 3: MERCADERÍA EMPLEADOS ──────────────────────────────
seccion("Mercadería de Empleados", "👥")

cfg_emp = {
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True),
    "Monto":    st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0)
}
df_empleados = st.data_editor(st.session_state['df_empleados'], column_config=cfg_emp,
                               num_rows="dynamic", use_container_width=True, key="ed_emp")
total_empleados = df_empleados["Monto"].sum() if not df_empleados.empty else 0.0
st.caption(f"Total consumo empleados: **${total_empleados:,.2f}**")

divider()


# ── SECCIÓN 4: EFECTIVO Y DIGITAL ────────────────────────────────
seccion("Totales de Venta", "💰")

col_ef1, col_ef2 = st.columns(2)

with col_ef1:
    st.markdown("**Ventas del día**")
    balanza_total      = st.number_input("Total Balanza (Venta Real)", 0.0, step=100.0)
    registradora_total = st.number_input("Registradora / Ticket Z",   0.0, step=100.0)

    with st.expander("🧮 Calculadora de Billetes", expanded=False):
        c1b, c2b = st.columns(2)
        with c1b:
            b20k = st.number_input("Billetes $20.000", 0, step=1)
            b10k = st.number_input("Billetes $10.000", 0, step=1)
            b5k  = st.number_input("Billetes $5.000",  0, step=1)
            b2k  = st.number_input("Billetes $2.000",  0, step=1)
        with c2b:
            b1k  = st.number_input("Billetes $1.000", 0, step=1)
            b500 = st.number_input("Billetes $500",   0, step=1)
            b200 = st.number_input("Billetes $200",   0, step=1)
            b100 = st.number_input("Billetes $100",   0, step=1)
        total_fisico = (b20k*20000 + b10k*10000 + b5k*5000 + b2k*2000
                       + b1k*1000 + b500*500 + b200*200 + b100*100)
        st.metric("Total calculado", f"${total_fisico:,.2f}")

    efectivo_neto = st.number_input("✅ Efectivo Total en Caja",
                                    value=float(total_fisico), step=100.0)

with col_ef2:
    st.markdown("**Cobros Digitales**")
    cd1, cd2 = st.columns(2)
    with cd1:
        mp     = st.number_input("Mercado Pago", 0.0, step=100.0)
        clover = st.number_input("Clover",       0.0, step=100.0)
    with cd2:
        nave = st.number_input("Nave", 0.0, step=100.0)
        bbva = st.number_input("BBVA", 0.0, step=100.0)

    total_digital = mp + nave + clover + bbva

    st.markdown("<br>", unsafe_allow_html=True)
    st.metric("Total Digital", f"${total_digital:,.2f}")

divider()


# ── SECCIÓN 5: PROVEEDORES Y SALIDAS ─────────────────────────────
seccion("Proveedores y Salidas", "📦")

col_prov1, col_prov2 = st.columns(2)

with col_prov1:
    st.markdown("**Pago a Proveedores**")
    cfg_prov = {
        "Proveedor":  st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True),
        "Forma Pago": st.column_config.SelectboxColumn("Método",    options=["Efectivo", "Digital / Banco"], required=True),
        "Nro Factura":st.column_config.TextColumn("Nro. Factura"),
        "Monto":      st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0),
    }
    df_proveedores = st.data_editor(st.session_state['df_proveedores'], column_config=cfg_prov,
                                    num_rows="dynamic", use_container_width=True, key="ed_prov")
    total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum()
    st.caption(f"Total en efectivo: **${total_prov_efectivo:,.2f}**")

with col_prov2:
    st.markdown("**Gastos Varios / Salidas de Caja**")
    cfg_sal = {
        "Descripción": st.column_config.TextColumn("Detalle", required=True),
        "Monto":       st.column_config.NumberColumn("($)", format="$%d", min_value=0),
    }
    df_salidas = st.data_editor(st.session_state['df_salidas'], column_config=cfg_sal,
                                num_rows="dynamic", use_container_width=True, key="ed_df_salidas")
    total_salidas = df_salidas["Monto"].sum() if not df_salidas.empty else 0.0
    st.caption(f"Subtotal: **${total_salidas:,.2f}**")

divider()


# ── SECCIÓN 6: RESULTADO FINAL ────────────────────────────────────
seccion("Resultado del Cierre", "📊")

total_ingresos  = efectivo_neto + total_digital + total_transf_in
total_egresos   = total_salidas + total_prov_efectivo + total_vales + total_empleados
diferencia      = balanza_total - (total_ingresos - total_egresos)

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Venta Balanza",    f"${balanza_total:,.2f}")
k2.metric("Efectivo en Caja", f"${efectivo_neto:,.2f}")
k3.metric("Total Digital",    f"${total_digital:,.2f}")
k4.metric("Total Egresos",    f"${total_egresos:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# Panel diferencia
if diferencia == 0:
    clase   = "ok"
    icono   = "✅"
    estado  = "CAJA CUADRADA"
    dif_txt = "$0,00"
elif diferencia > 0:
    clase   = "faltante"
    icono   = "⚠️"
    estado  = "FALTANTE"
    dif_txt = f"${diferencia:,.2f}"
else:
    clase   = "sobrante"
    icono   = "ℹ️"
    estado  = "SOBRANTE"
    dif_txt = f"${abs(diferencia):,.2f}"

st.markdown(f"""
    <div class="esf-resultado-panel">
        <div class="esf-diferencia {clase}">
            {icono}&nbsp;&nbsp;DIFERENCIA: {dif_txt}&nbsp;&nbsp;|&nbsp;&nbsp;{estado}
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── ACCIONES FINALES ──────────────────────────────────────────────
acc1, acc2, acc3 = st.columns([2, 2, 3])

with acc1:
    if st.button("💾  Guardar en Drive", use_container_width=True):
        # Persistir estado de sesión antes de guardar
        st.session_state['df_vales']          = df_vales
        st.session_state['df_transferencias'] = df_transferencias
        st.session_state['df_empleados']      = df_empleados
        st.session_state['df_proveedores']    = df_proveedores
        st.session_state['df_salidas']        = df_salidas

        datos = {
            "Fecha":      fecha_input.strftime("%d/%m/%Y"),
            "Cajero":     cajero,
            "Balanza":    balanza_total,
            "Digital":    total_digital,
            "Efectivo":   efectivo_neto,
            "Diferencia": diferencia,
        }
        if conn is not None:
            if guardar_todo_en_nube(datos, df_proveedores, df_empleados):
                st.success("✅ Cierre guardado exitosamente en Google Sheets.")
                st.balloons()
        else:
            st.error("No hay conexión con Google Sheets.")

with acc2:
    if st.button("📄  Generar PDF", use_container_width=True):
        desglose = {"MP": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
        pdf_bytes = generar_pdf_profesional(
            fecha_input, cajero, balanza_total, registradora_total,
            total_digital, efectivo_neto, df_salidas, df_transferencias,
            df_vales, df_proveedores, df_empleados, diferencia, desglose
        )
        st.download_button(
            label="⬇️  Descargar PDF del Cierre",
            data=pdf_bytes,
            file_name=f"Cierre_ESF_{fecha_input.strftime('%d-%m-%Y')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

with acc3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Turno: **{cajero}**  ·  Fecha: **{fecha_input.strftime('%d/%m/%Y')}**  ·  Registradora Z: **${registradora_total:,.2f}**")
