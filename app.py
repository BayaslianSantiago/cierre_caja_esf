import streamlit as st 
import pandas as pd 
from datetime import datetime 
from fpdf import FPDF 
import os 
from streamlit_gsheets import GSheetsConnection 
import streamlit.components.v1 as components 

# --- 1. CONFIGURACIÓN Y LOGIN --- 
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered") 

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

hide_st_style = """ 
            <style> 
            #MainMenu {visibility: hidden;} 
            footer {visibility: hidden;} 
            header {visibility: hidden;} 
            .block-container {padding-top: 2rem; padding-bottom: 2rem;}  
            </style> 
            """ 
st.markdown(hide_st_style, unsafe_allow_html=True) 

# SISTEMA DE LOGIN 
def check_password(): 
    def password_entered(): 
        if st.session_state["password"] == st.secrets["general"]["password"]: 
            st.session_state["password_correct"] = True 
            del st.session_state["password"] 
        else: 
            st.session_state["password_correct"] = False 

    if st.session_state.get("password_correct", False): 
        return True 

    st.title("Acceso Restringido") 
    st.text_input("Ingresá la contraseña del local:", type="password", on_change=password_entered, key="password") 
    if "password_correct" in st.session_state and not st.session_state["password_correct"]: 
        st.error("Contraseña incorrecta") 
    return False 

if not check_password(): 
    st.stop() 

# --- CONEXIÓN GOOGLE SHEETS --- 
try: 
    conn = st.connection("gsheets", type=GSheetsConnection) 
except: 
    st.error("Error de conexión con Google Sheets") 

# --- 2. CARGA DE DATOS MAESTROS --- 
lista_proveedores = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"] 
lista_cajeros = ["Leandro", "Natalia", "Santiago"] 
lista_empleados = ["Leandro", "Natalia", "Santiago", "Julieta", "Mariela", "Fernanda", "Brian", "Erika", "Oriana"] 

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
session_keys = { 
    'df_salidas': ["Descripción", "Monto"], 
    'df_transferencias': ["Monto"], 
    'df_vales': ["Descripción", "Monto"], 
    'df_errores': ["Descripción", "Monto"], 
    'df_descuentos': ["Descripción", "Monto"], 
    'df_proveedores': ["Proveedor", "Forma Pago", "Nro Factura", "Monto"], 
    'df_empleados': ["Empleado", "Monto"], 
    'df_calc_con': ["Monto"], 
    'df_calc_sin': ["Monto"]  
} 

for key, cols in session_keys.items(): 
    if key not in st.session_state: 
        st.session_state[key] = pd.DataFrame(columns=cols) 

# --- 4. FUNCIONES DE GUARDADO --- 
def guardar_todo_en_nube(datos_cierre, df_provs, df_empls): 
    try: 
        df_historial = conn.read(worksheet="Historial") 
        fila_cierre = pd.DataFrame([datos_cierre]) 
        df_historial_upd = pd.concat([df_historial, fila_cierre], ignore_index=True).fillna("") 
        conn.update(worksheet="Historial", data=df_historial_upd) 
         
        pagos_reales = df_provs[df_provs["Monto"] > 0].copy() 
        if not pagos_reales.empty: 
            pagos_reales["Fecha"] = datos_cierre["Fecha"] 
            pagos_reales["Cajero"] = datos_cierre["Cajero"] 
            df_pagos_ant = conn.read(worksheet="Pagos_Proveedores") 
            df_pagos_upd = pd.concat([df_pagos_ant, pagos_reales], ignore_index=True).fillna("") 
            conn.update(worksheet="Pagos_Proveedores", data=df_pagos_upd) 

        consumos_empl = df_empls[df_empls["Monto"] > 0].copy() 
        if not consumos_empl.empty: 
            consumos_empl["Fecha"] = datos_cierre["Fecha"] 
            consumos_empl = consumos_empl[["Fecha", "Empleado", "Monto"]] 
            df_empl_ant = conn.read(worksheet="Consumo_Empleados") 
            df_empl_upd = pd.concat([df_empl_ant, consumos_empl], ignore_index=True).fillna("") 
            conn.update(worksheet="Consumo_Empleados", data=df_empl_upd) 
             
        return True 
    except Exception as e: 
        st.error(f"Error guardando en nube: {e}") 
        return False 

