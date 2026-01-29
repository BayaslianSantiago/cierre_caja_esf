import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import os

# --- 1. CONFIGURACIÓN MINIMALISTA ---
st.set_page_config(page_title="Cierre de Caja", layout="wide")

# Ocultar menú de hamburguesa y footer para limpieza visual absoluta
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INICIALIZACIÓN DE VARIABLES (SEGURIDAD) ---
# Creamos las tablas en memoria si no existen
if 'df_salidas' not in st.session_state: st.session_state.df_salidas = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_vales' not in st.session_state: st.session_state.df_vales = pd.DataFrame(columns=["Descripción", "Monto"])
if 'df_errores' not in st.session_state: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'df_descuentos' not in st.session_state: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# Limpieza preventiva por cambios de estructura anteriores
if 'Descripción' in st.session_state.df_errores.columns: st.session_state.df_errores = pd.DataFrame(columns=["Monto"])
if 'Descripción' in st.session_state.df_descuentos.columns: st.session_state.df_descuentos = pd.DataFrame(columns=["Monto"])

# --- 3. FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto, 
                            caja_inicial, total_fisico, caja_proxima, retiro,
                            df_salidas, df_errores, df_vales, df_descuentos, diferencia, desglose_digital):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # -- ENCABEZADO --
    if os.path.exists("logo.png"):
        try: pdf.image("logo.png", 15, 10, 30)
        except: pass 

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
    pdf.ln(5)

    # -- CAJA RESULTADO --
    y_start_box = pdf.get_y()
    estado, color_texto = "OK", (0, 0, 0)
    if diferencia > 0: estado, color_texto = "FALTANTE", (200, 0, 0)
    elif diferencia < 0: estado, color_texto = "SOBRANTE", (0, 100, 0)
        
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(*color_texto)
    pdf.cell(0, 10, f"CAJA REAL (Diferencia): $ {diferencia:,.2f} ({estado})", ln=1, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.rect(15, y_start_box, 180, 10)
    pdf.ln(5)

    # -- RESUMEN --
    pdf.set_font("Arial", '', 11)
    def linea_resumen(texto, monto, es_negrita=False):
        pdf.set_font("Arial", 'B' if es_negrita else '', 11)
        pdf.cell(130, 7, texto, border=0)
        pdf.cell(50, 7, f"$ {monto:,.2f}", border=0, align='R', ln=1)

    linea_resumen("FACTURACIÓN BALANZA (Objetivo):", balanza, True)
    linea_resumen("TOTAL JUSTIFICADO:", balanza - diferencia)
    pdf.set_text_color(100, 100, 100)
    linea_resumen("Ticket Fiscal (Registradora):", registradora)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(5)

    # -- KPIs --
    total_venta = total_digital + efectivo_neto
    pct_dig = (total_digital / total_venta * 100) if total_venta > 0 else 0
    pct_efc = (efectivo_neto / total_venta * 100) if total_venta > 0 else 0

    # -- SECCIÓN A: INGRESOS --
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "A. DINERO INGRESADO", ln=1); pdf.ln(2)
    
    # 1. Digital
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240)
    pdf.cell(180, 6, f"  1. DIGITAL: $ {total_digital:,.2f}  [{pct_dig:.1f}%]", ln=1, fill=True)
    pdf.set_font("Arial", '', 9)
    for k, v in desglose_digital.items():
        if v > 0:
            pct_int = (v/total_digital*100) if total_digital else 0
            pdf.cell(130, 5, f"      - {k} ({pct_int:.1f}%)"); pdf.cell(40, 5, f"$ {v:,.2f}", align='R', ln=1)
    pdf.ln(3)

    # 2. Efectivo
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(180, 6, f"  2. EFECTIVO NETO: $ {efectivo_neto:,.2f}  [{pct_efc:.1f}%]", ln=1, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(130, 5, "      - Recuento Total Cajón"); pdf.cell(40, 5, f"$ {total_fisico:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, "      - (Menos) Caja Inicial"); pdf.cell(40, 5, f"-$ {caja_inicial:,.2f}", align='R', ln=1)
    
    pdf.ln(2); pdf.set_font("Arial", 'B', 9)
    pdf.cell(130, 5, "DESTINO DEL EFECTIVO:", ln=1); pdf.set_font("Arial", '', 9)
    pdf.cell(130, 5, "      -> Queda (Caja Próximo Día):"); pdf.cell(40, 5, f"$ {caja_proxima:,.2f}", align='R', ln=1)
    pdf.cell(130, 5, "      -> Se Retira:"); pdf.cell(40, 5, f"$ {retiro:,.2f}", align='R', ln=1)
    pdf.ln(5)
    
    # -- SECCIÓN B: AJUSTES (CON GRILLA) --
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "B. AJUSTES Y SALIDAS", ln=1); pdf.ln(2)

    def dibujar_tabla(titulo, df, estilo="lista", label_fijo=None):
        if df.empty or df['Monto'].sum() == 0: return
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True)
        pdf.set_font("Arial", '', 9)
        
        if estilo == 'grilla':
            # MODO GRILLA (4 Columnas)
            col_count = 0
            ancho_col = 45 
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    pdf.cell(ancho_col, 6, f"$ {row['Monto']:,.0f}", align='C', border=0)
                    col_count += 1
                    if col_count % 4 == 0: pdf.ln()
            if col_count % 4 != 0: pdf.ln()
                
        else:
            # MODO LISTA
            for _, row in df.iterrows():
                if row['Monto'] > 0:
                    txt = str(row['Descripción']) if estilo == 'lista' else label_fijo
                    pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1)
        pdf.ln(2)

    dibujar_tabla("3. GASTOS / SALIDAS", df_salidas, estilo='lista')
    dibujar_tabla("4. VALES / FIADOS", df_vales, estilo='lista')
    dibujar_tabla("5. ERRORES DE BALANZA", df_errores, estilo='fijo', label_fijo="Error de Facturación")
    dibujar_tabla("6. DESCUENTOS AVELLANEDA", df_descuentos, estilo='grilla')

    pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(2)
    pdf.set_font("Arial", 'B', 9); pdf.cell(0, 5, "OBSERVACIONES:", ln=1)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. INTERFAZ UI ---

