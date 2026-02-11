from PySide6 import QtCore, QtWidgets, QtGui
from datetime import date
from core import repo, theme
import sys

# --- MATPLOTLIB PARA LAS GRÁFICAS ---
try:
    import matplotlib
    matplotlib.use('Qt5Agg') # O QtAgg dependiendo de la versión
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Clase para el Canvas de la Gráfica
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor(theme.BG_SIDEBAR) # Fondo oscuro
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

# --- UTILIDAD EXPORTAR ---
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
        t.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        t.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(t)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(f"QTabWidget::pane {{ border: 1px solid {theme.BORDER_COLOR}; }} QTabBar::tab {{ background: {theme.BG_SIDEBAR}; color: {theme.TEXT_SECONDARY}; padding: 10px 20px; font-weight: bold; }} QTabBar::tab:selected {{ background: {theme.BTN_PRIMARY}; color: white; }}")

        self.tab_prod = QtWidgets.QWidget(); self._setup_prod_tab(self.tab_prod)
        self.tabs.addTab(self.tab_prod, "🏭 Producción")

        self.tab_disp = QtWidgets.QWidget(); self._setup_disp_tab(self.tab_disp)
        self.tabs.addTab(self.tab_disp, "🚚 Despachos")

        self.tab_lote = QtWidgets.QWidget(); self._setup_lote_tab(self.tab_lote)
        self.tabs.addTab(self.tab_lote, "🔢 Por Lotes")

        layout.addWidget(self.tabs)

    # ---------------- TAB 1: PRODUCCIÓN ----------------
    def _setup_prod_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        # Filtros
        filter_box = QtWidgets.QGroupBox("Filtros de Búsqueda")
        filter_box.setStyleSheet(f"color: white; border: 1px solid {theme.BORDER_COLOR};")
        fl = QtWidgets.QHBoxLayout(filter_box)

        self.d1_prod = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_prod.setCalendarPopup(True)
        self.d2_prod = QtWidgets.QDateEdit(date.today()); self.d2_prod.setCalendarPopup(True)
        
        self.txt_prod_filter = QtWidgets.QLineEdit()
        self.txt_prod_filter.setPlaceholderText("Tipo de Producto (Opcional)")
        self.txt_prod_filter.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 5px;")

        btn_search = QtWidgets.QPushButton("🔍 Buscar"); btn_search.clicked.connect(self._search_prod)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 6px;")
        
        fl.addWidget(QtWidgets.QLabel("Desde:")); fl.addWidget(self.d1_prod)
        fl.addWidget(QtWidgets.QLabel("Hasta:")); fl.addWidget(self.d2_prod)
        fl.addWidget(QtWidgets.QLabel("Producto:")); fl.addWidget(self.txt_prod_filter)
        fl.addWidget(btn_search)
        l.addWidget(filter_box)

        # Contenido: Tabla + Gráfica
        content_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Tabla
        self.table_prod = QtWidgets.QTableWidget()
        cols = ["Fecha", "Lote", "Producto", "Inicial (Pzas)", "Stock", "Estado"]
        self.table_prod.setColumnCount(len(cols)); self.table_prod.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_prod)
        content_split.addWidget(self.table_prod)

        # Gráfica
        if MATPLOTLIB_AVAILABLE:
            self.chart_prod = MplCanvas(self, width=4, height=4, dpi=90)
            content_split.addWidget(self.chart_prod)
        else:
            content_split.addWidget(QtWidgets.QLabel("Matplotlib no instalado"))

        # Configurar proporciones (Tabla 60%, Gráfica 40%)
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        l.addWidget(content_split)

        btn_xls = QtWidgets.QPushButton("📊 Exportar Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_prod, "produccion"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 6px;")
        l.addWidget(btn_xls)

    def _search_prod(self):
        d1 = self.d1_prod.date().toPython(); d2 = self.d2_prod.date().toPython()
        pname = self.txt_prod_filter.text().strip()
        try:
            data = repo.report_production_period(d1, d2, pname)
            self.table_prod.setRowCount(0)
            
            # Datos para gráfica
            stats = {}

            for r in data:
                row = self.table_prod.rowCount(); self.table_prod.insertRow(row)
                self.table_prod.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_prod.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_prod.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_prod.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{r['piezas_iniciales']:.0f}"))
                self.table_prod.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{r['cantidad']:.0f}"))
                self.table_prod.setItem(row, 5, QtWidgets.QTableWidgetItem(str(r['status'])))
                
                # Agrupar para gráfica (Por producto, sumando piezas iniciales)
                prod = r['producto']
                qty = r['piezas_iniciales']
                stats[prod] = stats.get(prod, 0) + qty

            if MATPLOTLIB_AVAILABLE:
                self._update_chart(self.chart_prod, stats, "Producción por Producto")

        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ---------------- TAB 2: DESPACHOS ----------------
    def _setup_disp_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        
        filter_box = QtWidgets.QGroupBox("Filtros")
        filter_box.setStyleSheet(f"color: white; border: 1px solid {theme.BORDER_COLOR};")
        fl = QtWidgets.QHBoxLayout(filter_box)

        self.d1_disp = QtWidgets.QDateEdit(date.today().replace(day=1)); self.d1_disp.setCalendarPopup(True)
        self.d2_disp = QtWidgets.QDateEdit(date.today()); self.d2_disp.setCalendarPopup(True)
        
        self.cb_client = QtWidgets.QComboBox(); self.cb_client.addItem("Todos", None)
        for c in repo.list_clients(): self.cb_client.addItem(c.name, c.id)
        
        self.txt_disp_prod = QtWidgets.QLineEdit()
        self.txt_disp_prod.setPlaceholderText("Producto...")
        self.txt_disp_prod.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 5px;")

        btn_search = QtWidgets.QPushButton("🔍 Buscar"); btn_search.clicked.connect(self._search_disp)
        btn_search.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 6px;")

        fl.addWidget(QtWidgets.QLabel("Desde:")); fl.addWidget(self.d1_disp)
        fl.addWidget(QtWidgets.QLabel("Hasta:")); fl.addWidget(self.d2_disp)
        fl.addWidget(QtWidgets.QLabel("Cliente:")); fl.addWidget(self.cb_client)
        fl.addWidget(QtWidgets.QLabel("Prod:")); fl.addWidget(self.txt_disp_prod)
        fl.addWidget(btn_search)
        l.addWidget(filter_box)

        content_split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        self.table_disp = QtWidgets.QTableWidget()
        cols = ["Fecha", "Guía", "Cliente", "Producto", "Lote", "Cant.", "Obs"]
        self.table_disp.setColumnCount(len(cols)); self.table_disp.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_disp)
        content_split.addWidget(self.table_disp)

        if MATPLOTLIB_AVAILABLE:
            self.chart_disp = MplCanvas(self, width=4, height=4, dpi=90)
            content_split.addWidget(self.chart_disp)
        
        content_split.setStretchFactor(0, 3)
        content_split.setStretchFactor(1, 2)
        l.addWidget(content_split)

        btn_xls = QtWidgets.QPushButton("📊 Exportar Excel")
        btn_xls.clicked.connect(lambda: exportar_tabla_excel(self, self.table_disp, "despachos"))
        btn_xls.setStyleSheet("background-color: #217346; color: white; padding: 6px;")
        l.addWidget(btn_xls)

    def _search_disp(self):
        d1 = self.d1_disp.date().toPython(); d2 = self.d2_disp.date().toPython()
        cid = self.cb_client.currentData()
        pname = self.txt_disp_prod.text().strip()
        
        try:
            data = repo.report_dispatches_detailed(d1, d2, cid, pname)
            self.table_disp.setRowCount(0)
            stats = {} # Para gráfica

            for r in data:
                row = self.table_disp.rowCount(); self.table_disp.insertRow(row)
                self.table_disp.setItem(row, 0, QtWidgets.QTableWidgetItem(str(r['fecha'])))
                self.table_disp.setItem(row, 1, QtWidgets.QTableWidgetItem(str(r['guia'])))
                self.table_disp.setItem(row, 2, QtWidgets.QTableWidgetItem(str(r['cliente'])))
                self.table_disp.setItem(row, 3, QtWidgets.QTableWidgetItem(str(r['producto'])))
                self.table_disp.setItem(row, 4, QtWidgets.QTableWidgetItem(str(r['lote'])))
                self.table_disp.setItem(row, 5, QtWidgets.QTableWidgetItem(f"{r['cantidad']:.0f}"))
                self.table_disp.setItem(row, 6, QtWidgets.QTableWidgetItem(str(r['obs'])))
                
                # Agrupar para gráfica (Por Producto Despachado)
                prod = r['producto']
                stats[prod] = stats.get(prod, 0) + r['cantidad']

            if MATPLOTLIB_AVAILABLE:
                self._update_chart(self.chart_disp, stats, "Despachos por Producto")

        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # ---------------- TAB 3: LOTES ----------------
    def _setup_lote_tab(self, parent):
        l = QtWidgets.QVBoxLayout(parent)
        h = QtWidgets.QHBoxLayout()
        self.s_l1 = QtWidgets.QSpinBox(); self.s_l1.setRange(0, 999999); self.s_l1.setPrefix("Lote ")
        self.s_l2 = QtWidgets.QSpinBox(); self.s_l2.setRange(0, 999999); self.s_l2.setPrefix("Lote ")
        btn = QtWidgets.QPushButton("🔍 Buscar"); btn.clicked.connect(self._search_lotes)
        btn.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; padding: 6px;")
        h.addWidget(QtWidgets.QLabel("Desde:")); h.addWidget(self.s_l1)
        h.addWidget(QtWidgets.QLabel("Hasta:")); h.addWidget(self.s_l2); h.addWidget(btn)
        l.addLayout(h)

        self.table_lote = QtWidgets.QTableWidget()
        cols = ["Lote", "Producto", "F. Prod", "Stock", "Estado"]
        self.table_lote.setColumnCount(len(cols)); self.table_lote.setHorizontalHeaderLabels(cols)
        self._style_table(self.table_lote)
        l.addWidget(self.table_lote)

    def _search_lotes(self):
        l1 = self.s_l1.value(); l2 = self.s_l2.value()
        if l1 > l2: QtWidgets.QMessageBox.warning(self, "Error", "Rango inválido."); return
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
        except Exception as e: QtWidgets.QMessageBox.critical(self, "Error", str(e))

    # --- HELPERS ---
    def _style_table(self, t):
        t.setStyleSheet(f"QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY}; gridline-color: {theme.BORDER_COLOR}; }} QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 5px; }}")
        t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)

    def _update_chart(self, canvas, data_dict, title):
        canvas.axes.clear()
        if not data_dict:
            canvas.draw(); return
        
        labels = list(data_dict.keys())
        sizes = list(data_dict.values())
        
        # Colores personalizados oscuros/neón
        colors = ['#00f2c3', '#fd5d93', '#ffc107', '#1d8cf8', '#e14eca']
        
        wedges, texts, autotexts = canvas.axes.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            startangle=90, colors=colors[:len(labels)],
            textprops=dict(color="white")
        )
        
        canvas.axes.set_title(title, color="white", fontsize=12)
        
        # Estilo para el texto dentro de la torta
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_weight('bold')
            
        canvas.draw()