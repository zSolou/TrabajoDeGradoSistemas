# core/utils.py
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PySide6 import QtWidgets
import os
from datetime import datetime

def exportar_tabla_pdf(parent, table_widget, title, filename_base):
    path, _ = QtWidgets.QFileDialog.getSaveFileName(parent, "Exportar PDF", f"{filename_base}.pdf", "PDF (*.pdf)")
    if not path: return

    try:
        doc = SimpleDocTemplate(path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        # 1. Logo (si existe)
        if os.path.exists("logo.png"):
            img = Image("logo.png", width=50, height=50)
            img.hAlign = 'LEFT'
            elements.append(img)
            elements.append(Spacer(1, 12))

        # 2. Título y Fecha
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # 3. Datos de la Tabla
        data = []
        
        # Headers
        headers = []
        for c in range(table_widget.columnCount()):
            headers.append(table_widget.horizontalHeaderItem(c).text())
        data.append(headers)

        # Rows
        for r in range(table_widget.rowCount()):
            row_data = []
            for c in range(table_widget.columnCount()):
                item = table_widget.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        # 4. Crear Tabla PDF
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), # Encabezado Azul Oscuro
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8), # Fuente pequeña para que quepa
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        QtWidgets.QMessageBox.information(parent, "Éxito", f"PDF guardado en:\n{path}")

    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "Error PDF", f"Error generando PDF: {str(e)}")