st.markdown("## Cierre de Caja")
st.markdown("Estancia San Francisco")

# CABECERA
c_head1, c_head2, c_head3 = st.columns([1, 1, 2])
with c_head1: fecha_input = st.date_input("Fecha", datetime.today())
with c_head2: cajero = st.text_input("Cajero", "Santiago")
with c_head3: pass

st.markdown("---")

# LAYOUT PRINCIPAL
col_izq, col_der = st.columns(2, gap="large")

with col_izq:
    st.subheader("1. Ingresos Digitales & Facturación")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: balanza_total = st.number_input("Total BALANZA ($)", 0.0, step=100.0)
        with c2: registradora_total = st.number_input("Ticket Z (Fiscal)", 0.0, step=100.0)

    st.caption("Terminales / Posnets")
    with st.container(border=True):
        c_pos1, c_pos2 = st.columns(2)
        with c_pos1:
            mp = st.number_input("Mercado Pago", 0.0, step=100.0)
            nave = st.number_input("Nave", 0.0, step=100.0)
        with c_pos2:
            clover = st.number_input("Clover", 0.0, step=100.0)
            bbva = st.number_input("BBVA", 0.0, step=100.0)
    
    total_digital = mp + nave + clover + bbva
    if total_digital > 0: st.info(f"Total Digital: ${total_digital:,.2f}")

