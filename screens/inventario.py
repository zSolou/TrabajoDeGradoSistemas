import os
from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

FACTORES_CONVERSION = {
    "Tablas": 30, "Tablones": 20, "Paletas": 10, "Machihembrado": 5
}

# (Omitiendo EditarProductoDialog que estaba bien, copia solo la clase InventarioScreen)

class InventarioScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_existencias = []
        self.data_historial = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Título
        lbl = QtWidgets.QLabel("CONTROL DE INVENTARIO Y SALIDAS")
        lbl.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        layout.addWidget(lbl)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tab_existencias = QtWidgets.QWidget()
        self.tab_historial = QtWidgets.QWidget()
        
        self.tabs.addTab(self.tab_existencias, "📦 Existencias en Patio")
        self.tabs.addTab(self.tab_historial, "🚛 Historial de Despachos")
        layout.addWidget(self.tabs)

        self._setup_existencias()
        self._setup_historial()

    def _setup_existencias(self):
        l = QtWidgets.QVBoxLayout(self.tab_existencias)
        
        # Barra
        h = QtWidgets.QHBoxLayout()
        self.search_exist = QtWidgets.QLineEdit()
        self.search_exist.setPlaceholderText("Buscar...")
        self.search_exist.textChanged.connect(self._filtrar_existencias)
        h.addWidget(self.search_exist)
        
        btn_ref = QtWidgets.QPushButton("🔄 Actualizar")
        btn_ref.clicked.connect(self.refresh)
        h.addWidget(btn_ref)
        l.addLayout(h)

        # Tabla
        self.table_exist = QtWidgets.QTableWidget()
        cols = ["ID", "SKU", "LOTE", "Producto", "Existencia", "Bultos", "F. Prod", "Estado"]
        self.table_exist.setColumnCount(len(cols))
        self.table_exist.setHorizontalHeaderLabels(cols)
        self.table_exist.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        l.addWidget(self.table_exist)

    def _setup_historial(self):
        l = QtWidgets.QVBoxLayout(self.tab_historial)
        self.table_hist = QtWidgets.QTableWidget()
        cols = ["Fecha", "Guía", "Cliente", "Producto", "Lote", "Salida (Pzas)", "Salida (Bultos)"]
        self.table_hist.setColumnCount(len(cols))
        self.table_hist.setHorizontalHeaderLabels(cols)
        self.table_hist.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        l.addWidget(self.table_hist)

    def refresh(self):
        try:
            # Cargar Datos
            self.data_existencias = repo.list_inventory_rows()
            self.data_historial = repo.list_dispatches_history()
            
            # Llenar Tablas
            self._llenar_existencias(self.data_existencias)
            self._llenar_historial(self.data_historial)
            
        except Exception as e:
            # ESTO TE MOSTRARÁ EL ERROR SI LA DB FALLA
            QtWidgets.QMessageBox.critical(self, "Error de Base de Datos", 
                f"No se pudo cargar el inventario.\n\nDetalle: {str(e)}")

    def _llenar_existencias(self, data):
        self.table_exist.setRowCount(0)
        for r in data:
            row = self.table_exist.rowCount()
            self.table_exist.insertRow(row)
            
            tipo = str(r.get("product_type", ""))
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor) if factor else 0
            
            vals = [
                str(r.get("id")), r.get("sku"), r.get("nro_lote"), tipo,
                f"{qty:.0f}", f"{bultos}",
                str(r.get("prod_date")), r.get("status")
            ]
            for i, v in enumerate(vals):
                self.table_exist.setItem(row, i, QtWidgets.QTableWidgetItem(str(v)))

    def _llenar_historial(self, data):
        self.table_hist.setRowCount(0)
        for r in data:
            row = self.table_hist.rowCount()
            self.table_hist.insertRow(row)
            
            tipo = str(r.get("type", "")) # Ojo con esto
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor) if factor else 0
            
            vals = [
                str(r.get("date")), r.get("guide"), r.get("client"),
                r.get("product"), r.get("lote"),
                f"{qty:.0f}", f"{bultos}"
            ]
            for i, v in enumerate(vals):
                self.table_hist.setItem(row, i, QtWidgets.QTableWidgetItem(str(v)))

    def _filtrar_existencias(self, text):
        t = text.lower()
        res = [x for x in self.data_existencias if t in str(x).lower()]
        self._llenar_existencias(res)