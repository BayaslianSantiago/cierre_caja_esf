import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """Renderiza un editor de datos de Streamlit vinculado a la sesión."""
    st.markdown(f"**{titulo}**") 
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # Limpiamos el índice antes de mostrar para evitar la columna extra '0', '1', etc.
    df_input = st.session_state[session_key].reset_index(drop=True)

    df = st.data_editor(
        df_input, 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"ed_{session_key}", 
        hide_index=True
    ) 
    
    # Guardamos con el índice reseteado para que no se acumule
    st.session_state[session_key] = df.reset_index(drop=True)
    return st.session_state[session_key], (df["Monto"].sum() if not df.empty else 0.0) 