with col_der:
    st.subheader("2. Arqueo de Efectivo")
    with st.container(border=True):
        st.caption("Calculadora de Billetes")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1: b_20000 = st.number_input("$ 20.000", 0); b_500 = st.number_input("$ 500", 0)
        with col_b2: b_10000 = st.number_input("$ 10.000", 0); b_200 = st.number_input("$ 200", 0)
        with col_b3: b_2000 = st.number_input("$ 2.000", 0); b_100 = st.number_input("$ 100", 0)
        with col_b4: b_1000 = st.number_input("$ 1.000", 0); monedas = st.number_input("Monedas $", 0.0)

        total_fisico = (b_20000*20000)+(b_10000*10000)+(b_2000*2000)+(b_1000*1000)+(b_500*500)+(b_200*200)+(b_100*100)+monedas
        st.markdown(f"**Total Contado: ${total_fisico:,.2f}**")
        
        caja_inicial = st.number_input("(-) Caja Inicial / Apertura", 0.0, step=100.0)
        efectivo_neto = total_fisico - caja_inicial
        
        if efectivo_neto < 0: st.error(f"Faltante físico: ${efectivo_neto:,.2f}")
        else: st.caption(f"Efectivo Neto Ventas: ${efectivo_neto:,.2f}")

    with st.container(border=True):
        st.caption("Destino del Efectivo")
        c_dest1, c_dest2 = st.columns(2)
        with c_dest1: caja_proxima = st.number_input("Para Mañana", 0.0, step=100.0)
        with c_dest2: 
            retiro = total_fisico - caja_proxima
            st.metric("Se Retira", f"${retiro:,.2f}")

# SECCIÓN INFERIOR
st.markdown("---")
st.subheader("3. Ajustes de Caja")

col_ajustes1, col_ajustes2 = st.columns(2)

def tabla_min(titulo, key, help_txt, solo_monto=False):
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d")}
    if not solo_monto:
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True)
    
    st.caption(f"**{titulo}**")
    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}")
    return df, (df["Monto"].sum() if not df.empty else 0.0)

with col_ajustes1:
    df_salidas, total_salidas = tabla_min("Gastos / Salidas", "df_salidas", "")
    df_errores, total_errores = tabla_min("Errores Facturación", "df_errores", "", True)

with col_ajustes2:
    df_vales, total_vales = tabla_min("Vales / Fiados", "df_vales", "")
    
    dia_semana = fecha_input.weekday()
    total_descuentos = 0.0
    df_descuentos = pd.DataFrame(columns=["Monto"])
    # Solo mostrar tabla si es Lunes(0) o Miércoles(2)
    if dia_semana in [0, 2]: 
        df_descuentos, total_descuentos = tabla_min("Desc. Somos Avellaneda", "df_descuentos", "", True)

# CÁLCULOS
total_justificado = total_digital + efectivo_neto + total_salidas + total_errores + total_vales + total_descuentos
diferencia = balanza_total - total_justificado

# BARRA RESULTADO
st.markdown("---")
c_res1, c_res2, c_res3 = st.columns([1, 2, 1])

with c_res1:
    st.metric("Total Balanza", f"${balanza_total:,.2f}")
    st.caption(f"Justificado: ${total_justificado:,.2f}")

with c_res2:
    lbl = "CAJA REAL (Diferencia)"
    val = f"${diferencia:,.2f}"
    if diferencia > 0: st.metric(lbl, val, "- Faltante", delta_color="inverse")
    elif diferencia < 0: st.metric(lbl, val, "+ Sobrante")
    else: st.metric(lbl, val, "OK")

with c_res3:
    st.write("") 
    if st.button("📄 Crear Reporte PDF", type="primary", use_container_width=True):
        desglose_digital = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva}
        pdf_bytes = generar_pdf_profesional(
            fecha_input, cajero, balanza_total, registradora_total, total_digital, 
            efectivo_neto, caja_inicial, total_fisico, caja_proxima, retiro,
            df_salidas, df_errores, df_vales, df_descuentos, 
            diferencia, desglose_digital
        )
        st.download_button("Guardar PDF", data=pdf_bytes, file_name=f"Cierre_{fecha_input}.pdf", mime="application/pdf", use_container_width=True)
