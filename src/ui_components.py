import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos de Streamlit con persistencia ultra-robusta.
    """
    st.markdown(f"**{titulo}**") 
    
    # Configuración de columnas
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # PATRÓN DE PERSISTENCIA:
    # Usamos el key del widget como la fuente de verdad. 
    # Streamlit maneja internamente la adición de filas sin perder el foco.
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"editor_{session_key}", # Key fija y única
        hide_index=True
    ) 
    
    # Sincronizamos de vuelta a la sesión para que otros módulos (PDF, Sheets) vean los datos
    # Pero lo hacemos de forma que no resetee el widget en el próximo renderizado
    st.session_state[session_key] = df_editado
    
    # Limpieza de Nones para el cálculo del total
    if not df_editado.empty:
        total = df_editado["Monto"].fillna(0).sum()
    else:
        total = 0.0
        
    return df_editado, total
