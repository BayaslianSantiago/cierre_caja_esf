import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos de Streamlit.
    Utiliza el key del widget para persistir los datos automáticamente en session_state.
    """
    st.markdown(f"**{titulo}**") 
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # IMPORTANTE: No re-asignamos st.session_state[session_key] aquí.
    # Simplemente dejamos que st.data_editor use el key para leer/escribir.
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"widget_{session_key}", 
        hide_index=True
    ) 
    
    # Solo actualizamos el valor de referencia de la sesión para los cálculos de la UI
    st.session_state[session_key] = df_editado
    
    total = df_editado["Monto"].sum() if not df_editado.empty else 0.0
    return df_editado, total
