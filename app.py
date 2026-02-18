import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# 1. CONFIGURACIÓN PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cierre de Caja · Estancia San Francisco",
    page_icon="🧀",
    layout="centered"
)

# ─── ESCUDO ANTI-CIERRE ACCIDENTAL ───────────
js_warning = """
<script>
    window.addEventListener("beforeunload", function (e) {
        var msg = 'Es posible que los cambios no se guarden.';
        (e || window.event).returnValue = msg;
        return msg;
    });
</script>
"""
components.html(js_warning, height=0)

# ─────────────────────────────────────────────
# 2. ESTILOS — PALETA ESTANCIA SAN FRANCISCO
#    Verde botella  #2D4A2D  (primario)
#    Crema/beige    #F5EDD8  (fondo)
#    Dorado         #B8942A  (acento)
#    Marrón oscuro  #3E2A1A  (texto fuerte)
#    Verde claro    #4A7C4A  (hover / secundario)
# ─────────────────────────────────────────────
esf_style = """
<style>
/* ── FUENTES ── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Lato:wght@400;600&display=swap');

/* ── VARIABLES ── */
:root {
    --verde:    #2D4A2D;
    --verde2:   #4A7C4A;
    --crema:    #F5EDD8;
    --dorado:   #B8942A;
    --marron:   #3E2A1A;
    --gris:     #EDEDED;
    --blanco:   #FFFFFF;
    --texto:    #2C2C2C;
}

/* ── OCULTAR CHROME DE STREAMLIT ── */
#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}
header    {visibility: hidden;}

/* ── FONDO Y CONTENEDOR ── */
.stApp {
    background-color: var(--crema) !important;
    font-family: 'Lato', sans-serif;
}
.block-container {
    padding: 2rem 2.5rem 3rem 2.5rem !important;
    max-width: 1050px;
}

/* ── TÍTULOS ── */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--verde) !important;
}

/* ── INPUTS ── */
input[type="number"], input[type="text"], .stTextInput input {
    border: 1px solid #ccc !important;
    border-radius: 4px !important;
    background-color: var(--blanco) !important;
}
input:focus {
    border-color: var(--dorado) !important;
    box-shadow: 0 0 0 2px rgba(184,148,42,0.2) !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    border-radius: 4px !important;
    border-color: #ccc !important;
}

/* ── DATA EDITOR ── */
.stDataFrame, [data-testid="stDataEditor"] {
    background-color: var(--blanco) !important;
    border-radius: 6px !important;
    border: 1px solid #ddd !important;
}

/* ── BOTONES PRIMARIOS ── */
.stButton > button {
    background-color: var(--verde) !important;
    color: var(--crema) !important;
    border: none !important;
    border-radius: 5px !important;
    font-family: 'Lato', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background-color: var(--verde2) !important;
    color: var(--blanco) !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.2) !important;
}

/* ── BOTÓN DOWNLOAD ── */
.stDownloadButton > button {
    background-color: var(--dorado) !important;
    color: var(--blanco) !important;
    border: none !important;
    border-radius: 5px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background-color: #9a7a22 !important;
}

/* ── MÉTRICAS ── */
[data-testid="metric-container"] {
    background-color: var(--blanco);
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="metric-container"] label {
    color: var(--verde) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── EXPANDER ── */
.stExpander {
    background-color: var(--blanco) !important;
    border: 1px solid #ddd !important;
    border-radius: 6px !important;
}

/* ── CAPTIONS ── */
.stCaption { color: #777 !important; font-style: italic; }

/* ── ALERTS ── */
.stSuccess { border-left: 4px solid var(--verde2) !important; }
.stError   { border-left: 4px solid #C0392B !important; }
</style>
"""
st.markdown(esf_style, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. HELPERS DE UI
# ─────────────────────────────────────────────
def encabezado_seccion(titulo: str, icono: str = ""):
    """Banda verde con título de sección."""
    st.markdown(f"""
        <div style='
            background: linear-gradient(90deg, #2D4A2D 0%, #4A7C4A 100%);
            color: #F5EDD8;
            padding: 0.55rem 1rem;
            border-radius: 5px;
            margin: 1.8rem 0 0.8rem 0;
            font-family: "Lato", sans-serif;
            font-weight: 700;
            font-size: 0.9rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        '>{icono}&nbsp; {titulo}</div>
    """, unsafe_allow_html=True)

def linea_dorada():
    st.markdown("""
        <hr style='border:none; border-top: 2px solid #B8942A; margin: 1.5rem 0;'>
    """, unsafe_allow_html=True)

def panel_resultado(diferencia: float):
    """Panel grande de cierre con color dinámico."""
    if diferencia == 0:
        color, estado, icono = "#2D4A2D", "CAJA CUADRADA", "✅"
    elif diferencia > 0:
        color, estado, icono = "#8B2020", "FALTANTE", "⚠️"
    else:
        color, estado, icono = "#1A5C1A", "SOBRANTE", "ℹ️"

    st.markdown(f"""
        <div style='
            background-color: {color};
            color: #F5EDD8;
            text-align: center;
            padding: 1.6rem 2rem;
            border-radius: 8px;
            font-family: "Playfair Display", serif;
            font-size: 1.9rem;
            font-weight: 700;
            letter-spacing: 1px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
            margin: 1rem 0;
            border: 3px solid #B8942A;
        '>
            {icono} &nbsp; ${abs(diferencia):,.2f} &nbsp;·&nbsp; {estado}
        </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 4. LOGIN
# ─────────────────────────────────────────────
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Encabezado de login
    st.markdown("""
        <div style='text-align:center; margin-bottom: 2rem;'>
            <h1 style='font-family:"Playfair Display",serif; color:#2D4A2D; font-size:2.2rem;'>
                Estancia San Francisco
            </h1>
            <p style='color:#777; font-size:0.95rem;'>Sistema de Cierre de Caja · Acceso Restringido</p>
            <hr style='border:none; border-top: 2px solid #B8942A; width:60%; margin:1rem auto;'>
        </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.text_input(
            "Contraseña del local",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Ingresá la contraseña..."
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Contraseña incorrecta. Intentá de nuevo.")
    return False

if not check_password():
    st.stop()


# ─────────────────────────────────────────────
# 5. CONEXIÓN GOOGLE SHEETS
# ─────────────────────────────────────────────
conn = None
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.warning(f"Sin conexión a Google Sheets: {e}")

# ─────────────────────────────────────────────
# 6. DATOS MAESTROS
# ─────────────────────────────────────────────
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira",
                     "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
lista_empleados   = ["Santiago", "Julieta", "Mariela", "Fernanda",
                     "Brian", "Erika", "Oriana"]

if conn is not None:
    try:
        df_directorio = conn.read(worksheet="Directorio", ttl=600)
        if not df_directorio.empty and "Proveedor" in df_directorio.columns:
            lista_proveedores = df_directorio["Proveedor"].dropna().unique().tolist()
            if "Otro" not in lista_proveedores:
                lista_proveedores.append("Otro")
    except Exception as e:
        st.caption(f"No se pudo cargar el directorio: {e}")

# ─────────────────────────────────────────────
# 7. ESTADO DE SESIÓN
# ─────────────────────────────────────────────
session_keys = {
    'df_salidas':       ["Descripción", "Monto"],
    'df_transferencias':["Monto"],
    'df_vales':         ["Descripción", "Monto"],
    'df_proveedores':   ["Proveedor", "Forma Pago", "Nro Factura", "Monto"],
    'df_empleados':     ["Empleado", "Monto"],
}
for key, cols in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)


# ─────────────────────────────────────────────
# 8. FUNCIONES DE GUARDADO
# ─────────────────────────────────────────────
def guardar_historial(datos_cierre):
    df = conn.read(worksheet="Historial")
    df_upd = pd.concat([df, pd.DataFrame([datos_cierre])], ignore_index=True).fillna("")
    conn.update(worksheet="Historial", data=df_upd)

def guardar_proveedores(df_provs, fecha, cajero):
    pagos = df_provs[df_provs["Monto"] > 0].copy()
    if pagos.empty:
        return
    pagos["Fecha"]  = fecha
    pagos["Cajero"] = cajero
    df_ant = conn.read(worksheet="Pagos_Proveedores")
    conn.update(worksheet="Pagos_Proveedores",
                data=pd.concat([df_ant, pagos], ignore_index=True).fillna(""))

def guardar_empleados(df_empls, fecha):
    consumos = df_empls[df_empls["Monto"] > 0].copy()
    if consumos.empty:
        return
    consumos["Fecha"] = fecha
    consumos = consumos[["Fecha", "Empleado", "Monto"]]
    df_ant = conn.read(worksheet="Consumo_Empleados")
    conn.update(worksheet="Consumo_Empleados",
                data=pd.concat([df_ant, consumos], ignore_index=True).fillna(""))

def guardar_todo_en_nube(datos_cierre, df_provs, df_empls):
    try:
        guardar_historial(datos_cierre)
        guardar_proveedores(df_provs, datos_cierre["Fecha"], datos_cierre["Cajero"])
        guardar_empleados(df_empls, datos_cierre["Fecha"])
        return True
    except Exception as e:
        st.error(f"Error guardando en nube: {e}")
        return False


# ─────────────────────────────────────────────
# 9. FUNCIÓN PDF
# ─────────────────────────────────────────────
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital,
                             efectivo_neto, df_salidas, df_transferencias,
                             df_vales, df_proveedores, df_empleados,
                             diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # Logo
    if os.path.exists("logo.png"):
        try:
            pdf.image("logo.png", 15, 10, 30)
        except Exception:
            pass

    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    fecha_texto = f"{dias_semana[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"

    pdf.set_xy(50, 12); pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20); pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R')
    pdf.set_x(130)
    pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R')
    pdf.ln(15)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)

    # KPIs
    def dibujar_kpi(titulo, monto):
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"{titulo}: $ {monto:,.2f}", ln=1, align='C', fill=True, border=1)
        pdf.ln(2)

    dibujar_kpi("1. BALANZA",   balanza)
    dibujar_kpi("2. EFECTIVO",  efectivo_neto)
    dibujar_kpi("3. DIGITAL",   total_digital)
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {registradora:,.2f}", border=0, align='C', ln=1)
    pdf.ln(5)

    # Tablas
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

    dibujar_tabla("MERCADERÍA EMPLEADOS",       df_empleados)
    dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transferencias, label_fijo="Transferencia")
    dibujar_tabla("GASTOS VARIOS / SALIDAS",    df_salidas)
    dibujar_tabla("VALES / FIADOS",             df_vales)

    # Resultado
    pdf.ln(5)
    if diferencia == 0:
        estado, color_texto = "OK",       (0, 0, 0)
    elif diferencia > 0:
        estado, color_texto = "FALTANTE", (200, 0, 0)
    else:
        estado, color_texto = "SOBRANTE", (0, 100, 0)

    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*color_texto)
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1)

    return pdf.output(dest="S").encode("latin-1")


