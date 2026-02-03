import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Cierre San Francisco", layout="centered", initial_sidebar_state="collapsed")

# CSS para limpiar la interfaz (borrar header, footer y márgenes excesivos)
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        div[data-testid="stMetricValue"] {font-size: 1.8rem;}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE SEGURIDAD (LOGIN)
# ==============================================================================
def check_login():
    if st.session_state.get("authenticated", False):
        return True

    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    st.title("🔒 Acceso Restringido")
    st.text_input("Contraseña:", type="password", on_change=password_entered, key="password")
    
    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("Contraseña incorrecta")
    return False

if not check_login():
    st.stop()

# ==============================================================================
# 3. GESTIÓN DE DATOS Y CONEXIONES
# ==============================================================================
# Conexión resiliente a Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

def inicializar_session_state():
    """Inicializa las tablas vacías en memoria si no existen."""
    tablas = {
        "df_salidas": ["Descripción", "Monto"],
        "df_vales": ["Descripción", "Monto"],
        "df_transferencias": ["Monto"], # Entrantes
        "df_errores": ["Monto"],
        "df_descuentos": ["Monto"],
        "df_proveedores": ["Proveedor", "Forma Pago", "Nro Factura", "Monto"]
    }
    
    for key, cols in tablas.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=cols)

def cargar_maestro_proveedores():
    """Carga la lista de proveedores desde la nube con caché para no lentificar."""
    lista_default = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
    if not conn: return lista_default, pd.DataFrame()
    
    try:
        df = conn.read(worksheet="Directorio", ttl=600) # Cache de 10 minutos
        if not df.empty and "Proveedor" in df.columns:
            lista = df["Proveedor"].dropna().unique().tolist()
            if "Otro" not in lista: lista.append("Otro")
            return lista, df
    except:
        pass
    return lista_default, pd.DataFrame()

# Inicializamos datos
inicializar_session_state()
LISTA_PROVEEDORES, DF_DIRECTORIO = cargar_maestro_proveedores()

# ==============================================================================
# 4. LÓGICA DE GUARDADO EN NUBE
# ==============================================================================
def guardar_cierre(datos_cierre, df_provs):
    if not conn:
        st.error("No hay conexión con Google Sheets."); return False
    
    try:
        # 1. Guardar en Historial
        df_hist = conn.read(worksheet="Historial")
        df_hist = pd.concat([df_hist, pd.DataFrame([datos_cierre])], ignore_index=True).fillna("")
        conn.update(worksheet="Historial", data=df_hist)
        
        # 2. Guardar Detalle Proveedores
        pagos = df_provs[df_provs["Monto"] > 0].copy()
        if not pagos.empty:
            # Asegurar columnas necesarias
            for col in ["Proveedor", "Forma Pago", "Nro Factura", "Monto"]:
                if col not in pagos.columns: pagos[col] = "" if col != "Monto" else 0.0
            
            # Agregar metadatos
            pagos["Fecha"] = datos_cierre["Fecha"]
            pagos["Cajero"] = datos_cierre["Cajero"]
            
            # Ordenar y Guardar
            pagos = pagos[["Fecha", "Proveedor", "Forma Pago", "Nro Factura", "Monto", "Cajero"]]
            df_pagos = conn.read(worksheet="Pagos_Proveedores")
            df_pagos = pd.concat([df_pagos, pagos], ignore_index=True).fillna("")
            conn.update(worksheet="Pagos_Proveedores", data=df_pagos)
            
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

