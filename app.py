import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os
from streamlit_gsheets import GSheetsConnection # <--- NUEVA LIBRERÍA

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Cierre de Caja", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Esto busca las credenciales en st.secrets automáticamente
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. VARIABLES Y LIMPIEZA ---
if 'df_salidas' not in st.session_state: st.session_state.df_salidas = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_transferencias' not in st.session_state: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"])
if 'df_vales' not in st.session_state: st.session_state.df_vales = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_errores' not in st.session_state: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'df_descuentos' not in st.session_state: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

if 'Descripción' in st.session_state.df_transferencias.columns: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_errores.columns: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_descuentos.columns: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# --- 3. FUNCIÓN PDF (Misma que antes, resumida aquí para no ocupar espacio) ---
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto, 
                            caja_inicial, total_fisico, caja_proxima, retiro,
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # ... (ACÁ VA TODO EL CÓDIGO DE GENERAR PDF QUE YA TENÉS) ...
    # (Copialo del mensaje anterior para que esté completo)
    # Por brevedad en esta respuesta, asumo que ya lo tenés.
    
    # SOLO PARA QUE EL CÓDIGO CORRA, PONGO UNA VERSIÓN MÍNIMA AQUÍ:
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_font("Arial", '', 12); pdf.cell(0, 10, f"FECHA: {fecha} - CAJERO: {cajero}", ln=1)
    pdf.cell(0, 10, f"CAJA REAL: ${diferencia}", ln=1)
    return pdf.output(dest="S").encode("latin-1")


# --- 4. FUNCIÓN GUARDAR EN NUBE ---
def guardar_en_sheets(datos):
    try:
        # 1. Leemos la hoja actual
        df_google = conn.read()
        
        # 2. Creamos un DataFrame con la nueva fila
        # Convertimos la fecha a string para evitar problemas de formato
        nueva_fila = pd.DataFrame([datos])
        
        # 3. Concatenamos (Unimos lo viejo con lo nuevo)
        # fillna("") evita errores si hay celdas vacías
        df_actualizado = pd.concat([df_google, nueva_fila], ignore_index=True).fillna("")
        
        # 4. Subimos todo de vuelta a Google Sheets
        conn.update(data=df_actualizado)
        return True
    except Exception as e:
        st.error(f"Error al guardar en la nube: {e}")
        return False

# --- 5. INTERFAZ UI ---

st.markdown("## Cierre de Caja")
st.markdown("Estancia San Francisco")

c_head1, c_head2, c_head3 = st.columns([1, 1, 2])
with c_head1: fecha_input = st.date_input("Fecha", datetime.today())
with c_head2: cajero = st.text_input("Cajero", "Santiago")
with c_head3: pass

st.markdown("---")

col_izq, col_der = st.columns(2, gap="large")

with col_izq:
    st.subheader("1. Facturación y Digital")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: balanza_total = st.number_input("Total BALANZA ($)", 0.0, step=100.0)
        with c2: registradora_total = st.number_input("Ticket Z (Fiscal)", 0.0, step=100.0)

    st.caption("Posnets")
    with st.container(border=True):
        c_pos1, c_pos2 = st.columns(2)
        with c_pos1: mp = st.number_input("Mercado Pago", 0.0, step=100.0); nave = st.number_input("Nave", 0.0, step=100.0)
        with c_pos2: clover = st.number_input("Clover", 0.0, step=100.0); bbva = st.number_input("BBVA", 0.0, step=100.0)
    
    total_digital = mp + nave + clover + bbva
    if total_digital > 0: st.info(f"Digital: ${total_digital:,.2f}")

with col_der:
    st.subheader("2. Efectivo")
    with st.container(border=True):
        st.caption("Billetes")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1: b_20000 = st.number_input("$20k", 0); b_500 = st.number_input("$500", 0)
        with col_b2: b_10000 = st.number_input("$10k", 0); b_200 = st.number_input("$200", 0)
        with col_b3: b_2000 = st.number_input("$2k", 0); b_100 = st.number_input("$100", 0)
        with col_b4: b_1000 = st.number_input("$1k", 0); monedas = st.number_input("Mon", 0.0)

        total_fisico = (b_20000*20000)+(b_10000*10000)+(b_2000*2000)+(b_1000*1000)+(b_500*500)+(b_200*200)+(b_100*100)+monedas
        st.markdown(f"**Contado: ${total_fisico:,.2f}**")
        
        caja_inicial = st.number_input("(-) Caja Inicial", 0.0, step=100.0)
        efectivo_neto = total_fisico - caja_inicial
        
        if efectivo_neto < 0: st.error(f"Físico Negativo: ${efectivo_neto:,.2f}")
        else: st.caption(f"Neto Ventas: ${efectivo_neto:,.2f}")

    with st.container(border=True):
        c_dest1, c_dest2 = st.columns(2)
        with c_dest1: caja_proxima = st.number_input("Queda Mañana", 0.0, step=100.0)
        with c_dest2: st.metric("Se Retira", f"${total_fisico - caja_proxima:,.2f}")