# ─────────────────────────────────────────────
# 10. HELPER TABLAS EDITABLES
# ─────────────────────────────────────────────
def input_tabla(titulo, key, solo_monto=False):
    cfg = {"Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0)}
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
    st.caption(f"Subtotal: ${total:,.2f}")
    return df, total


# ═════════════════════════════════════════════
#  ENCABEZADO PRINCIPAL
# ═════════════════════════════════════════════
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=75)
    else:
        st.markdown("""
            <div style='
                width:65px; height:65px;
                background:#2D4A2D;
                border-radius:50%;
                border: 3px solid #B8942A;
                display:flex; align-items:center; justify-content:center;
                font-size:1.8rem;
            '>🧀</div>
        """, unsafe_allow_html=True)
with col_titulo:
    st.markdown("""
        <h1 style='margin-bottom:0; font-size:1.9rem;'>Estancia San Francisco</h1>
        <p style='color:#777; margin-top:0.1rem; font-size:0.9rem; font-family:Lato,sans-serif;'>
            Sistema de Cierre de Caja
        </p>
    """, unsafe_allow_html=True)

linea_dorada()

# ═════════════════════════════════════════════
#  SECCIÓN 1 — DATOS DEL TURNO
# ═════════════════════════════════════════════
encabezado_seccion("Datos del Turno", "📋")
col_enc1, col_enc2 = st.columns(2)
with col_enc1:
    fecha_input = st.date_input("Fecha del cierre", datetime.today())
