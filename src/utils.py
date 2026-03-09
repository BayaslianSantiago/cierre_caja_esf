import logging
import streamlit as st

def setup_logger():
    """Configura el logger para la aplicación."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("cierre_caja")

logger = setup_logger()

def safe_execution(func):
    """Decorador para manejar errores y logging en funciones críticas."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True)
            st.error(f"Ocurrió un error inesperado en {func.__name__}. Por favor, contacte a soporte.")
            return None
    return wrapper