# ==============================================================================
# 5. GENERADOR DE PDF
# ==============================================================================
def generar_pdf(fecha, cajero, kpis, tablas_data, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # Logo
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 

    # Fecha formateada
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    fecha_txt = f"{dias[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}"

    # Encabezado
    pdf.set_xy(50, 12); pdf.set_font("Arial", 'B', 18); pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10); pdf.cell(60, 6, f"FECHA: {fecha_txt}", ln=1, align='R')
    pdf.set_x(130); pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R')
    pdf.ln(15); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(5)

    # KPIs (Bloques Grises)
    def kpi_box(titulo, valor):
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"{titulo}: $ {valor:,.2f}", ln=1, align='C', fill=True, border=1)
        pdf.ln(2)

    kpi_box("1. BALANZA", kpis['balanza'])
    kpi_box("2. EFECTIVO (Retiro)", kpis['efectivo'])
    kpi_box("3. DIGITAL", kpis['digital'])
    
    pdf.ln(2); pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {kpis['z']:,.2f}", border=0, align='C', ln=1)
    pdf.ln(5)

    # Desgloses
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE DIGITAL", ln=1); pdf.set_font("Arial", '', 9)
    for k, v in desglose_digital.items():
        if v > 0: pdf.cell(130, 5, f" - {k}"); pdf.cell(40, 5, f"$ {v:,.2f}", align='R', ln=1)
    
    pdf.ln(3); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE EFECTIVO", ln=1); pdf.set_font("Arial", '', 9)
    pdf.cell(130, 5, " - Efectivo Contado (Ventas)"); pdf.cell(40, 5, f"$ {kpis['efectivo']:,.2f}", align='R', ln=1)

    # Tablas
    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "AJUSTES Y PROVEEDORES", ln=1)

    def draw_table(titulo, df, tipo='lista'):
        if df.empty or df['Monto'].sum() == 0: return
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 9)
        
        for _, row in df.iterrows():
            if row['Monto'] > 0:
                if tipo == 'prov':
                    txt = f"{row['Proveedor']} ({row['Forma Pago']}) - Fac: {row['Nro Factura'] or '-'}"
                else:
                    txt = str(row.get('Descripción', 'Ítem'))
                
                pdf.cell(130, 5, f" - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    draw_table("PAGO PROVEEDORES", tablas_data['prov'], tipo='prov')
    draw_table("TRANSFERENCIAS (Entrantes)", tablas_data['transf'])
    draw_table("GASTOS VARIOS", tablas_data['salidas'])
    draw_table("VALES", tablas_data['vales'])
    draw_table("ERRORES BALANZA", tablas_data['errores'])
    draw_table("DESCUENTOS", tablas_data['desc'])

    # Resultado Final
    y = pdf.get_y()
    if y > 250: pdf.add_page(); y = 20
    
    dif = kpis['diferencia']
    estado, color = ("FALTANTE", (200, 0, 0)) if dif > 0 else ("SOBRANTE", (0, 100, 0))
    if dif == 0: estado, color = ("OK", (0, 0, 0))
    
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color)
    pdf.cell(0, 14, f"CAJA REAL: $ {dif:,.2f} ({estado})", ln=1, align='C', border=1)
    
    return pdf.output(dest="S").encode("latin-1")

# ==============================================================================
# 6. UI COMPONENTES (HELPER FUNCTIONS)
# ==============================================================================
def render_tabla(titulo, key, simple=False):
    """Renderiza una tabla de entrada limpia sin índice."""
    st.markdown(f"**{titulo}**")
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", width="medium")}
    
    if not simple:
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    
    # hide_index=True es CLAVE para el minimalismo
    df = st.data_editor(
        st.session_state[key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_{key}",
        hide_index=True
    )
    # Sincronización inmediata
    st.session_state[key] = df
    return df, (df["Monto"].sum() if not df.empty else 0.0)

# ==============================================================================
# 7. INTERFAZ PRINCIPAL (MAIN LOOP)
# ==============================================================================

# --- CABECERA ---
st.title("Estancia San Francisco")
col_h1, col_h2 = st.columns(2)
with col_h1: fecha_input = st.date_input("Fecha", datetime.today())
with col_h2: cajero = st.selectbox("Cajero", ["Santiago", "Leandro", "Natalia"])

st.markdown("---")

# --- BLOQUE 1: AJUSTES Y ENTRADAS ---
col_izq, col_der = st.columns(2, gap="medium")

with col_izq:
    # Descuentos (Solo Lun/Mie)
    dia = fecha_input.weekday()
    df_desc = pd.DataFrame(columns=["Monto"])
    total_desc = 0.0
    if dia in [0, 2]:
        df_desc, total_desc = render_tabla("Somos Avellaneda", "df_descuentos", simple=True)
    
    # Vales
    df_vales, total_vales = render_tabla("Vales / Fiados", "df_vales")

with col_der:
    # Transferencias Entrantes
    df_transf, total_transf_in = render_tabla("Transferencias (Clientes)", "df_transferencias", simple=True)
    
    # Gastos Varios
    df_salidas, total_salidas = render_tabla("Gastos Varios (Salidas)", "df_salidas")

st.markdown("---")

# --- BLOQUE 2: PROVEEDORES (NUEVO DISEÑO) ---
st.markdown("### Pago a Proveedores")
cfg_prov = {
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=LISTA_PROVEEDORES, required=True, width="medium"),
    "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"], required=True, width="small"),
    "Nro Factura": st.column_config.TextColumn("Factura", width="medium"), 
    "Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)
}

df_prov = st.data_editor(
    st.session_state.df_proveedores, 
    column_config=cfg_prov, 
    num_rows="dynamic", 
    use_container_width=True, 
    hide_index=True,
    key="editor_prov"
)
st.session_state.df_proveedores = df_prov # Sincronizar

# Totales Proveedores
prov_efectivo = df_prov[df_prov["Forma Pago"] == "Efectivo"]["Monto"].sum()
prov_digital = df_prov[df_prov["Forma Pago"] == "Digital / Banco"]["Monto"].sum()

if prov_efectivo > 0 or prov_digital > 0:
    c_p1, c_p2 = st.columns(2)
    c_p1.metric("Resta de Caja (Efvo)", f"${prov_efectivo:,.0f}")
    c_p2.metric("Pago Digital", f"${prov_digital:,.0f}")

