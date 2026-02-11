from PySide6 import QtCore, QtWidgets, QtGui
from datetime import date, timedelta
from core import repo, theme
import sys

# Factores
FACTORES_CONVERSION = { "Tablas": 30, "Tablones": 20, "Paletas": 10, "Machihembrado": 5 }

# --- MATPLOTLIB ---
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=3.5, height=3.5, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor(theme.BG_SIDEBAR)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

def exportar_tabla_excel(parent, table_widget, filename_base):
    try: import openpyxl
    except ImportError: QtWidgets.QMessageBox.warning(parent, "Error", "Instale openpyxl"); return
    path, _ = QtWidgets.QFileDialog.getSaveFileName(parent, "Exportar", f"{filename_base}.xlsx", "Excel (*.xlsx)")
    if not path: return
    try:
        wb = openpyxl.Workbook(); ws = wb.active
        headers = [table_widget.horizontalHeaderItem(c).text() for c in range(table_widget.columnCount())]
        ws.append(headers)
        for r in range(table_widget.rowCount()):
            row = []
            for c in range(table_widget.columnCount()):
                it = table_widget.item(r, c)
                txt = it.text() if it else ""
                try: row.append(float(txt))
                except: row.append(txt)
            ws.append(row)
        wb.save(path); QtWidgets.QMessageBox.information(parent, "Éxito", f"Guardado: {path}")
    except Exception as e: QtWidgets.QMessageBox.critical(parent, "Error", str(e))

