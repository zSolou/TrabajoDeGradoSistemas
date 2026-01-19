# screens/reportes.py
from PySide6 import QtCore, QtWidgets
from datetime import date, timedelta
import sys

# Intentar cargar matplotlib para la gráfica (pie chart)
try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None

import core.repo as repo


class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []      # filas originales de inventario
        self.filtered_rows = []   # filas tras filtros
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main = QtWidgets.QVBoxLayout(self)

        # Título
        title = QtWidgets.QLabel("Reportes de Inventario")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: 600;")
        main.addWidget(title)

        # Filtros
        filt = QtWidgets.QWidget()
        filt_layout = QtWidgets.QHBoxLayout(filt)
        filt_layout.setContentsMargins(0, 0, 0, 0)
        filt_layout.setSpacing(8)

        # Búsqueda
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Buscar por SKU o tipo...")
        filt_layout.addWidget(self.search_input)

        # Filtro de categoría (Tipo de producto)
        self.category_cb = QtWidgets.QComboBox()
        self.category_cb.addItems(["Todos","Tablas","Machihembrado","Tablones","Paletas"])
        filt_layout.addWidget(self.category_cb)

        # Filtro de fecha
        self.date_cb = QtWidgets.QComboBox()
        self.date_cb.addItems(["Todos","Semana","Mes","Personalizado"])
        filt_layout.addWidget(self.date_cb)

        # Rangos personalizados (visibles solo si "Personalizado")
        self.start_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.start_date.setDate(QtCore.QDate.currentDate().addDays(-7))
        self.start_date.setVisible(False)
        filt_layout.addWidget(self.start_date)

        self.end_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.end_date.setDate(QtCore.QDate.currentDate())
        self.end_date.setVisible(False)
        filt_layout.addWidget(self.end_date)

        # Botón Aplicar (opcional, para forzar filtrado)
        self.apply_btn = QtWidgets.QPushButton("Aplicar")
        filt_layout.addWidget(self.apply_btn)

        main.addWidget(filt)

        # Conectores de filtros
        self.apply_btn.clicked.connect(self._apply_filters)
        self.search_input.textChanged.connect(self._apply_filters)
        self.category_cb.currentTextChanged.connect(self._apply_filters)
        self.date_cb.currentTextChanged.connect(self._on_date_changed)

        # Área de gráfica
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(5, 4))
            self.canvas = FigureCanvas(self.figure)
            main.addWidget(self.canvas, 1)
        else:
            self.chart_label = QtWidgets.QLabel("Gráfico no disponible: matplotlib no instalado.")
            self.chart_label.setAlignment(QtCore.Qt.AlignCenter)
            main.addWidget(self.chart_label)

        # Tabla de detalle (opcional, ayuda a depurar)
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["SKU","Tipo","Cantidad","Prod_Date"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        main.addWidget(self.table)

    def _on_date_changed(self, text):
        if text == "Personalizado":
            self.start_date.setVisible(True)
            self.end_date.setVisible(True)
        else:
            self.start_date.setVisible(False)
            self.end_date.setVisible(False)
        self._apply_filters()

    def _load_data(self):
        try:
            self.all_rows = repo.list_inventory_rows()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error BD", f"No se pudieron cargar las filas de inventario: {e}")
            self.all_rows = []
        self._apply_filters()

    def _apply_filters(self):
        search = (self.search_input.text() or "").strip().lower()
        category = self.category_cb.currentText()
        date_filter = self.date_cb.currentText()

        # Rangos de fecha
        start = None
        end = None
        if date_filter == "Semana":
            end = date.today()
            start = end - timedelta(days=7)
        elif date_filter == "Mes":
            end = date.today()
            start = end - timedelta(days=30)
        elif date_filter == "Personalizado":
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()

        filtered = []
        for r in self.all_rows:
            # Filtro por tipo
            if category != "Todos" and r.get("product_type") != category:
                continue

            # Filtro por búsqueda
            sku = r.get("sku","")
            tipo = r.get("product_type","")
            combined = f"{sku} {tipo}".lower()
            if search and search not in combined:
                continue

            # Filtro por fecha
            prod_date_str = r.get("prod_date","")
            if prod_date_str:
                try:
                    prod_date = date.fromisoformat(prod_date_str)
                except Exception:
                    prod_date = None
            else:
                prod_date = None

            if start and end:
                if prod_date is None or not (start <= prod_date <= end):
                    continue
            elif date_filter in ("Semana","Mes"):
                if prod_date is None or not (start <= prod_date <= end):
                    continue

            filtered.append(r)

        # Actualizar tabla de detalle
        self.table.setRowCount(0)
        for row in filtered:
            self._add_table_row([
                row.get("sku",""),
                row.get("product_type",""),
                float(row.get("quantity") or 0),
                row.get("prod_date","")
            ])

        # Preparar datos para la gráfica
        totals = {"Tablas":0.0, "Machihembrado":0.0, "Tablones":0.0, "Paletas":0.0}
        for row in filtered:
            t = row.get("product_type","")
            if t in totals:
                try:
                    totals[t] += float(row.get("quantity") or 0)
                except Exception:
                    pass

        self._draw_chart(totals)

    def _add_table_row(self, values):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for i, v in enumerate(values):
            item = QtWidgets.QTableWidgetItem("" if v is None else str(v))
            self.table.setItem(r, i, item)

    def _draw_chart(self, data_by_type):
        if not MATPLOTLIB_AVAILABLE:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = [k for k in data_by_type.keys() if data_by_type[k] is not None]
        values = [data_by_type[k] for k in data_by_type.keys() if data_by_type[k] is not None]

        if not values or sum(values) == 0:
            ax.text(0.5, 0.5, "Sin datos para mostrar", transform=ax.transAxes,
                    horizontalalignment="center", verticalalignment="center")
        else:
            colors = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2']
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.axis('equal')
        if MATPLOTLIB_AVAILABLE and hasattr(self, "canvas"):
            self.canvas.draw()