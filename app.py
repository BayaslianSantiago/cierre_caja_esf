import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN Y ESTILO (CSS CUSTOM) ---
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered")

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&family=Playfair+Display:wght@700&display=swap');

    /* Fondo y Tipografía */
    .stApp {
        background-color: #F5EDD8;
        color: #2D4A2D;
        font-family: 'Lato', sans-serif;
    }

    /* Títulos Estilo Serif */
    h1, h2, h3, .playfair {
        font-family: 'Playfair Display', serif !important;
        color: #2D4A2D !important;
    }

    /* Botones - Verde Botella */
    div.stButton > button {
        background-color: #2D4A2D !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        height: 3em !important;
        font-weight: bold !important;
    }

    /* Botón PDF - Dorado */
    .stDownloadButton > button {
        background-color: #B8942A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }

    /* Bandas de Sección */
    .section-header {
        background: linear-gradient(90deg, #2D4A2D, #406340);
        color: #F5EDD8;
        padding: 12px 20px;
        border-radius: 8px;
        margin: 25px 0 15px 0;
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }

    /* Panel de Resultado */
    .result-box {
        border: 2px solid #B8942A;
        padding: 25px;
        border-radius: 15px;
        background-color: white;
        text-align: center;
        margin: 20px 0;
    }

    .gold-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #B8942A, transparent);
        margin: 20px 0;
    }

    /* Inputs y Data Editors */
    .stNumberInput, .stDataEditor {
        background-color: white !important;
        border-radius: 5px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 2. SISTEMA DE LOGIN ---
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<h2 style='text-align: center;'>Acceso Restringido</h2>", unsafe_allow_html=True)
    st.text_input("Contraseña del local:", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Contraseña incorrecta")
    return False

if not check_password():
    st.stop()

# --- 3. CONEXIONES Y DATOS MAESTROS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Error de conexión a la nube.")

lista_empleados = ["Santiago", "Julieta", "Mariela", "Fernanda", "Brian", "Erika", "Oriana"]
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]

# Variables de Sesión
session_keys = {
    'df_salidas': ["Descripción", "Monto"],
    'df_vales': ["Descripción", "Monto"],
    'df_proveedores': ["Proveedor", "Forma Pago", "Monto"],
    'df_empleados': ["Empleado", "Monto"]
}
for key, cols in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)

# --- 4. FUNCIONES DE GUARDADO Y PDF ---
def guardar_en_nube(datos_cierre, df_provs, df_empls):
    try:
        # Historial
        df_hist = conn.read(worksheet="Historial")
        df_hist_upd = pd.concat([df_hist, pd.DataFrame([datos_cierre])], ignore_index=True).fillna("")
        conn.update(worksheet="Historial", data=df_hist_upd)
        
        # Consumo Empleados
        consumos = df_empls[df_empls["Monto"] > 0].copy()
        if not consumos.empty:
            consumos["Fecha"] = datos_cierre["Fecha"]
            df_empl_ant = conn.read(worksheet="Consumo_Empleados")
            df_empl_upd = pd.concat([df_empl_ant, consumos[["Fecha", "Empleado", "Monto"]]], ignore_index=True).fillna("")
            conn.update(worksheet="Consumo_Empleados", data=df_empl_upd)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def generar_pdf(datos, df_sal, df_prov, df_empl, dif):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(45, 74, 45) # Verde Botella
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_text_color(245, 237, 216) # Crema
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, "ESTANCIA SAN FRANCISCO", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 5, "Reporte de Cierre de Caja", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, f"Fecha: {datos['Fecha']}")
    pdf.cell(95, 10, f"Cajero: {datos['Cajero']}", ln=True, align='R')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    # Resumen
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, f"DIFERENCIA FINAL: $ {dif:,.2f}", 1, ln=True, align='C', fill=True)
    
    # Detalle Empleados
    if not df_empl.empty:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, "CONSUMO EMPLEADOS", ln=True)
        pdf.set_font("Arial", '', 10)
        for _, r in df_empl.iterrows():
            pdf.cell(150, 7, f" - {r['Empleado']}")
            pdf.cell(40, 7, f"$ {r['Monto']:,.2f}", ln=True, align='R')

    return pdf.output(dest="S").encode("latin-1")