with col_enc2:
    cajero = st.selectbox("Cajero de Turno", lista_empleados)

# ═════════════════════════════════════════════
#  SECCIÓN 2 — TOTALES DE VENTA
# ═════════════════════════════════════════════
encabezado_seccion("Totales de Venta", "💰")
col_core1, col_core2 = st.columns(2)
with col_core1:
    balanza_total     = st.number_input("Total Balanza (Venta Real)", 0.0, step=100.0)
    registradora_total = st.number_input("Registradora / Ticket Z",  0.0, step=100.0)
with col_core2:
    with st.expander("🧮 Calculadora de Billetes", expanded=False):
        cols_bill = st.columns(2)
        b20k = cols_bill[0].number_input("$20.000", 0, min_value=0)
        b10k = cols_bill[1].number_input("$10.000", 0, min_value=0)
        b5k  = cols_bill[0].number_input("$5.000",  0, min_value=0)
        b2k  = cols_bill[1].number_input("$2.000",  0, min_value=0)
        b1k  = cols_bill[0].number_input("$1.000",  0, min_value=0)
        b500 = cols_bill[1].number_input("$500",    0, min_value=0)
        b200 = cols_bill[0].number_input("$200",    0, min_value=0)
        b100 = cols_bill[1].number_input("$100",    0, min_value=0)
        total_fisico = (b20k*20000 + b10k*10000 + b5k*5000 +
                        b2k*2000  + b1k*1000   + b500*500  +
                        b200*200  + b100*100)
        st.markdown(f"""
            <div style='
                background:#2D4A2D; color:#F5EDD8;
                text-align:center; border-radius:5px;
                padding:0.4rem; font-weight:700; margin-top:0.5rem;
            '>Total: ${total_fisico:,.2f}</div>
        """, unsafe_allow_html=True)
    efectivo_neto = st.number_input("Efectivo Total en Caja", value=float(total_fisico), step=100.0)

