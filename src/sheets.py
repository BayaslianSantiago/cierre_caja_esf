import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from src.utils import logger, safe_execution
from src.config import LISTA_PROVEEDORES_DEFAULT

def get_connection():
    """Establece conexión con Google Sheets."""
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        logger.error(f"Error al conectar con GSheets: {e}")
        st.error("Error de conexión con la base de datos centralizada.")
        return None

@safe_execution
def cargar_proveedores(conn):
    """Carga la lista de proveedores desde la hoja 'Directorio'."""
    if conn is None:
        return LISTA_PROVEEDORES_DEFAULT

    df_directorio = conn.read(worksheet="Directorio", ttl=600)
    if not df_directorio.empty and "Proveedor" in df_directorio.columns:
        lista = df_directorio["Proveedor"].dropna().unique().tolist()
        if "Otro" not in lista: lista.append("Otro")
        return lista
    return LISTA_PROVEEDORES_DEFAULT

@safe_execution
def guardar_cierre(conn, datos_cierre, df_provs, df_empls):
    """Guarda toda la información del cierre en las distintas hojas."""
    if conn is None:
        raise ConnectionError("No hay conexión con Google Sheets")

    # Guardar Historial General
    df_historial = conn.read(worksheet="Historial")
    fila_cierre = pd.DataFrame([datos_cierre])
    df_historial_upd = pd.concat([df_historial, fila_cierre], ignore_index=True).fillna("")
    conn.update(worksheet="Historial", data=df_historial_upd)
    
    # Guardar Pagos a Proveedores (si existen)
    pagos_reales = df_provs[df_provs["Monto"] > 0].copy()
    if not pagos_reales.empty:
        pagos_reales["Fecha"] = datos_cierre["Fecha"]
        pagos_reales["Cajero"] = datos_cierre["Cajero"]
        df_pagos_ant = conn.read(worksheet="Pagos_Proveedores")
        df_pagos_upd = pd.concat([df_pagos_ant, pagos_reales], ignore_index=True).fillna("")
        conn.update(worksheet="Pagos_Proveedores", data=df_pagos_upd)

    # Guardar Consumo de Empleados (si existen)
    consumos_empl = df_empls[df_empls["Monto"] > 0].copy()
    if not consumos_empl.empty:
        consumos_empl["Fecha"] = datos_cierre["Fecha"]
        consumos_empl = consumos_empl[["Fecha", "Empleado", "Monto"]]
        df_empl_ant = conn.read(worksheet="Consumo_Empleados")
        df_empl_upd = pd.concat([df_empl_ant, consumos_empl], ignore_index=True).fillna("")
        conn.update(worksheet="Consumo_Empleados", data=df_empl_upd)
    
    logger.info(f"Cierre guardado exitosamente por {datos_cierre['Cajero']}")
    return True
