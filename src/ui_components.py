import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos de Streamlit usando listas de diccionarios
    para evitar errores de índice y pérdida de datos.
    """
    st.markdown(f"**{titulo}**") 
    
    # Configuración de columnas
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # CONVERSIÓN A LISTA: 
    # Al pasar una lista de diccionarios, Streamlit no genera columnas de índice '0', '1', etc.
    datos_actuales = st.session_state[session_key].to_dict('records')

    df_editado = st.data_editor(
        datos_actuales, 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_v3_{session_key}", 
        hide_index=True
    ) 
    
    # Convertimos de nuevo a DataFrame para el sistema
    df_final = pd.DataFrame(df_editado)
    if df_final.empty:
        # Aseguramos que mantenga las columnas si está vacío
        cols = ["Monto"] if solo_monto else ["Descripción", "Monto"]
        df_final = pd.DataFrame(columns=cols)
        
    st.session_state[session_key] = df_final
    
    total = df_final["Monto"].fillna(0).sum()
    return df_final, total
