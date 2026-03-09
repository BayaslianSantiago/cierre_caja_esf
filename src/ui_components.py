import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos de Streamlit.
    Pasa el DataFrame directamente para evitar errores de índice.
    """
    st.markdown(f"**{titulo}**") 
    
    # Configuración de columnas
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True, default=0)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # IMPORTANTE: Pasamos st.session_state[session_key] DIRECTAMENTE.
    # No usamos .to_dict() ni .copy() para que Streamlit mantenga la identidad del objeto.
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_final_v5_{session_key}", 
        hide_index=True
    ) 
    
    # Sincronizamos
    st.session_state[session_key] = df_editado
    
    total = df_editado["Monto"].fillna(0).sum() if not df_editado.empty else 0.0
    return df_editado, total