st.markdown("---")

# --- BLOQUE 3: EL NÚCLEO (Balanza, Efectivo, Digital) ---
st.markdown("### Arqueo de Caja")

# Fila 1: Objetivos
c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
with c_kpi1: registradora_z = st.number_input("Ticket Z (Fiscal)", step=100.0)
with c_kpi2: balanza_total = st.number_input("Total Balanza", step=100.0)
with c_kpi3: st.markdown("##### 💵 Efectivo (Billetes)")

# Calculadora Ocultable (Minimalismo)
with st.expander("Abrir Calculadora de Billetes", expanded=False):
    cc1, cc2, cc3, cc4 = st.columns(4)
    b20k = cc1.number_input("$20.000", 0); b10k = cc2.number_input("$10.000", 0)
    b2k = cc3.number_input("$2.000", 0); b1k = cc4.number_input("$1.000", 0)
    b500 = cc1.number_input("$500", 0); b200 = cc2.number_input("$200", 0)
    b100 = cc3.number_input("$100", 0); mon = cc4.number_input("Monedas", 0.0)
    
    total_billetes = (b20k*20000)+(b10k*10000)+(b2k*2000)+(b1k*1000)+(b500*500)+(b200*200)+(b100*100)+mon

# Muestra del efectivo final
if total_billetes > 0:
    st.success(f"Efectivo Contado: ${total_billetes:,.2f}")

# Fila 2: Digital
st.caption("Cobros Digitales")
cd1, cd2, cd3, cd4 = st.columns(4)
mp = cd1.number_input("MercadoPago", step=100.0)
nave = cd2.number_input("Nave", step=100.0)
clover = cd3.number_input("Clover", step=100.0)
bbva = cd4.number_input("BBVA", step=100.0)
total_digital = mp + nave + clover + bbva

# Errores
df_errores, total_errores = render_tabla("Errores Balanza", "df_errores", simple=True)

st.markdown("---")

# ==============================================================================
# 8. CÁLCULOS Y RESULTADOS
# ==============================================================================
# Lógica Contable:
# Dinero que DEBERÍA HABER = Digital + Efectivo + Gastos + Pagos Efectivo + Errores + Vales + Descuentos
# Ojo: Transferencias entrantes justifican venta, suman al total justificado.

total_gastos_fisicos = total_salidas + prov_efectivo
total_justificado = (
    total_digital + 
    total_billetes + 
    total_transf_in + 
    total_gastos_fisicos + 
    total_errores + 
    total_vales + 
    total_desc
)

diferencia = balanza_total - total_justificado

# UI Resultado
c_res1, c_res2 = st.columns([2, 1])
with c_res1:
    lbl = "DIFERENCIA (CAJA REAL)"
    if diferencia > 0: st.metric(lbl, f"${diferencia:,.2f}", "Faltante", delta_color="inverse")
    elif diferencia < 0: st.metric(lbl, f"${diferencia:,.2f}", "Sobrante")
    else: st.metric(lbl, "$ 0.00", "OK")

with c_res2:
    # Preparar datos para PDF y Guardado
    kpis = {'balanza': balanza_total, 'efectivo': total_billetes, 'digital': total_digital, 'z': registradora_z, 'diferencia': diferencia}
    tablas_data = {'salidas': df_salidas, 'transf': df_transf, 'errores': df_errores, 'vales': df_vales, 'desc': df_desc, 'prov': df_prov}
    desglose_dig = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
    
    st.write("") # Espacio
    
    # 1. Botón PDF
    pdf_bytes = generar_pdf(fecha_input, cajero, kpis, tablas_data, desglose_dig)
    st.download_button("📄 Descargar PDF", pdf_bytes, f"Cierre_{fecha_input}.pdf", "application/pdf", use_container_width=True)
    
    # 2. Botón Guardar
    if conn:
        if st.button("☁️ Guardar Cierre", type="primary", use_container_width=True):
            estado = "FALTANTE" if diferencia > 0 else ("SOBRANTE" if diferencia < 0 else "OK")
            datos_save = {
                "Fecha": fecha_input.strftime("%d/%m/%Y"),
                "Cajero": cajero,
                "Balanza": balanza_total,
                "Digital": total_digital,
                "Efectivo": total_billetes,
                "Transferencias": total_transf_in,
                "Salidas": total_gastos_fisicos, # Varios + Prov Efectivo
                "Vales": total_vales,
                "Errores": total_errores,
                "Descuentos": total_desc,
                "Diferencia": diferencia,
                "Estado": estado
            }
            with st.spinner("Guardando..."):
                if guardar_cierre(datos_save, df_prov):
                    st.success("¡Guardado!")
                    st.balloons()

# --- Directorio Oculto al final ---
if not DF_DIRECTORIO.empty:
    with st.expander("Ver Datos de Proveedores"):
        st.dataframe(DF_DIRECTORIO, hide_index=True)
