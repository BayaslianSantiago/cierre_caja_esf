import streamlit as st 
import pandas as pd 
from datetime import datetime 
from fpdf import FPDF 
import os 
from streamlit_gsheets import GSheetsConnection 
import streamlit.components.v1 as components 
import plotly.express as px  

# --- 1. CONFIGURACIÓN Y LOGIN --- 
st.set_page_config(page_title="Cierre de Caja - Estancia San Francisco", layout="centered", initial_sidebar_state="collapsed") 

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
            footer {visibility: hidden;} 
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
    st.text_input("Ingresar la contrasena del local:", type="password", on_change=password_entered, key="password") 
    if "password_correct" in st.session_state and not st.session_state["password_correct"]: 
        st.error("Contrasena incorrecta") 
    return False 

if not check_password(): 
    st.stop() 

# --- CONEXIÓN GOOGLE SHEETS --- 
try: 
    conn = st.connection("gsheets", type=GSheetsConnection) 
except: 
    st.error("Error de conexion con Google Sheets") 

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

# --- SIDEBAR DE ANÁLISIS MENSUAL Y GLOSARIO ---
with st.sidebar:
    st.title("Analisis de Cierres")
    
    if 'conn' in globals():
        try:
            df_historial = conn.read(worksheet="Historial", ttl=600)
            
            try:
                df_empleados_bd = conn.read(worksheet="Consumo_Empleados", ttl=600)
            except:
                df_empleados_bd = pd.DataFrame() 

            if not df_historial.empty and "Fecha" in df_historial.columns:
                df_historial["Fecha_dt"] = pd.to_datetime(df_historial["Fecha"], format="%d/%m/%Y", errors="coerce")
                df_historial["Mes_Año"] = df_historial["Fecha_dt"].dt.strftime("%m/%Y")
                df_historial = df_historial.dropna(subset=["Fecha_dt"])
                
                meses_disponibles = df_historial["Mes_Año"].unique().tolist()
                meses_disponibles.sort(reverse=True)
                
                if meses_disponibles:
                    mes_seleccionado = st.selectbox("Seleccionar Mes", meses_disponibles)
                    
                    df_mes = df_historial[df_historial["Mes_Año"] == mes_seleccionado].copy()
                    
                    df_mes["Digital"] = pd.to_numeric(df_mes["Digital"], errors="coerce").fillna(0)
                    df_mes["Efectivo"] = pd.to_numeric(df_mes["Efectivo"], errors="coerce").fillna(0)
                    
                    tot_digital = df_mes["Digital"].sum()
                    tot_efectivo = df_mes["Efectivo"].sum()
                    
                    st.markdown("---")
                    st.subheader(f"Resumen {mes_seleccionado}")
                    
                    st.markdown("**Proporcion: Efectivo vs Digital**")
                    if tot_digital > 0 or tot_efectivo > 0:
                        df_pie = pd.DataFrame({
                            "Metodo": ["Efectivo", "Digital"],
                            "Monto": [tot_efectivo, tot_digital]
                        })
                        fig = px.pie(df_pie, values='Monto', names='Metodo', hole=0.3)
                        fig.update_traces(textinfo='percent', textposition='inside', hoverinfo='label+percent')
                        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=300, 
                                          legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay ingresos registrados este mes.")
                    
                    st.markdown("---")
                    
                    st.markdown("**Mercaderia por Empleado**")
                    if not df_empleados_bd.empty and "Fecha" in df_empleados_bd.columns:
                        df_empleados_bd["Fecha_dt"] = pd.to_datetime(df_empleados_bd["Fecha"], format="%d/%m/%Y", errors="coerce")
                        df_empleados_bd["Mes_Año"] = df_empleados_bd["Fecha_dt"].dt.strftime("%m/%Y")
                        
                        df_emp_mes = df_empleados_bd[df_empleados_bd["Mes_Año"] == mes_seleccionado].copy()
                        
                        if not df_emp_mes.empty:
                            df_emp_mes["Monto"] = pd.to_numeric(df_emp_mes["Monto"], errors="coerce").fillna(0)
                            consumo_agrupado = df_emp_mes.groupby("Empleado")["Monto"].sum().reset_index()
                            consumo_agrupado = consumo_agrupado[consumo_agrupado["Monto"] > 0].sort_values(by="Monto", ascending=False)
                            
                            if not consumo_agrupado.empty:
                                for _, row in consumo_agrupado.iterrows():
                                    st.write(f"**{row['Empleado']}**: ${row['Monto']:,.2f}")
                            else:
                                st.caption("Nadie retiro mercaderia este mes.")
                        else:
                            st.caption("No hay registros de mercaderia en este mes.")
                    else:
                        st.caption("No se encontro la tabla de Consumo_Empleados en Drive.")

                    st.markdown("---")
                    st.caption(f"Basado en {len(df_mes)} cierres de caja.")
                    
                else:
                    st.info("No hay fechas registradas con el formato correcto.")
            else:
                st.info("El historial esta vacio.")
        except Exception as e:
            st.error(f"Error cargando el analisis: {e}")

    # --- 3. GLOSARIO DE PROVEEDORES EN POPOVER ---
    st.markdown("---")
    with st.popover("Ver Glosario de Proveedores"):
        if not df_directorio.empty:
            columnas_deseadas = ["Proveedor", "Razon Social", "CUIT", "Alias/CBU", "Telefono"]
            columnas_disponibles = [col for col in columnas_deseadas if col in df_directorio.columns]
            
            if columnas_disponibles:
                st.dataframe(df_directorio[columnas_disponibles], hide_index=True, use_container_width=True)
            else:
                st.dataframe(df_directorio, hide_index=True, use_container_width=True)
        else:
            st.caption("No se encontraron datos de proveedores.")
        
    st.markdown("---")
    if st.button("Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

# --- 3. VARIABLES DE SESIÓN --- 
session_keys = { 
    'df_salidas': ["Descripción", "Monto"], 
    'df_transferencias': ["Monto"], 
    'df_vales': ["Descripción", "Monto"], 
    'df_errores': ["Monto"], 
    'df_descuentos': ["Monto"], 
    'df_proveedores': ["Proveedor", "Forma Pago", "Nro Factura", "Monto"], 
    'df_empleados': ["Empleado", "Ticket", "Monto"]
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
             
        st.cache_data.clear()
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

    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"] 
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
    
    # --- NUEVO: DESGLOSE DIGITAL EN EL PDF ---
    if desglose_digital:
        pdf.set_font("Arial", '', 9)
        for pos_nombre, pos_monto in desglose_digital.items():
            if pos_monto > 0:
                pdf.cell(130, 5, f"      - {pos_nombre}"); pdf.cell(40, 5, f"$ {pos_monto:,.2f}", align='R', ln=1)
        pdf.ln(2)
     
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
    dibujar_tabla("MERCADERIA EMPLEADOS", df_empleados) 
    
    if not df_transferencias.empty and df_transferencias['Monto'].sum() > 0:
        total_transf_acumulado = df_transferencias['Monto'].sum()
        df_transf_resumida = pd.DataFrame([{"Descripción": "Total transferencias entrantes", "Monto": total_transf_acumulado}])
        dibujar_tabla("TRANSFERENCIAS", df_transf_resumida)
        
    dibujar_tabla("SALIDA DE CAJA", df_salidas) 
    dibujar_tabla("VALES", df_vales) 
    
    if not df_errores.empty and df_errores['Monto'].sum() > 0:
        total_err_acumulado = df_errores['Monto'].sum()
        df_err_resumido = pd.DataFrame([{"Descripción": "Total errores registrados", "Monto": total_err_acumulado}])
        dibujar_tabla("ERRORES", df_err_resumido) 
        
    if not df_descuentos.empty and df_descuentos['Monto'].sum() > 0:
        total_desc = df_descuentos['Monto'].sum()
        df_desc_resumido = pd.DataFrame([{"Descripción": "Total Somos Avellaneda", "Monto": total_desc}])
        dibujar_tabla("SOMOS AVELLANEDA", df_desc_resumido)
     
    pdf.ln(5) 
    estado, color_texto = ("FALTANTE", (200, 0, 0)) if diferencia > 0 else ("SOBRANTE", (0, 100, 0)) 
    if diferencia == 0: estado, color_texto = ("OK", (0, 0, 0)) 
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color_texto) 
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1) 
     
    return pdf.output(dest="S").encode("latin-1") 

