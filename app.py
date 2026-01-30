import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN Y LOGIN ---
st.set_page_config(page_title="Cierre de Caja", layout="centered")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 2rem; padding-bottom: 2rem;} 
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 🔐 SISTEMA DE LOGIN
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["general"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Acceso Restringido")
    st.text_input("Ingresá la contraseña del local:", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Contraseña incorrecta")
    return False

if not check_password():
    st.stop()

# --- CONEXIÓN GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    pass

# --- 2. CARGA DE DATOS MAESTROS ---
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"]
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
if 'df_salidas' not in st.session_state: st.session_state.df_salidas = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_transferencias' not in st.session_state: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"])
if 'df_vales' not in st.session_state: st.session_state.df_vales = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_errores' not in st.session_state: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'df_descuentos' not in st.session_state: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])
if 'df_proveedores' not in st.session_state: st.session_state.df_proveedores = pd.DataFrame(columns=["Proveedor", "Forma Pago", "Nro Factura", "Monto"])

# Limpiezas
if 'Descripción' in st.session_state.df_transferencias.columns: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_errores.columns: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_descuentos.columns: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# --- 4. FUNCIÓN DE GUARDADO ---
def guardar_todo_en_nube(datos_cierre, df_provs):
    try:
        # A. Historial
        df_historial = conn.read(worksheet="Historial")
        fila_cierre = pd.DataFrame([datos_cierre])
        df_historial_upd = pd.concat([df_historial, fila_cierre], ignore_index=True).fillna("")
        conn.update(worksheet="Historial", data=df_historial_upd)
        
        # B. Proveedores
        pagos_reales = df_provs[df_provs["Monto"] > 0].copy()
        if not pagos_reales.empty:
            pagos_reales["Fecha"] = datos_cierre["Fecha"]
            pagos_reales["Cajero"] = datos_cierre["Cajero"]
            pagos_reales = pagos_reales[["Fecha", "Proveedor", "Forma Pago", "Nro Factura", "Monto", "Cajero"]]
            
            df_pagos_ant = conn.read(worksheet="Pagos_Proveedores")
            df_pagos_upd = pd.concat([df_pagos_ant, pagos_reales], ignore_index=True).fillna("")
            conn.update(worksheet="Pagos_Proveedores", data=df_pagos_upd)
        return True
    except Exception as e:
        st.error(f"Error guardando en nube: {e}")
        return False

# --- 5. FUNCIÓN PDF ---
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto, 
                            caja_inicial, total_fisico, caja_proxima, retiro,
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, df_proveedores, diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    nombre_dia = dias_semana[fecha.weekday()] 
    fecha_texto = f"{nombre_dia} {fecha.strftime('%d/%m/%Y')}"

    pdf.set_xy(50, 12); pdf.set_font("Arial", 'B', 18); pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10); pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R')
    pdf.set_x(130); pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R')
    pdf.ln(15); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"CAJA INICIAL (Apertura): $ {caja_inicial:,.2f}", ln=1, align='L')
    pdf.ln(3)

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

    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE DIGITAL", ln=1); pdf.set_font("Arial", '', 9)
    for k, v in desglose_digital.items():
        if v > 0: pdf.cell(130, 5, f" - {k}"); pdf.cell(40, 5, f"$ {v:,.2f}", align='R', ln=1)
    
    pdf.ln(3); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE EFECTIVO", ln=1); pdf.set_font("Arial", '', 9)
    pdf.cell(130, 5, " - Recuento Total Cajón"); pdf.cell(40, 5, f"$ {total_fisico:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, " - (Menos) Caja Inicial"); pdf.cell(40, 5, f"-$ {caja_inicial:,.2f}", align='R', ln=1)
    
    pdf.ln(2); pdf.set_font("Arial", 'B', 9); pdf.cell(130, 5, "DESTINO:"); pdf.set_font("Arial", '', 9)
    pdf.cell(40, 5, "", ln=1)
    pdf.cell(130, 5, "   -> Queda (Caja Mañana):"); pdf.cell(40, 5, f"$ {caja_proxima:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, "   -> Se Retira:"); pdf.cell(40, 5, f"$ {retiro:,.2f}", align='R', ln=1)

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "C. AJUSTES Y PROVEEDORES", ln=1)

    def dibujar_tabla(titulo, df, estilo="lista", label_fijo=None):
        if df.empty or df['Monto'].sum() == 0: return
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 9)
        if estilo == 'grilla':
            col_count = 0; ancho_col = 45 
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    pdf.cell(ancho_col, 6, f"$ {row['Monto']:,.0f}", align='C', border=0); col_count += 1
                    if col_count % 4 == 0: pdf.ln()
            if col_count % 4 != 0: pdf.ln()     
        else:
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    txt = str(row['Descripción']) if estilo == 'lista' else label_fijo
                    pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    def dibujar_tabla_proveedores(df):
        if df.empty or df['Monto'].sum() == 0: return
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  PAGO A PROVEEDORES (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 8)
        pdf.cell(50, 5, "PROVEEDOR", 1); pdf.cell(30, 5, "METODO", 1); pdf.cell(40, 5, "FACTURA", 1); pdf.cell(30, 5, "MONTO", 1, ln=1)
        for _, row in df.iterrows():
            if row['Monto'] > 0:
                prov = str(row['Proveedor']); met = str(row['Forma Pago'])
                fac = str(row['Nro Factura']) if row['Nro Factura'] else "-"
                pdf.cell(50, 5, prov, 1); pdf.cell(30, 5, met, 1); pdf.cell(40, 5, fac, 1); pdf.cell(30, 5, f"$ {row['Monto']:,.2f}", 1, ln=1)
        pdf.ln(2)

    dibujar_tabla_proveedores(df_proveedores)
    dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transferencias, estilo='fijo', label_fijo="Transferencia")
    dibujar_tabla("GASTOS VARIOS / SALIDAS", df_salidas, estilo='lista')
    dibujar_tabla("VALES / FIADOS", df_vales, estilo='lista')
    dibujar_tabla("ERRORES DE BALANZA", df_errores, estilo='fijo', label_fijo="Error de Facturación")
    dibujar_tabla("DESCUENTOS AVELLANEDA", df_descuentos, estilo='grilla')

    y_start_box = pdf.get_y()
    if y_start_box > 250: pdf.add_page(); y_start_box = 20
    estado, color_texto = ("FALTANTE", (200, 0, 0)) if diferencia > 0 else ("SOBRANTE", (0, 100, 0))
    if diferencia == 0: estado, color_texto = ("OK", (0, 0, 0))
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color_texto)
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1); pdf.set_text_color(0, 0, 0)
    pdf.ln(5); pdf.set_font("Arial", 'B', 9); pdf.cell(0, 5, "OBSERVACIONES:", ln=1)
    return pdf.output(dest="S").encode("latin-1")


