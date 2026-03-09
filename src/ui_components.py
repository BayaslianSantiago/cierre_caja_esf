import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos usando listas nativas de Python.
    ESTO ELIMINA EL ERROR DEL ÍNDICE DEFINITIVAMENTE.
    """
    st.markdown(f"**{titulo}**") 
    
    # Definición estricta de columnas
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True, default=0)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # Aseguramos que la sesión sea una LISTA, no un DataFrame
    if isinstance(st.session_state[session_key], pd.DataFrame):
        st.session_state[session_key] = st.session_state[session_key].to_dict('records')

    # El editor trabaja con la lista directamente
    datos_editados = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"pure_list_editor_{session_key}", 
        hide_index=True
    ) 
    
    # Sincronizamos la lista
    st.session_state[session_key] = datos_editados
    
    # Convertimos a DF solo para calcular el total
    df_temp = pd.DataFrame(datos_editados)
    total = df_temp["Monto"].fillna(0).sum() if not df_temp.empty else 0.0
    
    return df_temp, total
