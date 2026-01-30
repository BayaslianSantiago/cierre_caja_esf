import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os

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

# --- 2. VARIABLES Y LIMPIEZA ---
# Inicialización
if 'df_salidas' not in st.session_state: st.session_state.df_salidas = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_transferencias' not in st.session_state: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"]) # Solo monto ahora
if 'df_vales' not in st.session_state: st.session_state.df_vales = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_errores' not in st.session_state: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'df_descuentos' not in st.session_state: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# Limpieza de columnas viejas (SEGURIDAD)
# Si Transferencias tenía descripción antes, la borramos para que no choque con la nueva estructura
if 'Descripción' in st.session_state.df_transferencias.columns: st.session_state.df_transferencias = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_errores.columns: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_descuentos.columns: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# --- 3. FUNCIÓN PDF ---
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto, 
                            caja_inicial, total_fisico, caja_proxima, retiro,
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # LOGO
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 

    # TÍTULOS
    pdf.set_xy(50, 12)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
    pdf.set_xy(50, 20)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1)

    pdf.set_xy(140, 12)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 6, f"FECHA: {fecha.strftime('%d/%m/%Y')}", ln=1, align='R')
    pdf.set_x(140)
    pdf.cell(50, 6, f"CAJERO: {cajero}", ln=1, align='R')
    
    pdf.ln(15)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)

    # CAJA INICIAL
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"CAJA INICIAL (Apertura): $ {caja_inicial:,.2f}", ln=1, align='L')
    pdf.ln(3)

    # BLOQUE KPIs (ETIQUETAS CORREGIDAS)
    def dibujar_kpi(titulo, monto):
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"{titulo}: $ {monto:,.2f}", ln=1, align='C', fill=True, border=1)
        pdf.ln(2) 

    dibujar_kpi("1. BALANZA", balanza)     # Corrección solicitada
    dibujar_kpi("2. EFECTIVO", efectivo_neto) # Corrección solicitada
    dibujar_kpi("3. DIGITAL", total_digital)
    
    # Z (Informativo)
    pdf.ln(2)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {registradora:,.2f}", border=0, align='C', ln=1)
    pdf.ln(5)

    # DETALLES (A y B)
    # A. Digital
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE DIGITAL", ln=1)
    pdf.set_font("Arial", '', 9)
    for k, v in desglose_digital.items():
        if v > 0:
            pdf.cell(130, 5, f" - {k}"); pdf.cell(40, 5, f"$ {v:,.2f}", align='R', ln=1)
    
    # B. Efectivo
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "DETALLE EFECTIVO", ln=1)
    pdf.set_font("Arial", '', 9)
    pdf.cell(130, 5, " - Recuento Total Cajón"); pdf.cell(40, 5, f"$ {total_fisico:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, " - (Menos) Caja Inicial"); pdf.cell(40, 5, f"-$ {caja_inicial:,.2f}", align='R', ln=1)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(130, 5, "DESTINO:"); pdf.set_font("Arial", '', 9)
    pdf.cell(40, 5, "", ln=1)
    pdf.cell(130, 5, "   -> Queda (Caja Mañana):"); pdf.cell(40, 5, f"$ {caja_proxima:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, "   -> Se Retira:"); pdf.cell(40, 5, f"$ {retiro:,.2f}", align='R', ln=1)

    # C. LISTAS
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "C. AJUSTES, TRANSFERENCIAS Y OTROS", ln=1)

    def dibujar_tabla(titulo, df, estilo="lista", label_fijo=None):
        if df.empty or df['Monto'].sum() == 0: return
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True)
        pdf.set_font("Arial", '', 9)
        
        if estilo == 'grilla':
            col_count = 0; ancho_col = 45 
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    pdf.cell(ancho_col, 6, f"$ {row['Monto']:,.0f}", align='C', border=0)
                    col_count += 1
                    if col_count % 4 == 0: pdf.ln()
            if col_count % 4 != 0: pdf.ln()     
        else:
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    # Si es lista con descripción, usa la col Descripción. Si es fijo, usa label_fijo
                    txt = str(row['Descripción']) if estilo == 'lista' else label_fijo
                    pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    # Transferencias ahora usa estilo FIJO (Sin detalle, solo label)
    dibujar_tabla("TRANSFERENCIAS", df_transferencias, estilo='fijo', label_fijo="Transferencia")
    dibujar_tabla("GASTOS / SALIDAS", df_salidas, estilo='lista')
    dibujar_tabla("VALES / FIADOS", df_vales, estilo='lista')
    dibujar_tabla("ERRORES DE BALANZA", df_errores, estilo='fijo', label_fijo="Error de Facturación")
    dibujar_tabla("DESCUENTOS AVELLANEDA", df_descuentos, estilo='grilla')

    pdf.ln(5)

    # CAJA REAL (FONDO)
    y_start_box = pdf.get_y()
    if y_start_box > 250:
        pdf.add_page()
        y_start_box = 20

    estado, color_texto = "OK", (0, 0, 0)
    if diferencia > 0: estado, color_texto = "FALTANTE", (200, 0, 0)
    elif diferencia < 0: estado, color_texto = "SOBRANTE", (0, 100, 0)
        
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*color_texto)
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9); pdf.cell(0, 5, "OBSERVACIONES:", ln=1)
    
    return pdf.output(dest="S").encode("latin-1")

# --- 4. INTERFAZ UI ---

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
    # Transferencias ahora es solo monto (True)
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

st.markdown("---")
c_res1, c_res2, c_res3 = st.columns([1, 2, 1])

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
    if st.button("📄 Descargar Reporte PDF", type="primary", use_container_width=True):
        desglose_digital = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
        pdf_bytes = generar_pdf_profesional(
            fecha_input, cajero, balanza_total, registradora_total, total_digital, 
            efectivo_neto, caja_inicial, total_fisico, caja_proxima, retiro,
            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos, 
            diferencia, desglose_digital
        )
        st.download_button("Guardar PDF", data=pdf_bytes, file_name=f"Cierre_{fecha_input}.pdf", mime="application/pdf", use_container_width=True)