class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        t = QtWidgets.QLabel("CENTRO DE REPORTES")
        t.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR}; margin-bottom: 10px;")
        t.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(t)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme.BORDER_COLOR}; }} 
            QTabBar::tab {{ background: {theme.BG_SIDEBAR}; color: {theme.TEXT_SECONDARY}; padding: 8px 25px; font-weight: bold; margin-right: 2px; }} 
            QTabBar::tab:selected {{ background: {theme.BTN_PRIMARY}; color: white; }}
        """)

        self.tab_prod = QtWidgets.QWidget(); self._setup_prod_tab(self.tab_prod)
        self.tabs.addTab(self.tab_prod, "🏭 Producción")

        self.tab_disp = QtWidgets.QWidget(); self._setup_disp_tab(self.tab_disp)
        self.tabs.addTab(self.tab_disp, "🚚 Despachos")

        self.tab_lote = QtWidgets.QWidget(); self._setup_lote_tab(self.tab_lote)
        self.tabs.addTab(self.tab_lote, "🔢 Por Lotes")

        layout.addWidget(self.tabs)

    def _estilizar_input(self, widget):
        widget.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 5px; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px; min-width: 100px;")

    def _set_date_range(self, d1_widget, d2_widget, mode):
        today = date.today()
        if mode == "week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
        elif mode == "month":
            start = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end = next_month.replace(day=1) - timedelta(days=1)
        elif mode == "all":
            start = date(2000, 1, 1)
            end = date(2030, 12, 31)
        
        d1_widget.setDate(start); d2_widget.setDate(end)

    # ---------------- TAB 1: PRODUCCIÓN ----------------
    def _setup_prod_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        filter_box = QtWidgets.QGroupBox("Filtros de Producción")
        filter_box.setStyleSheet(f"color: white; border: 1px solid {theme.BORDER_COLOR}; margin-top: 10px; padding: 10px;")
        fl = QtWidgets.QVBoxLayout(filter_box)

        # Fila 1
        row1 = QtWidgets.QHBoxLayout()
        self.d1_prod = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_prod.setCalendarPopup(True)
        self.d2_prod = QtWidgets.QDateEdit(date.today()); self.d2_prod.setCalendarPopup(True)
        self._estilizar_input(self.d1_prod); self._estilizar_input(self.d2_prod)
        
        btn_week = QtWidgets.QPushButton("Esta Semana")
        btn_week.clicked.connect(lambda: self._set_date_range(self.d1_prod, self.d2_prod, "week"))
        
        btn_month = QtWidgets.QPushButton("Este Mes")
        btn_month.clicked.connect(lambda: self._set_date_range(self.d1_prod, self.d2_prod, "month"))
        
        btn_all = QtWidgets.QPushButton("Todos")
        btn_all.clicked.connect(lambda: self._set_date_range(self.d1_prod, self.d2_prod, "all"))
        
        for b in [btn_week, btn_month, btn_all]: 
            b.setStyleSheet(f"background-color: #444; color: white; padding: 4px 10px; border-radius: 4px;")
            b.setCursor(QtCore.Qt.PointingHandCursor)

        row1.addWidget(QtWidgets.QLabel("Desde:")); row1.addWidget(self.d1_prod)
        row1.addWidget(QtWidgets.QLabel("Hasta:")); row1.addWidget(self.d2_prod)
        row1.addWidget(btn_week); row1.addWidget(btn_month); row1.addWidget(btn_all)
        row1.addStretch()
        
        # Fila 2
        row2 = QtWidgets.QHBoxLayout()
        self.cb_prod_filter = QtWidgets.QComboBox(); self.cb_prod_filter.addItem("Todos los Productos")
        self.cb_prod_filter.addItems(["Tablas", "Machihembrado", "Tablones", "Paletas"])
        self._estilizar_input(self.cb_prod_filter)

        self.cb_qual_filter = QtWidgets.QComboBox()
        self.cb_qual_filter.addItems(["Todas", "Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self._estilizar_input(self.cb_qual_filter)

        btn_search = QtWidgets.QPushButton("🔍 Buscar"); btn_search.clicked.connect(self._search_prod)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 6px 20px; border-radius: 4px;")
        
        row2.addWidget(QtWidgets.QLabel("Producto:")); row2.addWidget(self.cb_prod_filter)
        row2.addWidget(QtWidgets.QLabel("Calidad:")); row2.addWidget(self.cb_qual_filter)
        row2.addWidget(btn_search); row2.addStretch()

        fl.addLayout(row1); fl.addLayout(row2)
        l.addWidget(filter_box)

        content_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.table_prod = QtWidgets.QTableWidget()
        # --- AÑADIDO SKU ---
        cols = ["Fecha", "Lote", "SKU", "Producto", "Calidad", "Cant.", "Bultos", "Estado"]
        self.table_prod.setColumnCount(len(cols)); self.table_prod.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_prod)
        content_split.addWidget(self.table_prod)

        if MATPLOTLIB_AVAILABLE:
            self.chart_prod = MplCanvas(self, width=3.5, height=3.5, dpi=90)
            content_split.addWidget(self.chart_prod)
        
        l.addWidget(content_split)
        
        btn_xls = QtWidgets.QPushButton("📊 Exportar Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_prod, "produccion"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 8px; font-weight: bold;")
        l.addWidget(btn_xls)

    def _search_prod(self):
        d1 = self.d1_prod.date().toPython(); d2 = self.d2_prod.date().toPython()
        pname = self.cb_prod_filter.currentText()
        if pname == "Todos los Productos": pname = ""
        qual = self.cb_qual_filter.currentText()

        try:
            data = repo.report_production_period(d1, d2, pname, qual)
            self.table_prod.setRowCount(0); stats = {}
            for r in data:
                row = self.table_prod.rowCount(); self.table_prod.insertRow(row)
                tipo = r['producto']; piezas = r['piezas_iniciales']
                factor = FACTORES_CONVERSION.get(tipo, 1)
                
                self.table_prod.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_prod.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_prod.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['sku']))) # SKU
                self.table_prod.setItem(row, 3, QtWidgets.QTableWidgetItem(str(tipo)))
                self.table_prod.setItem(row, 4, QtWidgets.QTableWidgetItem(str(r.get('quality', '-'))))
                self.table_prod.setItem(row, 5, QtWidgets.QTableWidgetItem(f"{piezas:.0f}"))
                self.table_prod.setItem(row, 6, QtWidgets.QTableWidgetItem(f"{piezas/factor:.0f}" if factor else "0"))
                self.table_prod.setItem(row, 7, QtWidgets.QTableWidgetItem(str(r['status'])))
                
                stats[tipo] = stats.get(tipo, 0) + piezas
            if MATPLOTLIB_AVAILABLE: self._update_chart(self.chart_prod, stats, "Producción (Piezas)")
        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ---------------- TAB 2: DESPACHOS ----------------
    def _setup_disp_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        filter_box = QtWidgets.QGroupBox("Filtros de Despacho")
        filter_box.setStyleSheet(f"color: white; border: 1px solid {theme.BORDER_COLOR}; margin-top: 10px; padding: 10px;")
        fl = QtWidgets.QVBoxLayout(filter_box)

        row1 = QtWidgets.QHBoxLayout()
        self.d1_disp = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_disp.setCalendarPopup(True)
        self.d2_disp = QtWidgets.QDateEdit(date.today()); self.d2_disp.setCalendarPopup(True)
        self._estilizar_input(self.d1_disp); self._estilizar_input(self.d2_disp)
        
        btn_week = QtWidgets.QPushButton("Esta Semana"); btn_week.clicked.connect(lambda: self._set_date_range(self.d1_disp, self.d2_disp, "week"))
        btn_month = QtWidgets.QPushButton("Este Mes"); btn_month.clicked.connect(lambda: self._set_date_range(self.d1_disp, self.d2_disp, "month"))
        btn_all = QtWidgets.QPushButton("Todos"); btn_all.clicked.connect(lambda: self._set_date_range(self.d1_disp, self.d2_disp, "all"))

        for b in [btn_week, btn_month, btn_all]: 
            b.setStyleSheet(f"background-color: #444; color: white; padding: 4px 10px; border-radius: 4px;")
            b.setCursor(QtCore.Qt.PointingHandCursor)

        row1.addWidget(QtWidgets.QLabel("Desde:")); row1.addWidget(self.d1_disp)
        row1.addWidget(QtWidgets.QLabel("Hasta:")); row1.addWidget(self.d2_disp)
        row1.addWidget(btn_week); row1.addWidget(btn_month); row1.addWidget(btn_all)
        row1.addStretch()

        row2 = QtWidgets.QHBoxLayout()
        self.cb_client = QtWidgets.QComboBox(); self.cb_client.addItem("Todos los Clientes", None)
        for c in repo.list_clients(): self.cb_client.addItem(c.name, c.id)
        self._estilizar_input(self.cb_client)
        
        self.cb_disp_prod = QtWidgets.QComboBox(); self.cb_disp_prod.addItem("Todos los Productos")
        self.cb_disp_prod.addItems(["Tablas", "Machihembrado", "Tablones", "Paletas"])
        self._estilizar_input(self.cb_disp_prod)

        self.txt_guide = QtWidgets.QLineEdit()
        self.txt_guide.setPlaceholderText("Nro. Guía")
        self._estilizar_input(self.txt_guide)

        btn_search = QtWidgets.QPushButton("🔍 Buscar"); btn_search.clicked.connect(self._search_disp)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 6px 15px; border-radius: 4px;")

        row2.addWidget(QtWidgets.QLabel("Cliente:")); row2.addWidget(self.cb_client)
        row2.addWidget(QtWidgets.QLabel("Prod:")); row2.addWidget(self.cb_disp_prod)
        row2.addWidget(QtWidgets.QLabel("Guía:")); row2.addWidget(self.txt_guide)
        row2.addWidget(btn_search); row2.addStretch()

        fl.addLayout(row1); fl.addLayout(row2)
        l.addWidget(filter_box)

        content_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.table_disp = QtWidgets.QTableWidget()
        # --- AÑADIDO SKU ---
        cols = ["Fecha", "Guía", "Cliente", "Producto", "Lote", "SKU", "Cant.", "Obs"]
        self.table_disp.setColumnCount(len(cols)); self.table_disp.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_disp)
        content_split.addWidget(self.table_disp)

        if MATPLOTLIB_AVAILABLE:
            self.chart_disp = MplCanvas(self, width=3.5, height=3.5, dpi=90)
            content_split.addWidget(self.chart_disp)
        
        l.addWidget(content_split)
        
        btn_xls = QtWidgets.QPushButton("📊 Exportar Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_disp, "despachos"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 8px; font-weight: bold;")
        l.addWidget(btn_xls)

    def _search_disp(self):
        d1 = self.d1_disp.date().toPython(); d2 = self.d2_disp.date().toPython()
        cid = self.cb_client.currentData()
        pname = self.cb_disp_prod.currentText()
        if pname == "Todos los Productos": pname = ""
        guide = self.txt_guide.text().strip()

        try:
            data = repo.report_dispatches_detailed(d1, d2, cid, pname, guide)
            self.table_disp.setRowCount(0); stats = {}
            for r in data:
                row = self.table_disp.rowCount(); self.table_disp.insertRow(row)
                self.table_disp.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_disp.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['guia'])))
                self.table_disp.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['cliente'])))
                self.table_disp.setItem(row, 3, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_disp.setItem(row, 4, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_disp.setItem(row, 5, QtWidgets.QTableWidgetItem(str(r['sku']))) # SKU
                self.table_disp.setItem(row, 6, QtWidgets.QTableWidgetItem(f"{r['cantidad']:.0f}"))
                self.table_disp.setItem(row, 7, QtWidgets.QTableWidgetItem(str(r['obs'])))
                prod = r['producto']; stats[prod] = stats.get(prod, 0) + r['cantidad']
            if MATPLOTLIB_AVAILABLE: self._update_chart(self.chart_disp, stats, "Despachos (Piezas)")
        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ---------------- TAB 3: LOTES ----------------
    def _setup_lote_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        h = QtWidgets.QHBoxLayout()
        h.setSpacing(15)
        
        self.s_l1 = QtWidgets.QSpinBox(); self.s_l1.setRange(0, 999999); self.s_l1.setPrefix("Lote ")
        self.s_l2 = QtWidgets.QSpinBox(); self.s_l2.setRange(0, 999999); self.s_l2.setPrefix("Lote ")
        self._estilizar_input(self.s_l1); self._estilizar_input(self.s_l2)

        self.cb_lote_prod = QtWidgets.QComboBox()
        self.cb_lote_prod.addItem("Todos los Productos")
        self.cb_lote_prod.addItems(["Tablas", "Machihembrado", "Tablones", "Paletas"])
        self._estilizar_input(self.cb_lote_prod)

        self.chk_agotados = QtWidgets.QCheckBox("Incluir Agotados/Bajas")
        self.chk_agotados.setStyleSheet("color: white; font-weight: bold;")

        btn = QtWidgets.QPushButton("🔍 Buscar"); btn.clicked.connect(self._search_lotes)
        btn.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 6px 15px; border-radius: 4px; color: white;")
        
        h.addWidget(QtWidgets.QLabel("Desde:")); h.addWidget(self.s_l1)
        h.addWidget(QtWidgets.QLabel("Hasta:")); h.addWidget(self.s_l2)
        h.addWidget(self.cb_lote_prod)
        h.addWidget(self.chk_agotados)
        h.addWidget(btn); h.addStretch()
        l.addLayout(h)

        self.table_lote = QtWidgets.QTableWidget()
        # --- AÑADIDO SKU ---
        cols = ["Lote", "SKU", "Producto", "F. Prod", "Stock Actual", "Estado"]
        self.table_lote.setColumnCount(len(cols)); self.table_lote.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_lote)
        l.addWidget(self.table_lote)

    def _search_lotes(self):
        l1 = self.s_l1.value(); l2 = self.s_l2.value()
        incluir = self.chk_agotados.isChecked()
        pname = self.cb_lote_prod.currentText()
        if pname == "Todos los Productos": pname = None

        if l1 > l2: QtWidgets.QMessageBox.warning(self, "Error", "Rango inválido."); return
        try:
            data = repo.report_by_lot_range(l1, l2, incluir, pname)
            self.table_lote.setRowCount(0)
            for r in data:
                row = self.table_lote.rowCount(); self.table_lote.insertRow(row)
                self.table_lote.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_lote.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['sku']))) # SKU
                self.table_lote.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_lote.setItem(row, 3, QtWidgets.QTableWidgetItem(str(r['fecha_prod'])))
                self.table_lote.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{r['stock_actual']:.0f}"))
                self.table_lote.setItem(row, 5, QtWidgets.QTableWidgetItem(str(r['estado'])))
        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _style_table(self, t):
        t.setStyleSheet(f"QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY}; gridline-color: {theme.BORDER_COLOR}; }} QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 8px; font-weight: bold; }} QTableWidget::item {{ padding: 5px; }}")
        t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        t.verticalHeader().setVisible(False); t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def _update_chart(self, canvas, data_dict, title):
        canvas.axes.clear()
        if not data_dict: canvas.axes.text(0.5, 0.5, "Sin datos", ha='center', va='center', color='white'); canvas.draw(); return
        labels = list(data_dict.keys()); sizes = list(data_dict.values())
        colors = ['#00f2c3', '#fd5d93', '#ffc107', '#1d8cf8', '#e14eca']
        wedges, texts, autotexts = canvas.axes.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)], textprops=dict(color="white"))
        canvas.axes.set_title(title, color="white", fontsize=10, pad=10)
        for autotext in autotexts: autotext.set_color('black'); autotext.set_weight('bold')
        canvas.draw()