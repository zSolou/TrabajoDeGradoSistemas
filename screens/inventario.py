import csv
import os
from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

class EditarProductoDialog(QtWidgets.QDialog):
    """Diálogo emergente para editar un lote de inventario."""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Editar Lote {data.get('nro_lote', '')}")
        self.setModal(True)
        self.resize(500, 600)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY};")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        content_widget = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(content_widget)
        form_layout.setSpacing(12)
        
        # Campos
        self.inp_lote = QtWidgets.QLineEdit(self.data.get('nro_lote', ''))
        self.inp_lote.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; color: white;")
        
        self.inp_cantidad = self._add_spinbox(float(self.data.get('quantity', 0)), "Cantidad Total")
        self.inp_largo = self._add_spinbox(float(self.data.get('largo', 0)), "Largo (m)")
        self.inp_ancho = self._add_spinbox(float(self.data.get('ancho', 0)), "Ancho (cm)")
        self.inp_espesor = self._add_spinbox(float(self.data.get('espesor', 0)), "Espesor (cm)")
        self.inp_piezas = self._add_spinbox(int(self.data.get('piezas', 0)), "Piezas", is_int=True)
        self.inp_prod_date = self._add_date(self.data.get('prod_date'))
        
        self.inp_calidad = QtWidgets.QComboBox()
        self.inp_calidad.addItems(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self.inp_calidad.setCurrentText(self.data.get('quality', ''))
        self.inp_calidad.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR};")

        self.inp_obs = QtWidgets.QPlainTextEdit()
        self.inp_obs.setPlainText(str(self.data.get('obs') or ""))
        self.inp_obs.setFixedHeight(80)
        self.inp_obs.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR};")

        form_layout.addRow("Nro. Lote:", self.inp_lote)
        form_layout.addRow("Cantidad:", self.inp_cantidad)
        form_layout.addRow("Largo:", self.inp_largo)
        form_layout.addRow("Ancho:", self.inp_ancho)
        form_layout.addRow("Espesor:", self.inp_espesor)
        form_layout.addRow("Nº Piezas:", self.inp_piezas)
        form_layout.addRow("Calidad:", self.inp_calidad)
        form_layout.addRow("Fecha Prod.:", self.inp_prod_date)
        form_layout.addRow("Observaciones:", self.inp_obs)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Botones
        btn_layout = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Guardar Cambios")
        btn_save.setCursor(QtCore.Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; padding: 10px; border-radius: 5px;")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _add_spinbox(self, val, label, is_int=False):
        sb = QtWidgets.QSpinBox() if is_int else QtWidgets.QDoubleSpinBox()
        sb.setRange(0, 999999)
        if not is_int: sb.setDecimals(2)
        sb.setValue(val)
        sb.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        return sb

    def _add_date(self, date_str):
        de = QtWidgets.QDateEdit(calendarPopup=True)
        if date_str:
            try:
                s = str(date_str)
                if "T" in s: s = s.split("T")[0]
                val = QtCore.QDate.fromString(s, "yyyy-MM-dd")
                de.setDate(val)
            except: pass
        else:
            de.setDate(QtCore.QDate.currentDate())
        de.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        return de

    def get_data(self):
        return {
            "id": self.data["id"],
            "nro_lote": self.inp_lote.text(),
            "quantity": self.inp_cantidad.value(),
            "largo": self.inp_largo.value(),
            "ancho": self.inp_ancho.value(),
            "espesor": self.inp_espesor.value(),
            "piezas": self.inp_piezas.value(),
            "quality": self.inp_calidad.currentText(),
            "prod_date": self.inp_prod_date.date().toString("yyyy-MM-dd"),
            "obs": self.inp_obs.toPlainText()
        }


class InventarioScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QtWidgets.QHBoxLayout()
        lbl_title = QtWidgets.QLabel("INVENTARIO")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        header.addWidget(lbl_title)
        header.addStretch()
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por Lote, SKU o Tipo...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 6px; border-radius: 4px;")
        self.search_input.textChanged.connect(self._filtrar_tabla)
        header.addWidget(self.search_input)
        layout.addLayout(header)

        actions_layout = QtWidgets.QHBoxLayout()
        btn_edit = QtWidgets.QPushButton("✎ Editar")
        btn_edit.clicked.connect(self._editar_producto)
        self._estilizar_boton(btn_edit, theme.BTN_PRIMARY)
        
        btn_del = QtWidgets.QPushButton("🗑 Eliminar")
        btn_del.clicked.connect(self._eliminar_producto)
        self._estilizar_boton(btn_del, theme.BTN_DANGER)
        
        btn_export = QtWidgets.QPushButton("📊 Exportar Excel")
        btn_export.clicked.connect(self._exportar_excel)
        self._estilizar_boton(btn_export, "#217346")
        
        actions_layout.addWidget(btn_edit)
        actions_layout.addWidget(btn_del)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_export)
        layout.addLayout(actions_layout)

        # TABLA ACTUALIZADA: Columna LOTE
        self.table = QtWidgets.QTableWidget()
        columns = [
            "ID", "SKU", "LOTE", "Producto", "Cant.", "Unidad", 
            "Largo", "Ancho", "Espesor", "Piezas", "Calidad", "F. Prod", "Estado", "Obs"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY}; gridline-color: {theme.BORDER_COLOR}; border: 1px solid {theme.BORDER_COLOR}; border-radius: 5px; }}
            QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 8px; border: none; font-weight: bold; }}
            QTableWidget::item {{ padding: 5px; }}
            QTableWidget::item:selected {{ background-color: {theme.ACCENT_COLOR}; color: black; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.lbl_status = QtWidgets.QLabel("Registros: 0")
        self.lbl_status.setStyleSheet("color: gray;")
        layout.addWidget(self.lbl_status)
        self.all_data = []

    def _estilizar_boton(self, btn, color):
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold; }} QPushButton:hover {{ filter: brightness(115%); }}")

    def refresh(self):
        try:
            self.all_data = repo.list_inventory_rows()
            self._llenar_tabla(self.all_data)
        except Exception as e:
            print(f"Error cargando inventario: {e}")

    def _llenar_tabla(self, datos):
        self.table.setRowCount(0)
        for row_data in datos:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            valores = [
                str(row_data.get("id", "")),
                str(row_data.get("sku", "")),
                str(row_data.get("nro_lote", "---")), # LOTE AQUI
                str(row_data.get("product_type", "")),
                f"{row_data.get('quantity', 0):.2f}",
                str(row_data.get("unit", "")),
                str(row_data.get("largo", 0)),
                str(row_data.get("ancho", 0)),
                str(row_data.get("espesor", 0)),
                str(row_data.get("piezas", 0)),
                str(row_data.get("quality", "")),
                str(row_data.get("prod_date", "")),
                str(row_data.get("status", "")),
                str(row_data.get("obs") or "")
            ]
            
            for col_idx, valor in enumerate(valores):
                item = QtWidgets.QTableWidgetItem(valor)
                if col_idx == 0: item.setData(QtCore.Qt.UserRole, row_data)
                if col_idx in [4, 6, 7, 8, 9]: item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                else: item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
        self.lbl_status.setText(f"Registros: {self.table.rowCount()}")

    def _filtrar_tabla(self, texto):
        texto = texto.lower()
        filtrados = [d for d in self.all_data if texto in str(d.get("sku", "")).lower() or texto in str(d.get("nro_lote", "")).lower() or texto in str(d.get("product_type", "")).lower()]
        self._llenar_tabla(filtrados)

    def _get_selected_data(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self.table.item(row, 0).data(QtCore.Qt.UserRole)

    def _eliminar_producto(self):
        data = self._get_selected_data()
        if not data:
            QtWidgets.QMessageBox.warning(self, "Atención", "Seleccione un producto para eliminar.")
            return
        confirm = QtWidgets.QMessageBox.question(self, "Confirmar Eliminación", f"¿Eliminar Lote {data.get('nro_lote')} ({data.get('sku')})?\nEsta acción es irreversible.", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                repo.delete_inventory(data['id'])
                QtWidgets.QMessageBox.information(self, "Éxito", "Producto eliminado.")
                self.refresh()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

    def _editar_producto(self):
        data = self._get_selected_data()
        if not data:
            QtWidgets.QMessageBox.warning(self, "Atención", "Seleccione un producto para editar.")
            return
        dialog = EditarProductoDialog(data, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_data = dialog.get_data()
            try:
                repo.update_inventory(new_data)
                QtWidgets.QMessageBox.information(self, "Éxito", "Producto actualizado.")
                self.refresh()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo actualizar: {e}")

    def _exportar_excel(self):
        if not self.all_data: return
        if not OPENPYXL_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Falta Librería", "Instale openpyxl para exportar a Excel.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exportar Inventario", "inventario.xlsx", "Archivos Excel (*.xlsx)")
        if not path: return
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Inventario"
            headers = ["ID", "SKU", "LOTE", "Producto", "Cantidad", "Unidad", "Largo", "Ancho", "Espesor", "Piezas", "Calidad", "F. Prod", "Estado", "Obs"]
            ws.append(headers)
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            for r in self.all_data:
                ws.append([
                    r.get("id"), r.get("sku"), r.get("nro_lote"), r.get("product_type"),
                    float(r.get("quantity") or 0), r.get("unit"),
                    float(r.get("largo") or 0), float(r.get("ancho") or 0), float(r.get("espesor") or 0),
                    int(r.get("piezas") or 0), r.get("quality"),
                    str(r.get("prod_date") or ""), str(r.get("status") or ""), str(r.get("obs") or "")
                ])
            wb.save(path)
            QtWidgets.QMessageBox.information(self, "Éxito", f"Reporte Excel generado en:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al exportar: {e}")