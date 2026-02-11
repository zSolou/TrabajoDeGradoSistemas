import os
from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

FACTORES_CONVERSION = {
    "Tablas": 30, "Tablones": 20, "Paletas": 10, "Machihembrado": 5
}

class EditarProductoDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Editar Lote {data.get('nro_lote', '')}")
        self.setModal(True); self.resize(500, 600)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY};")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        scroll = QtWidgets.QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        content = QtWidgets.QWidget(); form = QtWidgets.QFormLayout(content); form.setSpacing(12)
        
        self.inp_lote = QtWidgets.QLineEdit(self.data.get('nro_lote', ''))
        self.inp_lote.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; color: white;")
        
        self.inp_qty = self._spinbox(float(self.data.get('quantity', 0)))
        self.inp_l = self._spinbox(float(self.data.get('largo', 0)))
        self.inp_a = self._spinbox(float(self.data.get('ancho', 0)))
        self.inp_e = self._spinbox(float(self.data.get('espesor', 0)))
        
        self.inp_date = QtWidgets.QDateEdit(calendarPopup=True)
        try:
            d = str(self.data.get('prod_date')).split("T")[0]
            self.inp_date.setDate(QtCore.QDate.fromString(d, "yyyy-MM-dd"))
        except: self.inp_date.setDate(QtCore.QDate.currentDate())
        self.inp_date.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 4px;")

        self.inp_calidad = QtWidgets.QComboBox(); self.inp_calidad.addItems(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self.inp_calidad.setCurrentText(self.data.get('quality', ''))
        self.inp_calidad.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 4px;")

        self.inp_obs = QtWidgets.QPlainTextEdit(str(self.data.get('obs') or "")); self.inp_obs.setFixedHeight(60)
        self.inp_obs.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")

        form.addRow("Nro. Lote:", self.inp_lote); form.addRow("Cantidad (Piezas):", self.inp_qty)
        form.addRow("Largo (m):", self.inp_l); form.addRow("Ancho (cm):", self.inp_a); form.addRow("Espesor (cm):", self.inp_e)
        form.addRow("Fecha Prod:", self.inp_date); form.addRow("Calidad:", self.inp_calidad); form.addRow("Obs:", self.inp_obs)

        scroll.setWidget(content); layout.addWidget(scroll)
        btn_box = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Guardar"); btn_save.clicked.connect(self.accept)
        btn_save.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; padding: 8px;")
        btn_cancel = QtWidgets.QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; padding: 8px;")
        btn_box.addWidget(btn_cancel); btn_box.addWidget(btn_save); layout.addLayout(btn_box)

    def _spinbox(self, val):
        sb = QtWidgets.QDoubleSpinBox(); sb.setRange(0, 999999); sb.setValue(val)
        sb.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 4px;")
        return sb

    def get_data(self):
        return {
            "id": self.data["id"], "nro_lote": self.inp_lote.text(), "quantity": self.inp_qty.value(),
            "largo": self.inp_l.value(), "ancho": self.inp_a.value(), "espesor": self.inp_e.value(),
            "prod_date": self.inp_date.date().toString("yyyy-MM-dd"), "quality": self.inp_calidad.currentText(), "obs": self.inp_obs.toPlainText()
        }

class InventarioScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_existencias = []
        self.data_historial = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        lbl = QtWidgets.QLabel("CONTROL DE INVENTARIO Y SALIDAS")
        lbl.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(lbl)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme.BORDER_COLOR}; }}
            QTabBar::tab {{ background: {theme.BG_SIDEBAR}; color: {theme.TEXT_SECONDARY}; padding: 10px 20px; font-weight: bold; }}
            QTabBar::tab:selected {{ background: {theme.BTN_PRIMARY}; color: white; }}
        """)
        
        self.tab_existencias = QtWidgets.QWidget()
        self._setup_tab_existencias(self.tab_existencias)
        self.tabs.addTab(self.tab_existencias, "📦 Existencias en Patio")
        
        self.tab_historial = QtWidgets.QWidget()
        self._setup_tab_historial(self.tab_historial)
        self.tabs.addTab(self.tab_historial, "🚛 Historial de Despachos")
        
        layout.addWidget(self.tabs)

    def _estilizar_boton(self, btn, color):
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; border-radius: 4px; padding: 6px 15px; font-weight: bold; }} QPushButton:hover {{ filter: brightness(115%); }}")

    def _setup_tab_existencias(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        
        top_bar = QtWidgets.QHBoxLayout()
        self.search_exist = QtWidgets.QLineEdit()
        self.search_exist.setPlaceholderText("🔍 Buscar Lote, SKU...")
        self.search_exist.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 6px; border-radius: 4px;")
        self.search_exist.textChanged.connect(self._filtrar_existencias)
        
        # --- CAMBIO: Checkbox para Mostrar Agotados ---
        self.chk_show_exhausted = QtWidgets.QCheckBox("Mostrar Agotados/Bajas")
        self.chk_show_exhausted.setStyleSheet("color: white; font-weight: bold;")
        self.chk_show_exhausted.stateChanged.connect(self.refresh)
        # ----------------------------------------------
        
        btn_edit = QtWidgets.QPushButton("✎ Editar"); btn_edit.clicked.connect(self._editar_producto)
        btn_del = QtWidgets.QPushButton("📉 Dar de Baja"); btn_del.clicked.connect(self._dar_baja_producto)
        btn_xls = QtWidgets.QPushButton("📊 Excel"); btn_xls.clicked.connect(lambda: self._exportar_excel("existencias"))
        
        self._estilizar_boton(btn_edit, theme.BTN_PRIMARY)
        self._estilizar_boton(btn_del, theme.BTN_DANGER)
        self._estilizar_boton(btn_xls, "#217346")
        
        top_bar.addWidget(self.search_exist)
        top_bar.addWidget(self.chk_show_exhausted) # Agregado al layout
        top_bar.addWidget(btn_edit)
        top_bar.addWidget(btn_del)
        top_bar.addWidget(btn_xls)
        layout.addLayout(top_bar)

        self.table_exist = QtWidgets.QTableWidget()
        cols = ["ID", "SKU", "LOTE", "Producto", "Existencia", "Bultos", "F. Prod", "Estado", "Largo", "Ancho", "Espesor", "Calidad", "Secado", "Cepillado", "Impregnado", "Obs"]
        self.table_exist.setColumnCount(len(cols))
        self.table_exist.setHorizontalHeaderLabels(cols)
        self._estilizar_tabla(self.table_exist)
        layout.addWidget(self.table_exist)

    def _setup_tab_historial(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        top_bar = QtWidgets.QHBoxLayout()
        self.search_hist = QtWidgets.QLineEdit()
        self.search_hist.setPlaceholderText("🔍 Buscar por Cliente, Guía...")
        self.search_hist.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 6px; border-radius: 4px;")
        self.search_hist.textChanged.connect(self._filtrar_historial)
        
        btn_refresh = QtWidgets.QPushButton("🔄 Actualizar"); btn_refresh.clicked.connect(self.refresh)
        btn_xls = QtWidgets.QPushButton("📊 Excel Historial"); btn_xls.clicked.connect(lambda: self._exportar_excel("historial"))
        
        self._estilizar_boton(btn_refresh, theme.BTN_PRIMARY)
        self._estilizar_boton(btn_xls, "#217346")

        top_bar.addWidget(self.search_hist)
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_xls)
        layout.addLayout(top_bar)

        self.table_hist = QtWidgets.QTableWidget()
        cols = ["ID", "Fecha", "Guía", "Cliente", "Producto", "Lote", "SKU", "Cant. Salida", "Bultos Salida", "Obs"]
        self.table_hist.setColumnCount(len(cols))
        self.table_hist.setHorizontalHeaderLabels(cols)
        self._estilizar_tabla(self.table_hist)
        layout.addWidget(self.table_hist)

    def _estilizar_tabla(self, table):
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY}; gridline-color: {theme.BORDER_COLOR}; border: 1px solid {theme.BORDER_COLOR}; }}
            QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 5px; font-weight: bold; border: none; }}
            QTableWidget::item:selected {{ background-color: {theme.ACCENT_COLOR}; color: black; }}
        """)
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def refresh(self):
        try:
            # --- CAMBIO: Pasamos el estado del checkbox al repo ---
            mostrar_todo = self.chk_show_exhausted.isChecked()
            self.data_existencias = repo.list_inventory_rows(mostrar_agotados=mostrar_todo)
            # ----------------------------------------------------
            self._llenar_existencias(self.data_existencias)
            
            self.data_historial = repo.list_dispatches_history()
            self._llenar_historial(self.data_historial)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error cargando datos: {e}")

    def _llenar_existencias(self, data):
        self.table_exist.setRowCount(0)
        for r in data:
            row = self.table_exist.rowCount()
            self.table_exist.insertRow(row)
            
            tipo = str(r.get("product_type", ""))
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor) if factor else 0
            
            # Colorear texto si está agotado
            status = r.get("status")
            if qty == 0: status = "AGOTADO/BAJA"

            vals = [
                str(r.get("id")), r.get("sku"), r.get("nro_lote"), tipo,
                f"{qty:.0f}", f"{bultos}", str(r.get("prod_date")), status,
                str(r.get("largo")), str(r.get("ancho")), str(r.get("espesor")),
                r.get("quality"), r.get("drying"), r.get("planing"), r.get("impregnated"), r.get("obs")
            ]
            for i, v in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(str(v or ""))
                if i==0: it.setData(QtCore.Qt.UserRole, r)
                
                # Visual: gris si está agotado
                if qty == 0: it.setForeground(QtGui.QColor("gray"))
                
                self.table_exist.setItem(row, i, it)

    def _llenar_historial(self, data):
        self.table_hist.setRowCount(0)
        for r in data:
            row = self.table_hist.rowCount()
            self.table_hist.insertRow(row)
            
            tipo = str(r.get("type", ""))
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor) if factor else 0
            
            vals = [
                str(r.get("id")), str(r.get("date")), r.get("guide"),
                r.get("client"), r.get("product"), r.get("lote"), r.get("sku"),
                f"{qty:.0f}", f"{bultos}", r.get("obs")
            ]
            for i, v in enumerate(vals):
                self.table_hist.setItem(row, i, QtWidgets.QTableWidgetItem(str(v or "")))

    def _filtrar_existencias(self, text):
        t = text.lower()
        res = [x for x in self.data_existencias if t in str(x.get("sku")).lower() or t in str(x.get("nro_lote")).lower() or t in str(x.get("product_type")).lower()]
        self._llenar_existencias(res)

    def _filtrar_historial(self, text):
        t = text.lower()
        res = [x for x in self.data_historial if t in str(x.get("client")).lower() or t in str(x.get("guide")).lower() or t in str(x.get("lote")).lower()]
        self._llenar_historial(res)

    def _get_selected_existencia(self):
        row = self.table_exist.currentRow()
        if row < 0: return None
        return self.table_exist.item(row, 0).data(QtCore.Qt.UserRole)

    # --- CAMBIO: Lógica de Dar de Baja ---
    def _dar_baja_producto(self):
        data = self._get_selected_existencia()
        if not data: return
        
        if float(data['quantity']) == 0:
            QtWidgets.QMessageBox.information(self, "Info", "Este producto ya está agotado.")
            return

        if QtWidgets.QMessageBox.question(self, "Dar de Baja", 
            f"¿Desea dar de baja el lote {data['nro_lote']}?\n\n"
            "Esto pondrá la existencia en 0 y lo ocultará de la lista principal.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            
            repo.delete_inventory(data['id'])
            self.refresh()
            QtWidgets.QMessageBox.information(self, "Listo", "Producto dado de baja.")
    # -------------------------------------

    def _editar_producto(self):
        data = self._get_selected_existencia()
        if not data: return
        dlg = EditarProductoDialog(data, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            repo.update_inventory(dlg.get_data())
            self.refresh()

    def _exportar_excel(self, tipo):
        try: import openpyxl
        except: QtWidgets.QMessageBox.warning(self, "Error", "Instale openpyxl"); return
        filename = "inventario.xlsx" if tipo == "existencias" else "historial.xlsx"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar", filename, "Excel (*.xlsx)")
        if not path: return
        try:
            wb = openpyxl.Workbook(); ws = wb.active
            if tipo == "existencias":
                ws.append(["ID", "SKU", "LOTE", "Producto", "Existencia", "Bultos", "F. Prod", "Estado", "Largo", "Ancho", "Espesor", "Calidad", "Secado", "Cepillado", "Impregnado", "Obs"])
                for r in self.data_existencias:
                    f = FACTORES_CONVERSION.get(r.get("product_type"), 1); q = float(r.get("quantity", 0))
                    ws.append([r.get("id"), r.get("sku"), r.get("nro_lote"), r.get("product_type"), q, int(q/f), str(r.get("prod_date")), r.get("status"), float(r.get("largo") or 0), float(r.get("ancho") or 0), float(r.get("espesor") or 0), r.get("quality"), r.get("drying"), r.get("planing"), r.get("impregnated"), r.get("obs")])
            else:
                ws.append(["ID", "Fecha", "Guía", "Cliente", "Producto", "Lote", "SKU", "Cant. Salida", "Bultos Salida", "Obs"])
                for r in self.data_historial:
                    f = FACTORES_CONVERSION.get(r.get("type"), 1); q = float(r.get("quantity", 0))
                    ws.append([r.get("id"), str(r.get("date")), r.get("guide"), r.get("client"), r.get("product"), r.get("lote"), r.get("sku"), q, int(q/f), r.get("obs")])
            wb.save(path); QtWidgets.QMessageBox.information(self, "Éxito", f"Guardado en:\n{path}")
        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))