# --- 5. FUNCIÓN PDF --- 
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto,  
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos,  
                            df_proveedores, df_empleados, diferencia, desglose_digital): 
    pdf = FPDF() 
    pdf.add_page() 
    pdf.set_margins(15, 15, 15) 
     
    if os.path.exists("logo.png"): 
        try: pdf.image("logo.png", 15, 10, 30) 
        except: pass  

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"] 
    fecha_texto = f"{dias_semana[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}" 

    pdf.set_xy(50, 12); pdf.set_font("Arial", 'B', 18); pdf.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1) 
    pdf.set_xy(50, 20); pdf.set_font("Arial", '', 12); pdf.cell(0, 8, "Reporte de Cierre de Caja", ln=1) 
    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10); pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R') 
    pdf.set_x(130); pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R') 
    pdf.ln(15); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(3) 

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

    def dibujar_tabla(titulo, df, label_fijo=None): 
        if df.empty or df['Monto'].sum() == 0: return 
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240) 
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 9) 
        for _, row in df.iterrows(): 
            if row['Monto'] > 0: 
                if 'Proveedor' in df.columns:
                    txt = f"{row['Proveedor']} ({row['Forma Pago']})"
                else:
                    txt = str(row.get('Descripción', row.get('Empleado', label_fijo))) 
                
                pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1) 
        pdf.ln(2) 

    dibujar_tabla("PAGO A PROVEEDORES", df_proveedores) 
    dibujar_tabla("MERCADERÍA EMPLEADOS", df_empleados) 
    dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transferencias, label_fijo="Transferencia") 
    dibujar_tabla("GASTOS VARIOS / SALIDAS", df_salidas) 
    dibujar_tabla("VALES / FIADOS", df_vales) 
    dibujar_tabla("ERRORES DE FACTURACIÓN", df_errores)  
    # Resumimos todos los descuentos en un solo renglón para no ocupar espacio
    if not df_descuentos.empty and df_descuentos['Monto'].sum() > 0:
        total_desc = df_descuentos['Monto'].sum()
        df_desc_resumido = pd.DataFrame([{"Descripción": "Total descuentos aplicados en el turno", "Monto": total_desc}])
        dibujar_tabla("DESCUENTOS Y PROMOS", df_desc_resumido)
     
    pdf.ln(5) 
    estado, color_texto = ("FALTANTE", (200, 0, 0)) if diferencia > 0 else ("SOBRANTE", (0, 100, 0)) 
    if diferencia == 0: estado, color_texto = ("OK", (0, 0, 0)) 
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color_texto) 
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1) 
     
    return pdf.output(dest="S").encode("latin-1") 

# --- 6. INTERFAZ UI --- 
def input_tabla(titulo, key, solo_monto=False): 
    st.markdown(f"**{titulo}**") 
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)} 
    if not solo_monto: cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # Al no reescribir manualmente st.session_state[key], Streamlit deja de robar el foco
    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}", hide_index=True) 
    
    return df, (df["Monto"].sum() if not df.empty else 0.0) 

st.title("Estancia San Francisco") 

col_enc1, col_enc2 = st.columns(2) 
with col_enc1: fecha_input = st.date_input("Fecha", datetime.today()) 
with col_enc2: cajero = st.selectbox("Cajero de Turno", lista_cajeros) 
st.markdown("---") 

# --- NUEVA FUNCIONALIDAD: CALCULADORA DE PROMOS --- 
es_dia_promo = fecha_input.weekday() in [0, 2] # 0=Lunes, 2=Miércoles 
if es_dia_promo: 
    st.info("Hoy hay Somos Avellaneda (10% / 15%)") 
    with st.popover("Somos Avellaneda"): 
        st.write("Ingrese los valores de los importes de los productos para el descuento:                                           ") 
         
        c_dto, s_dto = st.columns(2) 
         
        with c_dto: 
            st.markdown("**CON Descuento**") 
            df_calc_con = st.data_editor(st.session_state['df_calc_con'], column_config={"Monto": st.column_config.NumberColumn("Importe ($)", min_value=0.0)}, num_rows="dynamic", key="calc_con", use_container_width=True, hide_index=True) 
            monto_con_dto = df_calc_con["Monto"].sum() if not df_calc_con.empty else 0.0 
            st.caption(f"Subtotal: ${monto_con_dto:,.2f}") 

        with s_dto: 
            st.markdown("**SIN Descuento**") 
            df_calc_sin = st.data_editor(st.session_state['df_calc_sin'], column_config={"Monto": st.column_config.NumberColumn("Importe ($)", min_value=0.0)}, num_rows="dynamic", key="calc_sin", use_container_width=True, hide_index=True) 
            monto_sin_dto = df_calc_sin["Monto"].sum() if not df_calc_sin.empty else 0.0 
            st.caption(f"Subtotal: ${monto_sin_dto:,.2f}") 

        st.markdown("---") 
        tipo_dto = st.radio("Porcentaje de Tarjeta", [0.10, 0.15], format_func=lambda x: f"{int(x*100)}%", horizontal=True) 
         
        calculo_descuento = monto_con_dto * tipo_dto 
        total_a_cobrar = (monto_con_dto - calculo_descuento) + monto_sin_dto 
         
        st.markdown(f"### Cobrar: **${total_a_cobrar:,.2f}**") 
        st.caption(f"Descuento: ${calculo_descuento:,.2f}") 
         
        if st.button("Agregar descuento a la caja", use_container_width=True): 
            if calculo_descuento > 0: 
                # Tomamos la tabla de descuentos más reciente (que incluye las ediciones manuales)
                base_df = st.session_state.get("latest_df_descuentos", st.session_state.df_descuentos)
                
                # Le pegamos el nuevo cálculo
                nueva_fila = pd.DataFrame([{"Descripción": f"Promo {int(tipo_dto*100)}% Tarjeta", "Monto": calculo_descuento}]) 
                st.session_state.df_descuentos = pd.concat([base_df, nueva_fila], ignore_index=True) 
                 
                # Vaciamos la calculadora para el próximo cliente 
                st.session_state['df_calc_con'] = pd.DataFrame(columns=["Monto"]) 
                st.session_state['df_calc_sin'] = pd.DataFrame(columns=["Monto"]) 
                
                # Limpiamos los widgets gráficos para que se re-dibujen correctamente
                for widget_key in ["calc_con", "calc_sin", "ed_df_descuentos"]:
                    if widget_key in st.session_state:
                        del st.session_state[widget_key]
                 
                st.toast("Cobro registrado. Calculadora limpia.", icon="✅") 
                st.rerun() 
            else: 
                st.warning("No hay importes con descuento para aplicar.") 

