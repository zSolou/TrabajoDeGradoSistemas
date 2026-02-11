from PySide6 import QtCore, QtWidgets, QtGui
from datetime import date
from core import repo, theme
import os

# --- UTILIDAD PARA EXPORTAR ---
def exportar_tabla_excel(parent, table_widget, filename_base):
    try:
        import openpyxl
    except ImportError:
        QtWidgets.QMessageBox.warning(parent, "Error", "Librería 'openpyxl' requerida para Excel.")
        return

    path, _ = QtWidgets.QFileDialog.getSaveFileName(parent, "Exportar Reporte", f"{filename_base}.xlsx", "Excel (*.xlsx)")
    if not path: return

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # Headers
        headers = []
        for col in range(table_widget.columnCount()):
            headers.append(table_widget.horizontalHeaderItem(col).text())
        ws.append(headers)
        
        # Rows
        for row in range(table_widget.rowCount()):
            row_data = []
            for col in range(table_widget.columnCount()):
                item = table_widget.item(row, col)
                text = item.text() if item else ""
                # Intentar guardar números como números
                try: row_data.append(float(text))
                except: row_data.append(text)
            ws.append(row_data)
            
        wb.save(path)
        QtWidgets.QMessageBox.information(parent, "Éxito", f"Reporte guardado en:\n{path}")
    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "Error", str(e))