# --- 6. INTERFAZ UI --- 
def input_tabla(titulo, key, solo_monto=False): 
    st.markdown(f"**{titulo}**") 
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%.2f", min_value=0.0, step=0.01)} 
    if not solo_monto: cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    df = st.data_editor(st.session_state[key], column_config=cfg, num_rows="dynamic", use_container_width=True, key=f"ed_{key}", hide_index=True) 
    
    return df, (df["Monto"].sum() if not df.empty else 0.0) 

separador_grueso = "<hr style='border: none; height: 4px; background-color: #555555; margin-top: 2rem; margin-bottom: 2rem;'/>"

st.title("Estancia San Francisco") 

# --- BLOQUE 1: FECHA Y CAJERO ---
col_enc1, col_enc2 = st.columns(2) 
with col_enc1: fecha_input = st.date_input("Fecha", datetime.today()) 
with col_enc2: cajero = st.selectbox("Cajero de Turno", lista_cajeros) 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 2: SOMOS AVELLANEDA ---
df_descuentos, total_descuentos = input_tabla("Somos Avellaneda", "df_descuentos", solo_monto=True) 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 3: VALES ---
df_vales, total_vales = input_tabla("Vales", "df_vales") 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 4: TRANSFERENCIAS ---
df_transferencias, total_transf_in = input_tabla("Transferencias", "df_transferencias", solo_monto=True) 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 5: REGISTRADORA, BALANZA Y EFECTIVO ---
registradora_total = st.number_input("Registradora (Z)", 0.0, step=100.0, format="%.2f") 
balanza_total = st.number_input("Balanza", 0.0, step=100.0, format="%.2f") 

