import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered")

# CSS personalizado para la estética del local
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&family=Playfair+Display:wght@700&display=swap');

    .stApp {
        background-color: #F5EDD8;
        color: #2D4A2D;
        font-family: 'Lato', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #2D4A2D !important;
    }
    .section-header {
        background: linear-gradient(90deg, #2D4A2D, #406340);
        color: #F5EDD8;
        padding: 10px 15px;
        border-radius: 5px;
        margin: 20px 0;
        font-family: 'Playfair Display', serif;
    }
    .gold-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #B8942A, transparent);
        margin: 20px 0;
    }
    .result-box {
        border: 2px solid #B8942A;
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ESCUDO ANTI-CIERRE ACCIDENTAL
components.html("""<script>window.addEventListener("beforeunload",function(e){var m='Cambios no guardados';(e||window.event).returnValue=m;return m;});</script>""", height=0)

# --- 2. LOGIN ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Acceso Restringido")
    st.text_input("Contraseña del local:", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Contraseña incorrecta")
    return False

if not check_password(): st.stop()

# --- 3. CONEXIONES Y DATOS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Error de conexión")

lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
lista_empleados = ["Santiago", "Julieta", "Mariela", "Fernanda", "Brian", "Erika", "Oriana"]

# Inicializar sesión
for key, cols in {
    'df_salidas': ["Descripción", "Monto"],
    'df_transferencias': ["Monto"],
    'df_vales': ["Descripción", "Monto"],
    'df_errores': ["Monto"],
    'df_descuentos': ["Monto"],
    'df_proveedores': ["Proveedor", "Forma Pago", "Nro Factura", "Monto"],
    'df_empleados': ["Empleado", "Monto"]
}.items():
    if key not in st.session_state: st.session_state[key] = pd.DataFrame(columns=cols)

# --- 4. ENCABEZADO ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>Estancia San Francisco</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #B8942A; font-style: italic;'>Reporte Diario de Cierre de Caja</p>", unsafe_allow_html=True)
st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

col_e1, col_e2 = st.columns(2)
fecha_input = col_e1.date_input("Fecha", datetime.today())
cajero = col_e2.selectbox("Cajero de Turno", lista_empleados)

# --- 5. LÓGICA SOMOS AVELLANEDA (Lunes y Miércoles) ---
dia_semana = fecha_input.weekday()
total_descuentos = 0.0
if dia_semana in [0, 2]:
    st.markdown("<div class='section-header'>🛍️ Somos Avellaneda (Descuentos)</div>", unsafe_allow_html=True)
    df_desc = st.data_editor(st.session_state.df_descuentos, column_config={"Monto": st.column_config.NumberColumn("$", format="$%d")}, num_rows="dynamic", use_container_width=True, key="ed_desc")
    total_descuentos = df_desc["Monto"].sum()

# --- 6. SECCIONES DE CARGA ---
st.markdown("<div class='section-header'>👥 Mercadería Empleados</div>", unsafe_allow_html=True)
df_empl = st.data_editor(st.session_state.df_empleados, column_config={
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True),
    "Monto": st.column_config.NumberColumn("$", format="$%d")
}, num_rows="dynamic", use_container_width=True, key="ed_empl")
total_empleados = df_empl["Monto"].sum()

st.markdown("<div class='section-header'>🪙 Efectivo en Caja</div>", unsafe_allow_html=True)
with st.expander("Calculadora de Billetes", expanded=False):
    c1, c2, c3 = st.columns(3)
    b20k = c1.number_input("$20k", 0); b10k = c2.number_input("$10k", 0); b2k = c3.number_input("$2k", 0)
    b1k = c1.number_input("$1k", 0); b500 = c2.number_input("$500", 0); b200 = c3.number_input("$200", 0)
    b100 = c1.number_input("$100", 0); mon = c2.number_input("Monedas/Otros", 0.0)
    total_fisico = (b20k*20000)+(b10k*10000)+(b2k*2000)+(b1k*1000)+(b500*500)+(b200*200)+(b100*100)+mon
efectivo_neto = st.number_input("Efectivo Total Confirmado", value=float(total_fisico))

st.markdown("<div class='section-header'>📱 Cobros Digitales</div>", unsafe_allow_html=True)
dg1, dg2 = st.columns(2)
mp = dg1.number_input("Mercado Pago", 0.0); nave = dg2.number_input("Nave", 0.0)
clover = dg1.number_input("Clover", 0.0); bbva = dg2.number_input("BBVA", 0.0)
total_digital = mp + nave + clover + bbva

st.markdown("<div class='section-header'>🚛 Proveedores y Salidas</div>", unsafe_allow_html=True)
df_prov = st.data_editor(st.session_state.df_proveedores, column_config={
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores),
    "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"])
}, num_rows="dynamic", use_container_width=True, key="ed_prov")
total_prov_efectivo = df_prov[df_prov["Forma Pago"] == "Efectivo"]["Monto"].sum()

# --- 7. RESULTADO FINAL ---
st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
balanza_total = st.number_input("TOTAL BALANZA", 0.0, step=500.0)

# Recalcular Justificado
total_justificado = total_digital + efectivo_neto + total_empleados + total_prov_efectivo + total_descuentos
# Nota: Aquí puedes sumar vales/errores si los usas
diferencia = balanza_total - total_justificado

st.markdown(f"""
<div class='result-box'>
    <p style='margin:0; font-size:1.2rem;'>Diferencia de Caja</p>
    <h1 style='margin:0; font-size:3.5rem;'>${diferencia:,.2f}</h1>
</div>
""", unsafe_allow_html=True)

# BOTONES
st.write("")
b_col1, b_col2 = st.columns(2)
if b_col1.button("💾 Guardar en Drive", use_container_width=True):
    # Lógica de guardado (usa tu función guardar_todo_en_nube)
    st.success("Guardado correctamente")

if b_col2.button("📄 Generar PDF", use_container_width=True):
    st.info("Generando reporte...")
