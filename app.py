import streamlit as st 
import pandas as pd 
from datetime import datetime 
import streamlit.components.v1 as components 

# Importaciones locales
from src.auth import check_password
from src.config import SESSION_KEYS, LISTA_CAJEROS, LISTA_EMPLEADOS
from src.sheets import get_connection, cargar_proveedores, guardar_cierre
from src.pdf import generar_pdf_profesional
from src.ui_components import render_input_tabla
from src.utils import logger

# --- 1. CONFIGURACIÓN INICIAL --- 
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered") 

# Inyección de JS para evitar cierres accidentales
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

# Estilos CSS para ocultar elementos de Streamlit
st.markdown(""" 
    <style> 
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;} 
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}  
    </style> 
    """, unsafe_allow_html=True) 

# --- 2. SEGURIDAD ---
if not check_password(): 
    st.stop() 

# --- 3. INICIALIZACIÓN DE ESTADO ---
for key, cols in SESSION_KEYS.items(): 
    if key not in st.session_state: 
        st.session_state[key] = pd.DataFrame(columns=cols) 

# --- 4. CONEXIONES Y DATOS ---
conn = get_connection()
lista_proveedores = cargar_proveedores(conn)

# --- 5. INTERFAZ DE USUARIO ---
st.title("Estancia San Francisco") 

col_enc1, col_enc2 = st.columns(2) 
with col_enc1: fecha_input = st.date_input("Fecha", datetime.today()) 
with col_enc2: cajero = st.selectbox("Cajero de Turno", LISTA_CAJEROS) 
st.markdown("---") 

# Tablas de Carga
df_vales, total_vales = render_input_tabla("Vales / Fiados", "df_vales") 
df_transferencias, total_transf_in = render_input_tabla("Transferencias (Entrantes)", "df_transferencias", solo_monto=True) 
df_errores, total_errores = render_input_tabla("Errores de Facturación", "df_errores", solo_monto=True) 
df_descuentos, total_descuentos = render_input_tabla("Somos Avellaneda (Descuentos)", "df_descuentos", solo_monto=True) 

# Mercadería de Empleados
st.markdown("**Mercadería de Empleados**") 
cfg_emp = { 
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=LISTA_EMPLEADOS, required=True), 
    "Ticket": st.column_config.SelectboxColumn("Tipo", options=["Con Ticket", "Sin Ticket"], required=True),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0, required=True) 
} 
df_empleados = st.data_editor(
    st.session_state.df_empleados, 
    column_config=cfg_emp, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="widget_empleados_root", 
    hide_index=True
) 
st.session_state.df_empleados = df_empleados

# Lógica de Empleados: Solo sumamos los "Con Ticket" al total justificado
total_empleados = df_empleados[df_empleados["Ticket"] == "Con Ticket"]["Monto"].sum() if not df_empleados.empty and "Ticket" in df_empleados.columns else 0.0

st.markdown("---")

# Ventas y Efectivo
# ... (líneas 80-100 aprox) ...

# Proveedores y Gastos
st.markdown("**Pago a Proveedores**") 
cfg_prov = { 
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True), 
    "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"], required=True), 
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0, required=True) 
} 
df_proveedores = st.data_editor(
    st.session_state.df_proveedores, 
    column_config=cfg_prov, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="widget_proveedores_root", 
    hide_index=True
) 
st.session_state.df_proveedores = df_proveedores
total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum() if not df_proveedores.empty else 0.0

df_salidas, total_salidas = render_input_tabla("Gastos Varios (Salidas de Caja)", "df_salidas") 

# --- 6. CÁLCULO FINAL --- 
st.markdown("### Resultado del Cierre") 

# Se suman todos los conceptos que justifican la diferencia con la balanza
total_justificado = (
    total_digital + 
    efectivo_neto + 
    total_transf_in + 
    total_salidas + 
    total_prov_efectivo + 
    total_vales + 
    total_empleados + 
    total_errores + 
    total_descuentos
)
diferencia = balanza_total - total_justificado 

c1, c2, c3 = st.columns(3) 
c1.metric("Diferencia", f"${diferencia:,.2f}", delta_color="inverse" if diferencia > 0 else "normal") 

# --- 7. ACCIONES ---
if c2.button("Guardar en Drive", use_container_width=True): 
    estado_caja = "OK" if diferencia == 0 else ("FALTANTE" if diferencia > 0 else "SOBRANTE")
    
    datos = { 
        "Fecha": fecha_input.strftime("%d/%m/%Y"), 
        "Cajero": cajero, 
        "Balanza": balanza_total, 
        "Digital": total_digital, 
        "Efectivo": efectivo_neto, 
        "Transferencias": total_transf_in,
        "Salidas": total_salidas,
        "Vales": total_vales,
        "Errores": total_errores,
        "Descuentos": total_descuentos,
        "Proveedores": total_prov_efectivo,
        "Diferencia": diferencia,
        "Estado": estado_caja
    } 
    
    if guardar_cierre(conn, datos, df_proveedores, df_empleados): 
        st.success("Cierre guardado exitosamente en Google Sheets") 
        st.balloons() 

if c3.button("Generar PDF", use_container_width=True): 
    desglose = {"MP": mp, "Nave": nave, "Clover": clover, "BBVA": bbva} 
    pdf_bytes = generar_pdf_profesional(
        fecha_input, cajero, balanza_total, registradora_total,  
        total_digital, efectivo_neto, df_salidas, df_transferencias,  
        df_errores, df_vales, df_descuentos, df_proveedores,  
        df_empleados, diferencia, desglose
    ) 
    if pdf_bytes:
        st.download_button("Descargar PDF", pdf_bytes, f"Cierre_{fecha_input}.pdf", "application/pdf")