with st.expander("Calculadora de Billetes", expanded=False): 
    b20k = st.number_input("$20k", 0); b10k = st.number_input("$10k", 0) 
    b2k = st.number_input("$2k", 0); b1k = st.number_input("$1k", 0) 
    total_fisico = (b20k*20000)+(b10k*10000)+(b2k*2000)+(b1k*1000) 

efectivo_neto = st.number_input("Efectivo", value=float(total_fisico), format="%.2f") 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 6: COBROS DIGITALES Y TOTAL ---
mp = st.number_input("Mercado Pago", 0.0, format="%.2f")
nave = st.number_input("Nave", 0.0, format="%.2f")
clover = st.number_input("Clover", 0.0, format="%.2f")
bbva = st.number_input("BBVA", 0.0, format="%.2f")

total_digital = mp + nave + clover + bbva 
st.info(f"**Total Digital: ${total_digital:,.2f}**")

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 7: ERRORES Y SALIDAS ---
df_errores, total_errores = input_tabla("Errores", "df_errores", solo_monto=True) 
df_salidas, total_salidas = input_tabla("Salida de Caja", "df_salidas") 

st.markdown(separador_grueso, unsafe_allow_html=True) 

# --- BLOQUE 8: MERCADERÍA, PROVEEDORES Y CAJA REAL ---
st.markdown("**Mercaderia de Empleados**") 
cfg_emp = { 
    "Empleado": st.column_config.SelectboxColumn("Empleado", options=lista_empleados, required=True), 
    "Ticket": st.column_config.SelectboxColumn("Tipo", options=["Con Ticket", "Sin Ticket"], required=True),
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%.2f", min_value=0.0, step=0.01) 
} 
df_empleados = st.data_editor(st.session_state.df_empleados, column_config=cfg_emp, num_rows="dynamic", use_container_width=True, key="ed_emp", hide_index=True) 

if not df_empleados.empty and "Ticket" in df_empleados.columns:
    total_empleados = df_empleados[df_empleados["Ticket"] == "Con Ticket"]["Monto"].sum()
else:
    total_empleados = df_empleados["Monto"].sum() if not df_empleados.empty else 0.0

st.markdown("**Pago a Proveedores**") 
cfg_prov = { 
    "Proveedor": st.column_config.SelectboxColumn("Proveedor", options=lista_proveedores, required=True), 
    "Forma Pago": st.column_config.SelectboxColumn("Metodo", options=["Efectivo", "Digital / Banco"], required=True), 
    "Monto": st.column_config.NumberColumn("Monto ($)", format="$%.2f", min_value=0.0, step=0.01) 
} 
df_proveedores = st.data_editor(st.session_state.df_proveedores, column_config=cfg_prov, num_rows="dynamic", use_container_width=True, key="ed_prov", hide_index=True) 
total_prov_efectivo = df_proveedores[df_proveedores["Forma Pago"] == "Efectivo"]["Monto"].sum() 

# --- RESULTADO FINAL (CAJA REAL) --- 
st.markdown("### Caja Real") 

total_justificado = total_digital + efectivo_neto + total_transf_in + total_salidas + total_prov_efectivo + total_vales + total_empleados + total_errores + total_descuentos
diferencia = balanza_total - total_justificado 

c1, c2, c3 = st.columns(3) 
c1.metric("Diferencia", f"${diferencia:,.2f}", delta_color="inverse" if diferencia > 0 else "normal") 

if c2.button("Guardar en Drive", use_container_width=True): 
    if diferencia == 0:
        estado_caja = "OK"
    elif diferencia > 0:
        estado_caja = "FALTANTE"
    else:
        estado_caja = "SOBRANTE"

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
        st.toast("Cierre guardado correctamente")
        st.success("Guardado exitoso") 

if c3.button("Generar PDF", use_container_width=True): 
    # Aquí definimos cómo se verán los nombres en el PDF
    desglose = {"Mercado Pago": mp, "Nave": nave, "Clover": clover, "BBVA": bbva} 
    pdf_bytes = generar_pdf_profesional(fecha_input, cajero, balanza_total, registradora_total,  
                                        total_digital, efectivo_neto, df_salidas, df_transferencias,  
                                        df_errores, df_vales, df_descuentos, df_proveedores,  
                                        df_empleados, diferencia, desglose) 
    st.download_button("Descargar PDF", pdf_bytes, f"Cierre_{fecha_input}.pdf", "application/pdf")