# ─── Cobros Digitales ────────────────────────
encabezado_seccion("Cobros Digitales", "💳")
col_d1, col_d2 = st.columns(2)
with col_d1:
    mp     = st.number_input("Mercado Pago", 0.0, step=100.0)
    clover = st.number_input("Clover",       0.0, step=100.0)
with col_d2:
    nave = st.number_input("Nave", 0.0, step=100.0)
    bbva = st.number_input("BBVA", 0.0, step=100.0)
total_digital = mp + nave + clover + bbva
st.caption(f"Total digital: ${total_digital:,.2f}")

# ═════════════════════════════════════════════
#  SECCIÓN 3 — MOVIMIENTOS
# ═════════════════════════════════════════════
encabezado_seccion("Transferencias Entrantes", "🔄")
df_transferencias, total_transf_in = input_tabla(
    "Transferencias (Entrantes)", "df_transferencias", solo_monto=True
)

encabezado_seccion("Vales / Fiados", "📝")
df_vales, total_vales = input_tabla("Vales / Fiados", "df_vales")

encabezado_seccion("Gastos Varios (Salidas de Caja)", "🧾")
df_salidas, total_salidas = input_tabla("Gastos Varios", "df_salidas")

# ─── Proveedores ─────────────────────────────
encabezado_seccion("Pago a Proveedores", "📦")
cfg_prov = {
    "Proveedor":  st.column_config.SelectboxColumn("Proveedor",  options=lista_proveedores, required=True),
    "Forma Pago": st.column_config.SelectboxColumn("Método",     options=["Efectivo", "Digital / Banco"], required=True),
    "Nro Factura":st.column_config.TextColumn("Nro Factura"),
    "Monto":      st.column_config.NumberColumn("Monto ($)",     format="$%d", min_value=0),
}
df_proveedores = st.data_editor(
    st.session_state.df_proveedores,
    column_config=cfg_prov,
    num_rows="dynamic",
    use_container_width=True,
    key="ed_prov"
)
total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum()
st.caption(f"Pagos en efectivo: ${total_prov_efectivo:,.2f}  ·  "
           f"Digital/Banco: ${df_proveedores[df_proveedores['Forma Pago'] == 'Digital / Banco']['Monto'].sum():,.2f}")