st.markdown("---")
st.subheader("3. Ajustes y Transferencias")

col_aj1, col_aj2 = st.columns(2)
def tabla_min(titulo, key, solo_monto=False):
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d")}
    if not solo_monto: cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    st.caption(f"**{titulo}**")
    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}")
    return df, (df["Monto"].sum() if not df.empty else 0.0)

with col_aj1:
    df_transferencias, total_transf = tabla_min("Transferencias", "df_transferencias", True)
    df_salidas, total_salidas = tabla_min("Gastos / Salidas", "df_salidas", False)

with col_aj2:
    df_vales, total_vales = tabla_min("Vales / Fiados", "df_vales", False)
    df_errores, total_errores = tabla_min("Errores Facturación", "df_errores", True)
    
    dia_semana = fecha_input.weekday()
    total_descuentos = 0.0
    df_descuentos = pd.DataFrame(columns=["Monto"])
    if dia_semana in [0, 2]: 
        df_descuentos, total_descuentos = tabla_min("Somos Avellaneda", "df_descuentos", True)

# CÁLCULOS
total_justificado = total_digital + efectivo_neto + total_transf + total_salidas + total_errores + total_vales + total_descuentos
diferencia = balanza_total - total_justificado
retiro = total_fisico - caja_proxima

# --- BARRA FINAL DE ACCIONES ---
st.markdown("---")
c_res1, c_res2, c_res3 = st.columns([1, 2, 2]) # Más espacio a la derecha para botones

with c_res1:
    st.metric("Total Balanza", f"${balanza_total:,.2f}")
    st.caption(f"Justificado: ${total_justificado:,.2f}")

with c_res2:
    lbl = "CAJA REAL"
    val = f"${diferencia:,.2f}"
    if diferencia > 0: st.metric(lbl, val, "Faltante", delta_color="inverse")
    elif diferencia < 0: st.metric(lbl, val, "Sobrante")
    else: st.metric(lbl, val, "OK")

with c_res3:
    st.write("") 
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # BOTÓN PDF
        if st.button("📄 Generar PDF", use_container_width=True):
            desglose_digital = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
            pdf_bytes = generar_pdf_profesional(
                fecha_input, cajero, balanza_total, registradora_total, total_digital, 
                efectivo_neto, caja_inicial, total_fisico, caja_proxima, retiro,
                df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, 
                diferencia, desglose_digital
            )
            st.download_button("📥 Descargar", data=pdf_bytes, file_name=f"Cierre_{fecha_input}.pdf", mime="application/pdf", use_container_width=True)

    with col_btn2:
        # BOTÓN GUARDAR EN NUBE
        if st.button("☁️ Guardar en Nube", type="primary", use_container_width=True):
            # Preparamos los datos para la fila de Excel
            estado_caja = "OK"
            if diferencia > 0: estado_caja = "FALTANTE"
            elif diferencia < 0: estado_caja = "SOBRANTE"
            
            datos_para_guardar = {
                "Fecha": fecha_input.strftime("%d/%m/%Y"),
                "Cajero": cajero,
                "Total Balanza": balanza_total,
                "Total Digital": total_digital,
                "Total Efectivo": efectivo_neto,
                "Transferencias": total_transf,
                "Salidas": total_salidas,
                "Vales": total_vales,
                "Errores": total_errores,
                "Descuentos": total_descuentos,
                "Diferencia Real": diferencia,
                "Estado": estado_caja
            }
            
            with st.spinner("Guardando en Google Sheets..."):
                exito = guardar_en_sheets(datos_para_guardar)
                if exito:
                    st.success("✅ ¡Guardado Correctamente!")
                    st.balloons()
