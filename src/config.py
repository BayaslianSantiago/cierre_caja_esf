# --- CONFIGURACIÓN Y LISTAS MAESTRAS --- 

# Listas por defecto (se usan si falla la conexión a Google Sheets)
LISTA_PROVEEDORES_DEFAULT = ["Pan Rustico", "Pan Fresh", "Dharma", "ValMaira", "Aprea", "CocaCola", "Grenn&Co", "Basile Walter", "Otro"] 
LISTA_CAJEROS = ["Leandro", "Natalia", "Santiago"] 
LISTA_EMPLEADOS = ["Leandro", "Natalia", "Santiago", "Julieta", "Mariela", "Fernanda", "Brian", "Erika", "Oriana"] 

# Configuración de tablas de sesión
SESSION_KEYS = { 
    'df_salidas': ["Descripción", "Monto"], 
    'df_transferencias': ["Monto"], 
    'df_vales': ["Descripción", "Monto"], 
    'df_errores': ["Monto"], 
    'df_descuentos': ["Monto"],  # Cambiado a solo monto para Somos Avellaneda
    'df_proveedores': ["Proveedor", "Forma Pago", "Nro Factura", "Monto"], 
    'df_empleados': ["Empleado", "Ticket", "Monto"], 
    'df_calc_con': ["Monto"], 
    'df_calc_sin': ["Monto"]  
} 
