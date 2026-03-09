# Documentación Técnica - Cierre de Caja ESF

## Introducción
Este sistema automatiza el cierre de caja de la fiambrería "Estancia San Francisco". Reemplaza el uso de planillas manuales y centraliza la información en Google Sheets.

## Requisitos de Instalación
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv .env`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar `.streamlit/secrets.toml` con las credenciales de Google Sheets y la contraseña de acceso.

## Flujo de Datos
1. El usuario ingresa con contraseña.
2. Se cargan los datos de proveedores desde Sheets.
3. El usuario completa los campos de ventas (Balanza, Z, Digital, Efectivo).
4. Se calculan las diferencias.
5. Los datos se suben a Sheets y se genera un PDF de respaldo.

## KPIs Calculados
- **Venta Real:** Total Balanza.
- **Efectivo Neto:** Dinero físico rendido.
- **Diferencia:** Balanza - (Efectivo + Digital + Gastos + Pagos + Vales + Errores + Descuentos).
