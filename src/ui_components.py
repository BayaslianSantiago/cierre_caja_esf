import streamlit as st
import pandas as pd

def render_input_tabla(titulo, session_key, solo_monto=False):
    """
    Renderiza un editor de datos estable.
    Usa column_order para forzar que NO se vea el índice.
    """
    st.markdown(f"**{titulo}**") 
    
    # Definición de columnas
    columnas = ["Monto"] if solo_monto else ["Descripción", "Monto"]
    cfg = {"Monto": st.column_config.NumberColumn("($)", format="$%d", min_value=0, required=True, default=0)} 
    if not solo_monto: 
        cfg["Descripción"] = st.column_config.TextColumn("Detalle", required=True) 

    # Aseguramos que sea un DataFrame con las columnas correctas
    if not isinstance(st.session_state[session_key], pd.DataFrame):
        st.session_state[session_key] = pd.DataFrame(columns=columnas)

    # TRUCO: column_order fuerza a Streamlit a mostrar SOLO estas columnas,
    # eliminando visualmente el índice de Pandas (la columna '0', '1', etc.)
    df_editado = st.data_editor(
        st.session_state[session_key], 
        column_config=cfg, 
        column_order=columnas, # <--- ESTO ELIMINA EL ÍNDICE
        num_rows="dynamic", 
        use_container_width=True, 
        key=f"st_editor_{session_key}", 
        hide_index=True
    ) 
    
    # Sincronizamos
    st.session_state[session_key] = df_editado
    
    total = df_editado["Monto"].fillna(0).sum() if not df_editado.empty else 0.0
    return df_editado, total
