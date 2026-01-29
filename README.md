# Sistema de Cierre de Caja - Estancia San Francisco Avellaneda

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30-red?style=for-the-badge&logo=streamlit)
![Status](https://img.shields.io/badge/Estado-En_Producción-green?style=for-the-badge)

Aplicación web desarrollada en **Python** y **Streamlit** para automatizar, calcular y auditar el proceso de cierre de caja diario en un local gastronómico (fiambrería).

El sistema reemplaza las planillas manuales, reduce errores humanos en el conteo de efectivo y genera reportes ejecutivos en PDF con indicadores de negocio (KPIs).

## 🚀 Funcionalidades Principales

* **Interfaz Minimalista y Responsiva:** Diseño limpio ("Clean UI") optimizado para pantallas anchas, eliminando distracciones visuales para agilizar la carga de datos.
* **Arqueo de Caja Inteligente:** Calculadora integrada de billetes y monedas que determina automáticamente el efectivo neto y el retiro diario.
* **Gestión de Descuentos Dinámica:** Detección automática de días de promoción ("Somos Avellaneda") basada en la fecha, habilitando tablas de carga específicas solo los Lunes y Miércoles.
* **Cálculo de Diferencias en Tiempo Real:** Comparación instantánea entre la facturación esperada (Balanza) y el dinero rendido, alertando sobre sobrantes o faltantes.
* **Reporte PDF Ejecutivo (Business Intelligence):**
    * Generación de comprobantes listos para imprimir.
    * **KPIs:** Análisis de Mix de Ventas (% Efectivo vs % Digital).
    * **Matriz de Descuentos:** Formato de grilla compacta para visualizar grandes volúmenes de tickets de descuento.
    * Diseño contable profesional con trazabilidad de cajero y fecha.

## 🛠️ Tecnologías Utilizadas

* **Python:** Lógica del backend y cálculos financieros.
* **Streamlit:** Framework para la interfaz de usuario (Frontend).
* **Pandas:** Manipulación de estructuras de datos para las tablas de gastos y ajustes.
* **FPDF:** Librería para la maquetación y generación pixel-perfect del reporte PDF.

## 🧠 Estructura del Proyecto

```text
├── app.py              # Código principal de la aplicación
├── requirements.txt    # Dependencias del proyecto
├── logo.png            # (Opcional) Logo para el reporte PDF
└── README.md           # Documentación