# --- 5. INTERFAZ ---
col_logo1, col_logo2 = st.columns([1, 4])
with col_logo2:
    st.markdown("<h1 style='margin-bottom:0;'>Estancia San Francisco</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-style:italic; color:#B8942A;'>Tradición y Calidad en su Mesa</p>", unsafe_allow_html=True)

st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)

c_inf1, c_inf2 = st.columns(2)
fecha_input = c_inf1.date_input("Fecha", datetime.today())
cajero = c_inf2.selectbox("Cajero Responsable", lista_empleados)

# CALCULADORA
st.markdown("<div class='section-header'>🪙 Calculadora de Efectivo</div>", unsafe_allow_html=True)
with st.expander("Desglosar Billetes", expanded=False):
    cb1, cb2, cb3 = st.columns(3)
    b20k = cb1.number_input("$20.000", 0); b10k = cb2.number_input("$10.000", 0); b2k = cb3.number_input("$2.000", 0)
    b1k = cb1.number_input("$1.000", 0); b500 = cb2.number_input("$500", 0); b200 = cb3.number_input("$200", 0)
    b100 = cb1.number_input("$100", 0); mon = cb2.number_input("Monedas/Otros", 0.0)
    total_fisico = (b20k*20000)+(b10k*10000)+(b2k*2000)+(b1k*1000)+(b500*500)+(b200*200)+(b100*100)+mon
    st.markdown(f"<h3 style='text-align:right;'>Total: ${total_fisico:,.2f}</h3>", unsafe_allow_html=True)

# DIGITAL
st.markdown("<div class='section-header'>📱 Cobros Digitales</div>", unsafe_allow_html=True)
dg1, dg2 = st.columns(2)
mp = dg1.number_input("Mercado Pago", 0.0)
nave = dg2.number_input("Nave", 0.0)
clover = dg1.number_input("Clover", 0.0)
bbva = dg2.number_input("BBVA", 0.0)
total_digital = mp + nave + clover + bbva

# EMPLEADOS
st.markdown("<div class='section-header'>🥖 Mercadería Empleados</div>", unsafe_allow_html=True)
df_empl = st.data_editor(st.session_state.df_empleados, column_config={
    "Empleado": st.column_config.SelectboxColumn("Nombre", options=lista_empleados, required=True),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d")
}, num_rows="dynamic", use_container_width=True)
total_empl = df_empl["Monto"].sum()

# VENTAS Y GASTOS
st.markdown("<div class='section-header'>📑 Ventas y Salidas</div>", unsafe_allow_html=True)
v1, v2 = st.columns(2)
balanza = v1.number_input("Total Balanza", 0.0)
vales = v2.number_input("Total Vales / Fiados", 0.0)

st.markdown("**Proveedores y Salidas de Caja**")
df_prov = st.data_editor(st.session_state.df_proveedores, column_config={
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores),
    "Forma Pago": st.column_config.SelectboxColumn("Pago", options=["Efectivo", "Digital"])
}, num_rows="dynamic", use_container_width=True)
total_prov_efectivo = df_prov[df_prov["Forma Pago"] == "Efectivo"]["Monto"].sum()

# --- 6. RESULTADOS ---
st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
total_justificado = total_digital + total_fisico + total_empl + vales + total_prov_efectivo
diferencia = balanza - total_justificado

st.markdown(f"""
<div class='result-box'>
    <p style='margin:0; font-family:Playfair Display; font-size:1.5rem;'>Diferencia Final</p>
    <h1 style='margin:0; font-size:4rem;'>${diferencia:,.2f}</h1>
</div>
""", unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2)
if col_f1.button("💾 Guardar Cierre", use_container_width=True):
    datos = {
        "Fecha": fecha_input.strftime("%d/%m/%Y"), "Cajero": cajero, 
        "Balanza": balanza, "Diferencia": diferencia
    }
    if guardar_en_nube(datos, df_prov, df_empl):
        st.success("Guardado correctamente en Drive")
        st.balloons()

with col_f2:
    pdf_b = generar_pdf({"Fecha": fecha_input, "Cajero": cajero}, None, df_prov, df_empl, diferencia)
    st.download_button("📄 Descargar PDF", pdf_b, f"Cierre_{fecha_input}.pdf", "application/pdf", use_container_width=True)
