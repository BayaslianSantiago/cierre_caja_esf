import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """Renderiza un editor de datos de Streamlit vinculado a la sesión."""
    st.markdown(f"**{titulo}**") 
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # Sincronización robusta: 
    # Usamos st.data_editor directamente con el DataFrame de session_state.
    # Streamlit actualizará automáticamente el valor devuelto.
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_widget_{session_key}", # Key fija para el widget
        hide_index=True
    ) 
    
    # Actualizamos la sesión solo si hay cambios para evitar reruns infinitos o pérdida de foco
    st.session_state[session_key] = df_editado.reset_index(drop=True)
    
    return st.session_state[session_key], (df_editado["Monto"].sum() if not df_editado.empty else 0.0) 