# --- RESTO DE TABLAS --- 
df_vales, total_vales = input_tabla("Vales / Fiados", "df_vales") 
df_transferencias, total_transf_in = input_tabla("Transferencias (Entrantes)", "df_transferencias", solo_monto=True) 

df_errores, total_errores = input_tabla("Errores de Facturación", "df_errores") 

# Descuentos tiene un tratamiento especial para poder mezclarse con la calculadora sin romperse
df_descuentos, total_descuentos = input_tabla("Descuentos Promocionales", "df_descuentos") 
st.session_state["latest_df_descuentos"] = df_descuentos

# MERCADERÍA EMPLEADOS 
st.markdown("**Mercadería de Empleados**") 
cfg_emp = { 
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True), 
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0) 
} 

df_empleados = st.data_editor(st.session_state.df_empleados, column_config=cfg_emp, num_rows="dynamic", use_container_width=True, key="ed_emp", hide_index=True) 
total_empleados = df_empleados["Monto"].sum() 
st.markdown("---") 

# EFECTIVO Y DIGITAL 
col_core1, col_core2 = st.columns(2) 
with col_core1:  
    balanza_total = st.number_input("Total Balanza (Venta Real)", 0.0, step=100.0) 
    registradora_total = st.number_input("Registradora (Z)", 0.0, step=100.0) 
with col_core2: 
    with st.expander("Calculadora de Billetes", expanded=False): 
        b20k = st.number_input("$20k", 0); b10k = st.number_input("$10k", 0) 
        b2k = st.number_input("$2k", 0); b1k = st.number_input("$1k", 0) 
        total_fisico = (b20k*20000)+(b10k*10000)+(b2k*2000)+(b1k*1000) 
    efectivo_neto = st.number_input("Efectivo Total en Caja", value=float(total_fisico)) 

st.markdown("**Cobros Digitales**") 
cd1, cd2, cd3, cd4 = st.columns(4) 
mp = cd1.number_input("Mercado Pago", 0.0); nave = cd2.number_input("Nave", 0.0) 
clover = cd3.number_input("Clover", 0.0); bbva = cd4.number_input("BBVA", 0.0) 
total_digital = mp + nave + clover + bbva 
st.markdown("---") 

# PROVEEDORES Y SALIDAS 
st.markdown("**Pago a Proveedores**") 
cfg_prov = { 
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True), 
    "Forma Pago": st.column_config.SelectboxColumn("Método", options=["Efectivo", "Digital / Banco"], required=True), 
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%d", min_value=0) 
} 

df_proveedores = st.data_editor(st.session_state.df_proveedores, column_config=cfg_prov, num_rows="dynamic", use_container_width=True, key="ed_prov", hide_index=True) 
total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum() 

df_salidas, total_salidas = input_tabla("Gastos Varios (Salidas de Caja)", "df_salidas") 

# --- 7. RESULTADO FINAL --- 
st.markdown("### Resultado del Cierre") 

total_justificado = total_digital + efectivo_neto + total_transf_in + total_salidas + total_prov_efectivo + total_vales + total_empleados + total_errores + total_descuentos
diferencia = balanza_total - total_justificado 

c1, c2, c3 = st.columns(3) 
c1.metric("Diferencia", f"${diferencia:,.2f}", delta_color="inverse" if diferencia > 0 else "normal") 

if c2.button("Guardar en Drive", use_container_width=True): 
    # Calculamos el Estado de la caja
    if diferencia == 0:
        estado_caja = "OK"
    elif diferencia > 0:
        estado_caja = "FALTANTE"
    else:
        estado_caja = "SOBRANTE"

    # Datos completos para Google Sheets
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
    
    if guardar_todo_en_nube(datos, df_proveedores, df_empleados): 
        st.success("Guardado exitoso") 
        st.balloons() 

if c3.button("Generar PDF", use_container_width=True): 
    desglose = {"MP": mp, "Nave": nave, "Clover": clover, "BBVA": bbva} 
    pdf_bytes = generar_pdf_profesional(fecha_input, cajero, balanza_total, registradora_total,  
                                        total_digital, efectivo_neto, df_salidas, df_transferencias,  
                                        df_errores, df_vales, df_descuentos, df_proveedores,  
                                        df_empleados, diferencia, desglose) 
    st.download_button("Descargar PDF", pdf_bytes, f"Cierre_{fecha_input}.pdf", "application/pdf")
