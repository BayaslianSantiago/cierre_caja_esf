# Agentes del Proyecto - Cierre de Caja

Este archivo documenta los roles y responsabilidades de los agentes (módulos) que componen el sistema de Cierre de Caja de Estancia San Francisco.

## 🤖 Arquitectura de Módulos

### 1. `app.py` (Orquestador)
- **Rol:** Punto de entrada y gestión de la interfaz de usuario (Streamlit).
- **Responsabilidad:** Conectar los componentes visuales con la lógica de negocio y manejar el estado global de la sesión.

### 2. `src/auth.py` (Guardián)
- **Rol:** Seguridad y control de acceso.
- **Responsabilidad:** Validar las credenciales de los cajeros mediante los secrets de la aplicación.

### 3. `src/sheets.py` (Escriba)
- **Rol:** Interfaz con la base de datos (Google Sheets).
- **Responsabilidad:** Realizar lecturas del directorio de proveedores y persistir los cierres diarios, pagos y consumos en la nube de forma segura.

### 4. `src/pdf.py` (Reportero)
- **Rol:** Generador de documentos.
- **Responsabilidad:** Maquetar y generar el archivo PDF profesional para auditoría, incluyendo KPIs y desgloses financieros.

### 5. `src/ui_components.py` (Constructor)
- **Rol:** Componentes de interfaz.
- **Responsabilidad:** Renderizar tablas interactivas y la calculadora de promociones "Somos Avellaneda".

### 6. `src/config.py` (Memoria Estática)
- **Rol:** Almacén de constantes.
- **Responsabilidad:** Definir las listas de empleados, cajeros y estructuras de datos base.

### 7. `src/utils.py` (Auditor de Errores)
- **Rol:** Utilidades y Logging.
- **Responsabilidad:** Centralizar el registro de errores y asegurar que fallos en módulos críticos no rompan la experiencia del usuario.
