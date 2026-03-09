import streamlit as st

def check_password(): 
    """SISTEMA DE LOGIN CENTRALIZADO"""
    
    # Validación de seguridad: Verificar si el secreto existe
    if "general" not in st.secrets or "password" not in st.secrets["general"]:
        st.error("Error de configuración: Falta la contraseña en los Secrets de Streamlit.")
        st.stop()

    def password_entered(): 
        if st.session_state["password"] == st.secrets["general"]["password"]: 
            st.session_state["password_correct"] = True 
            del st.session_state["password"] 
        else: 
            st.session_state["password_correct"] = False 

    if st.session_state.get("password_correct", False): 
        return True 

    st.title("Acceso Restringido") 
    st.text_input("Ingresá la contraseña del local:", type="password", on_change=password_entered, key="password") 
    if "password_correct" in st.session_state and not st.session_state["password_correct"]: 
        st.error("Contraseña incorrecta") 
    return False 