# --- 5. INTERFAZ UI ---
def input_tabla(titulo, key, solo_monto=False):
    st.markdown(f"**{titulo}**")
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", width="medium")}
    if not solo_monto: cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}")
    return df, (df["Monto"].sum() if not df.empty else 0.0)

# --- FORMULARIO ---
st.title("Estancia San Francisco")

# 1. FECHA y CAJA ANTERIOR
c1, c2 = st.columns(2)
with c1: fecha_input = st.date_input("Fecha", datetime.today())
with c2: caja_inicial = st.number_input("Caja (Día Anterior)", 0.0, step=100.0)
cajero = st.selectbox("Cajero de Turno", ["Santiago", "Leandro", "Natalia"])
st.markdown("---")

# 2. SOMOS AVELLANEDA
dia_semana = fecha_input.weekday()
df_descuentos = pd.DataFrame(columns=["Monto"])
total_descuentos = 0.0
if dia_semana in [0, 2]:
    df_descuentos, total_descuentos = input_tabla("Somos Avellaneda", "df_descuentos", solo_monto=True)
    st.caption(f"Total Descuentos: ${total_descuentos:,.2f}")
    st.markdown("---")

# 3. VALES
df_vales, total_vales = input_tabla("Vales", "df_vales", solo_monto=False)
st.caption(f"Total Vales: ${total_vales:,.2f}")
st.markdown("---")

# 4. TRANSFERENCIAS (ENTRANTES)
df_transferencias, total_transf_in = input_tabla("Transferencias (Entrantes / Clientes)", "df_transferencias", solo_monto=True)
st.caption(f"Total Transferencias: ${total_transf_in:,.2f}")
st.markdown("---")

# 5. REGISTRADORA | BALANZA | EFECTIVO
col_core1, col_core2, col_core3 = st.columns(3)
with col_core1: registradora_total = st.number_input("Registradora (Z)", 0.0, step=100.0)
with col_core2: balanza_total = st.number_input("Balanza", 0.0, step=100.0)
with col_core3: st.markdown("**Efectivo (Físico)**")

with st.expander("🧮 Calculadora de Billetes", expanded=True):
    cb1, cb2, cb3, cb4 = st.columns(4)
    with cb1: b_20000 = st.number_input("$20k", 0); b_500 = st.number_input("$500", 0)
    with cb2: b_10000 = st.number_input("$10k", 0); b_200 = st.number_input("$200", 0)
    with cb3: b_2000 = st.number_input("$2k", 0); b_100 = st.number_input("$100", 0)
    with cb4: b_1000 = st.number_input("$1k", 0); monedas = st.number_input("Mon", 0.0)
    total_fisico = (b_20000*20000)+(b_10000*10000)+(b_2000*2000)+(b_1000*1000)+(b_500*500)+(b_200*200)+(b_100*100)+monedas

