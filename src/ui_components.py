import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos de Streamlit.
    Asegura que las columnas se mantengan incluso si la tabla está vacía.
    """
    st.markdown(f"**{titulo}**") 
    
    # Definición de columnas
    cols = ["Monto"] if solo_monto else ["Descripción", "Monto"]
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # IMPORTANTE: Si la sesión está vacía, nos aseguramos de que el DataFrame tenga columnas
    if st.session_state[session_key].empty:
        st.session_state[session_key] = pd.DataFrame(columns=cols)

    # El secreto para que no se borre el dato al dar Enter es pasar el DataFrame
    # pero NO re-asignar la sesión inmediatamente en la misma línea del widget.
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"widget_v4_{session_key}", 
        hide_index=True
    ) 
    
    # Guardamos en sesión
    st.session_state[session_key] = df_editado
    
    total = df_editado["Monto"].fillna(0).sum() if not df_editado.empty else 0.0
    return df_editado, total