# ─── Mercadería Empleados ─────────────────────
encabezado_seccion("Mercadería de Empleados", "👤")
cfg_emp = {
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True),
    "Monto":    st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0),
}
df_empleados = st.data_editor(
    st.session_state.df_empleados,
    column_config=cfg_emp,
    num_rows="dynamic",
    use_container_width=True,
    key="ed_emp"
)
total_empleados = df_empleados["Monto"].sum()
st.caption(f"Total empleados: ${total_empleados:,.2f}")

# ─── Sync session_state ───────────────────────
st.session_state['df_transferencias'] = df_transferencias
st.session_state['df_vales']          = df_vales
st.session_state['df_salidas']        = df_salidas
st.session_state['df_proveedores']    = df_proveedores
st.session_state['df_empleados']      = df_empleados


# ═════════════════════════════════════════════
#  SECCIÓN 4 — RESULTADO DEL CIERRE
# ═════════════════════════════════════════════
linea_dorada()
encabezado_seccion("Resultado del Cierre", "📊")

total_ingresos = efectivo_neto + total_digital + total_transf_in
total_egresos  = total_salidas + total_prov_efectivo + total_vales + total_empleados
diferencia     = balanza_total - (total_ingresos - total_egresos)

# Fila de métricas resumen
m1, m2, m3, m4 = st.columns(4)
m1.metric("Venta Balanza",     f"${balanza_total:,.2f}")
m2.metric("Efectivo en Caja",  f"${efectivo_neto:,.2f}")
m3.metric("Cobros Digitales",  f"${total_digital:,.2f}")
m4.metric("Total Egresos",     f"${total_egresos:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)
panel_resultado(diferencia)
st.markdown("<br>", unsafe_allow_html=True)

# ─── Botones de acción ────────────────────────
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("💾  Guardar en Drive", use_container_width=True):
        if conn is None:
            st.error("No hay conexión con Google Sheets.")
        else:
            confirmar = st.checkbox("✅ Confirmo que los datos son correctos antes de guardar")
            if confirmar:
                datos = {
                    "Fecha":      fecha_input.strftime("%d/%m/%Y"),
                    "Cajero":     cajero,
                    "Balanza":    balanza_total,
                    "Digital":    total_digital,
                    "Efectivo":   efectivo_neto,
                    "Diferencia": diferencia,
                }
                if guardar_todo_en_nube(datos, df_proveedores, df_empleados):
                    st.success("¡Guardado exitoso!")
                    st.balloons()

with btn_col2:
    if st.button("📄  Generar PDF", use_container_width=True):
        desglose = {"MP": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
        pdf_bytes = generar_pdf_profesional(
            fecha_input, cajero, balanza_total, registradora_total,
            total_digital, efectivo_neto, df_salidas, df_transferencias,
            df_vales, df_proveedores, df_empleados, diferencia, desglose
        )
        st.download_button(
            "⬇️  Descargar PDF",
            pdf_bytes,
            file_name=f"Cierre_{fecha_input}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
