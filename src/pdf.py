import os
import pandas as pd
from fpdf import FPDF
from src.utils import safe_execution, logger

class SF_PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            try: self.image("logo.png", 15, 10, 30)
            except: pass
        self.set_font("Arial", 'B', 18)
        self.set_xy(50, 12)
        self.cell(0, 10, "ESTANCIA SAN FRANCISCO", ln=1)
        self.set_font("Arial", '', 12)
        self.set_xy(50, 20)
        self.cell(0, 8, "Reporte de Cierre de Caja", ln=1)
        self.ln(10)

@safe_execution
def generar_pdf_profesional(fecha, cajero, balanza, registradora, total_digital, efectivo_neto,  
                            df_salidas, df_transferencias, df_errores, df_vales, df_descuentos,  
                            df_proveedores, df_empleados, diferencia, desglose_digital):
    """Genera el documento PDF del cierre."""
    pdf = SF_PDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
     
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"] 
    fecha_texto = f"{dias_semana[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}" 

    pdf.set_xy(130, 12); pdf.set_font("Arial", 'B', 10); pdf.cell(60, 6, f"FECHA: {fecha_texto}", ln=1, align='R') 
    pdf.set_x(130); pdf.cell(60, 6, f"CAJERO: {cajero}", ln=1, align='R') 
    pdf.ln(15); pdf.line(15, pdf.get_y(), 195, pdf.get_y()); pdf.ln(3) 

    def dibujar_kpi(titulo, monto): 
        pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12) 
        pdf.cell(0, 10, f"{titulo}: $ {monto:,.2f}", ln=1, align='C', fill=True, border=1) 
        pdf.ln(2)  

    dibujar_kpi("1. BALANZA", balanza) 
    dibujar_kpi("2. EFECTIVO", efectivo_neto) 
    dibujar_kpi("3. DIGITAL", total_digital) 
     
    pdf.ln(2); pdf.set_font("Arial", '', 10) 
    pdf.cell(0, 6, f"Ticket Fiscal (Z): $ {registradora:,.2f}", border=0, align='C', ln=1) 
    pdf.ln(5) 

    def dibujar_tabla(titulo, df, label_fijo=None): 
        if df.empty or df['Monto'].sum() == 0: return 
        pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(240, 240, 240) 
        pdf.cell(180, 6, f"  {titulo} (Total: $ {df['Monto'].sum():,.2f})", ln=1, fill=True); pdf.set_font("Arial", '', 9) 
        for _, row in df.iterrows(): 
            if row['Monto'] > 0: 
                if 'Proveedor' in df.columns:
                    txt = f"{row['Proveedor']} ({row['Forma Pago']})"
                else:
                    txt = str(row.get('Descripción', row.get('Empleado', label_fijo))) 
                
                pdf.cell(130, 5, f"      - {txt}"); pdf.cell(40, 5, f"$ {row['Monto']:,.2f}", align='R', ln=1) 
        pdf.ln(2) 

    dibujar_tabla("PAGO A PROVEEDORES", df_proveedores) 
    dibujar_tabla("MERCADERÍA EMPLEADOS", df_empleados) 
    
    if not df_transferencias.empty and df_transferencias['Monto'].sum() > 0:
        total_transf = df_transferencias['Monto'].sum()
        df_transf_res = pd.DataFrame([{"Descripción": "Total transferencias entrantes", "Monto": total_transf}])
        dibujar_tabla("TRANSFERENCIAS (Entrantes)", df_transf_res)

    dibujar_tabla("GASTOS VARIOS / SALIDAS", df_salidas) 
    dibujar_tabla("VALES / FIADOS", df_vales) 

    if not df_errores.empty and df_errores['Monto'].sum() > 0:
        total_err = df_errores['Monto'].sum()
        df_err_res = pd.DataFrame([{"Descripción": "Errores de facturación registrados", "Monto": total_err}])
        dibujar_tabla("ERRORES DE FACTURACIÓN", df_err_res) 

    if not df_descuentos.empty and df_descuentos['Monto'].sum() > 0:
        total_desc = df_descuentos['Monto'].sum()
        df_desc_res = pd.DataFrame([{"Descripción": "Descuentos aplicados en el turno", "Monto": total_desc}])
        dibujar_tabla("DESCUENTOS Y PROMOS", df_desc_res)
     
    pdf.ln(5) 
    estado, color_texto = ("FALTANTE", (200, 0, 0)) if diferencia > 0 else ("SOBRANTE", (0, 100, 0)) 
    if diferencia == 0: estado, color_texto = ("OK", (0, 0, 0)) 
    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(*color_texto) 
    pdf.cell(0, 14, f"CAJA REAL: $ {diferencia:,.2f} ({estado})", ln=1, align='C', border=1) 
     
    return pdf.output(dest="S").encode("latin-1") 