st.info(f"💵 Total Efectivo: ${total_fisico:,.2f}")
efectivo_neto = total_fisico - caja_inicial
st.markdown("---")

# 6. DIGITAL
st.markdown("**Cobros Digitales**")
cd1, cd2, cd3, cd4 = st.columns(4)
with cd1: mp = st.number_input("Mercado Pago", 0.0, step=100.0)
with cd2: nave = st.number_input("Nave", 0.0, step=100.0)
with cd3: clover = st.number_input("Clover", 0.0, step=100.0)
with cd4: bbva = st.number_input("BBVA", 0.0, step=100.0)
total_digital = mp + nave + clover + bbva
st.caption(f"TOTAL DIGITAL: ${total_digital:,.2f}")
st.markdown("---")

# 7. ERRORES
df_errores, total_errores = input_tabla("Errores", "df_errores", solo_monto=True)
st.caption(f"Total Errores: ${total_errores:,.2f}")
st.markdown("---")

# 8. PAGO A PROVEEDORES
st.markdown("**Pago a Proveedores**")
columnas_proveedores = {
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True, width="medium"),
    "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"], required=True, width="small"),
    "Nro Factura": st.column_config.TextColumn("Nro Factura", width="medium"),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0)
}
df_proveedores = st.data_editor(st.session_state.df_proveedores, column_config=columnas_proveedores, num_rows="dynamic", use_container_width=True, key="ed_proveedores")

total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum()
total_prov_digital = df_proveedores[df_proveedores["Forma Pago"] == "Digital / Banco"]["Monto"].sum()

if total_prov_efectivo > 0: st.warning(f"📉 Se descontarán ${total_prov_efectivo:,.2f} de la CAJA (Pagos en Efectivo).")
if total_prov_digital > 0: st.info(f"ℹ️ Pagos Digitales/Banco: ${total_prov_digital:,.2f} (No afectan caja).")
st.markdown("---")

# 9. SALIDA DE CAJA (GASTOS VARIOS)
df_salidas, total_salidas = input_tabla("Salida de Caja (Gastos Varios Local)", "df_salidas", solo_monto=False)
st.caption(f"Total Salidas Varios: ${total_salidas:,.2f}")
st.markdown("---")

# 10. RESULTADO
col_dest1, col_dest2 = st.columns(2)
with col_dest1: caja_proxima = st.number_input("Queda para Mañana", 0.0, step=100.0)
with col_dest2: retiro = total_fisico - caja_proxima

# CÁLCULOS FINALES
total_gastos_fisicos = total_salidas + total_prov_efectivo
total_justificado = total_digital + efectivo_neto + total_transf_in + total_gastos_fisicos + total_errores + total_vales + total_descuentos
diferencia = balanza_total - total_justificado

st.markdown("### Resultado")
col_final1, col_final2 = st.columns([2, 1])

with col_final1:
    lbl = "CAJA REAL"
    val = f"${diferencia:,.2f}"
    if diferencia > 0: st.metric(lbl, val, "Faltante", delta_color="inverse")
    elif diferencia < 0: st.metric(lbl, val, "Sobrante")
    else: st.metric(lbl, val, "OK")

with col_final2:
    st.write("")
    if st.button("📄 Generar PDF", use_container_width=True):
        desglose_digital = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
        pdf_bytes = generar_pdf_profesional(
            fecha_input, cajero, balanza_total, registradora_total, total_digital, 
            efectivo_neto, caja_inicial, total_fisico, caja_proxima, retiro,
            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, df_proveedores,
            diferencia, desglose_digital
        )
        st.download_button("Descargar", data=pdf_bytes, file_name=f"Cierre_{fecha_input}.pdf", mime="application/pdf", use_container_width=True)
    
    if 'conn' in globals():
        if st.button("☁️ Guardar Nube", use_container_width=True):
            estado_caja = "FALTANTE" if diferencia > 0 else ("SOBRANTE" if diferencia < 0 else "OK")
            total_salidas_reporte = total_salidas + total_prov_efectivo
            datos_cierre = {
                "Fecha": fecha_input.strftime("%d/%m/%Y"), "Cajero": cajero,
                "Balanza": balanza_total, "Digital": total_digital, "Efectivo": efectivo_neto,
                "Transferencias": total_transf_in, "Salidas": total_salidas_reporte, "Vales": total_vales,
                "Errores": total_errores, "Descuentos": total_descuentos, "Diferencia": diferencia, "Estado": estado_caja
            }
            with st.spinner("Guardando..."):
                if guardar_todo_en_nube(datos_cierre, df_proveedores):
                    st.success("✅ Guardado Correctamente")
                    st.balloons()

# --- DIRECTORIO AL FINAL ---
st.markdown("---")
if not df_directorio.empty:
    with st.expander("📖 Ver Directorio de Proveedores (Alias/CUIT)"):
        st.dataframe(df_directorio, use_container_width=True)