class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        title = QtWidgets.QLabel("CENTRO DE REPORTES")
        title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # --- TABS ---
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme.BORDER_COLOR}; }}
            QTabBar::tab {{ background: {theme.BG_SIDEBAR}; color: {theme.TEXT_SECONDARY}; padding: 10px 20px; font-weight: bold; }}
            QTabBar::tab:selected {{ background: {theme.BTN_PRIMARY}; color: white; }}
        """)

        # Tab 1: Producción
        self.tab_prod = QtWidgets.QWidget()
        self._setup_prod_tab(self.tab_prod)
        self.tabs.addTab(self.tab_prod, "🏭 Producción (Entradas)")

        # Tab 2: Despachos
        self.tab_disp = QtWidgets.QWidget()
        self._setup_disp_tab(self.tab_disp)
        self.tabs.addTab(self.tab_disp, "🚚 Despachos (Salidas)")

        # Tab 3: Rango de Lotes
        self.tab_lote = QtWidgets.QWidget()
        self._setup_lote_tab(self.tab_lote)
        self.tabs.addTab(self.tab_lote, "🔢 Búsqueda por Lotes")

        layout.addWidget(self.tabs)

    # ---------------- TAB 1: PRODUCCIÓN ----------------
    def _setup_prod_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        # Filtros
        h = QtWidgets.QHBoxLayout()
        self.d1_prod = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_prod.setCalendarPopup(True)
        self.d2_prod = QtWidgets.QDateEdit(date.today()); self.d2_prod.setCalendarPopup(True)
        
        btn_search = QtWidgets.QPushButton("🔍 Buscar Producción")
        btn_search.clicked.connect(self._search_prod)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; font-weight: bold; padding: 6px;")
        
        btn_xls = QtWidgets.QPushButton("📊 Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_prod, "reporte_produccion"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 6px;")

        h.addWidget(QtWidgets.QLabel("Desde:")); h.addWidget(self.d1_prod)
        h.addWidget(QtWidgets.QLabel("Hasta:")); h.addWidget(self.d2_prod)
        h.addWidget(btn_search)
        h.addWidget(btn_xls)
        l.addLayout(h)

        # Tabla
        self.table_prod = QtWidgets.QTableWidget()
        cols = ["Fecha", "Lote", "Producto", "Prod. Inicial (Pzas)", "Stock Actual", "Estado"]
        self.table_prod.setColumnCount(len(cols)); self.table_prod.setHorizontalHeaderLabels(cols)
        self.table_prod.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._style_table(self.table_prod)
        l.addWidget(self.table_prod)

    def _search_prod(self):
        d1 = self.d1_prod.date().toPython()
        d2 = self.d2_prod.date().toPython()
        try:
            data = repo.report_production_period(d1, d2)
            self.table_prod.setRowCount(0)
            for r in data:
                row = self.table_prod.rowCount(); self.table_prod.insertRow(row)
                self.table_prod.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_prod.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_prod.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_prod.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{r['piezas_iniciales']:.0f}"))
                self.table_prod.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{r['cantidad']:.0f}"))
                self.table_prod.setItem(row, 5, QtWidgets.QTableWidgetItem(str(r['status'])))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


    # ---------------- TAB 2: DESPACHOS ----------------
    def _setup_disp_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        # Filtros
        h = QtWidgets.QHBoxLayout()
        self.d1_disp = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_disp.setCalendarPopup(True)
        self.d2_disp = QtWidgets.QDateEdit(date.today()); self.d2_disp.setCalendarPopup(True)
        
        self.cb_client = QtWidgets.QComboBox()
        self.cb_client.addItem("Todos los Clientes", None)
        for c in repo.list_clients(): self.cb_client.addItem(c.name, c.id)

        btn_search = QtWidgets.QPushButton("🔍 Buscar Salidas")
        btn_search.clicked.connect(self._search_disp)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; font-weight: bold; padding: 6px;")
        
        btn_xls = QtWidgets.QPushButton("📊 Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_disp, "reporte_despachos"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 6px;")

        h.addWidget(QtWidgets.QLabel("Desde:")); h.addWidget(self.d1_disp)
        h.addWidget(QtWidgets.QLabel("Hasta:")); h.addWidget(self.d2_disp)
        h.addWidget(self.cb_client)
        h.addWidget(btn_search)
        h.addWidget(btn_xls)
        l.addLayout(h)

        # Tabla
        self.table_disp = QtWidgets.QTableWidget()
        cols = ["Fecha", "Guía", "Cliente", "Producto", "Lote Origen", "Cant. Despachada", "Observación"]
        self.table_disp.setColumnCount(len(cols)); self.table_disp.setHorizontalHeaderLabels(cols)
        self.table_disp.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._style_table(self.table_disp)
        l.addWidget(self.table_disp)

    def _search_disp(self):
        d1 = self.d1_disp.date().toPython()
        d2 = self.d2_disp.date().toPython()
        cid = self.cb_client.currentData()
        
        try:
            data = repo.report_dispatches_detailed(d1, d2, cid)
            self.table_disp.setRowCount(0)
            for r in data:
                row = self.table_disp.rowCount(); self.table_disp.insertRow(row)
                self.table_disp.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_disp.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['guia'])))
                self.table_disp.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['cliente'])))
                self.table_disp.setItem(row, 3, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_disp.setItem(row, 4, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_disp.setItem(row, 5, QtWidgets.QTableWidgetItem(f"{r['cantidad']:.0f}"))
                self.table_disp.setItem(row, 6, QtWidgets.QTableWidgetItem(str(r['obs'])))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))


    # ---------------- TAB 3: LOTES ----------------
    def _setup_lote_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        h = QtWidgets.QHBoxLayout()
        self.spin_l1 = QtWidgets.QSpinBox(); self.spin_l1.setRange(0, 999999); self.spin_l1.setPrefix("Lote ")
        self.spin_l2 = QtWidgets.QSpinBox(); self.spin_l2.setRange(0, 999999); self.spin_l2.setPrefix("Lote ")
        
        btn_search = QtWidgets.QPushButton("🔍 Buscar Rango")
        btn_search.clicked.connect(self._search_lotes)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; font-weight: bold; padding: 6px;")

        h.addWidget(QtWidgets.QLabel("Desde:")); h.addWidget(self.spin_l1)
        h.addWidget(QtWidgets.QLabel("Hasta:")); h.addWidget(self.spin_l2)
        h.addWidget(btn_search)
        l.addLayout(h)

        self.table_lote = QtWidgets.QTableWidget()
        cols = ["Lote", "Producto", "F. Producción", "Stock Actual", "Estado"]
        self.table_lote.setColumnCount(len(cols)); self.table_lote.setHorizontalHeaderLabels(cols)
        self.table_lote.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._style_table(self.table_lote)
        l.addWidget(self.table_lote)

    def _search_lotes(self):
        l1 = self.spin_l1.value()
        l2 = self.spin_l2.value()
        
        if l1 > l2:
            QtWidgets.QMessageBox.warning(self, "Error", "El lote 'Desde' debe ser menor que 'Hasta'.")
            return

        try:
            data = repo.report_by_lot_range(l1, l2)
            self.table_lote.setRowCount(0)
            for r in data:
                row = self.table_lote.rowCount(); self.table_lote.insertRow(row)
                self.table_lote.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_lote.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_lote.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['fecha_prod'])))
                self.table_lote.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{r['stock_actual']:.0f}"))
                self.table_lote.setItem(row, 4, QtWidgets.QTableWidgetItem(str(r['estado'])))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _style_table(self, table):
        table.setStyleSheet(f"""
            QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY}; gridline-color: {theme.BORDER_COLOR}; border: 1px solid {theme.BORDER_COLOR}; }}
            QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 5px; font-weight: bold; border: none; }}
            QTableWidget::item {{ padding: 5px; }}
        """)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)