import csv
import os
from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

# Factores para calcular bultos visualmente
FACTORES_CONVERSION = {
    "Tablas": 30,
    "Tablones": 20,
    "Paletas": 10,
    "Machihembrado": 5
}

# Verificar Excel
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# --- DIÁLOGO DE EDICIÓN (Sin cambios mayores) ---
class EditarProductoDialog(QtWidgets.QDialog):
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
        
        content = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content)
        form.setSpacing(12)
        
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

        self.inp_calidad = QtWidgets.QComboBox()
        self.inp_calidad.addItems(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self.inp_calidad.setCurrentText(self.data.get('quality', ''))
        self.inp_calidad.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 4px;")

        self.inp_obs = QtWidgets.QPlainTextEdit(str(self.data.get('obs') or ""))
        self.inp_obs.setFixedHeight(60)
        self.inp_obs.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")

        form.addRow("Nro. Lote:", self.inp_lote)
        form.addRow("Cantidad (Piezas):", self.inp_qty)
        form.addRow("Largo (m):", self.inp_l)
        form.addRow("Ancho (cm):", self.inp_a)
        form.addRow("Espesor (cm):", self.inp_e)
        form.addRow("Fecha Prod:", self.inp_date)
        form.addRow("Calidad:", self.inp_calidad)
        form.addRow("Obs:", self.inp_obs)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_box = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Guardar")
        btn_save.clicked.connect(self.accept)
        btn_save.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; padding: 8px;")
        
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; padding: 8px;")
        
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def _spinbox(self, val):
        sb = QtWidgets.QDoubleSpinBox()
        sb.setRange(0, 999999)
        sb.setValue(val)
        sb.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 4px;")
        return sb

    def get_data(self):
        return {
            "id": self.data["id"],
            "nro_lote": self.inp_lote.text(),
            "quantity": self.inp_qty.value(),
            "largo": self.inp_l.value(),
            "ancho": self.inp_a.value(),
            "espesor": self.inp_e.value(),
            "prod_date": self.inp_date.date().toString("yyyy-MM-dd"),
            "quality": self.inp_calidad.currentText(),
            "obs": self.inp_obs.toPlainText()
        }

# --- PANTALLA PRINCIPAL CON PESTAÑAS ---
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
        
        # Título General
        lbl = QtWidgets.QLabel("CONTROL DE INVENTARIO Y SALIDAS")
        lbl.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(lbl)

        # Sistema de Pestañas
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme.BORDER_COLOR}; }}
            QTabBar::tab {{
                background: {theme.BG_SIDEBAR};
                color: {theme.TEXT_SECONDARY};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {theme.BTN_PRIMARY};
                color: white;
            }}
        """)
        
        # Pestaña 1: Existencias
        self.tab_existencias = QtWidgets.QWidget()
        self._setup_tab_existencias(self.tab_existencias)
        self.tabs.addTab(self.tab_existencias, "📦 Existencias en Patio")
        
        # Pestaña 2: Historial
        self.tab_historial = QtWidgets.QWidget()
        self._setup_tab_historial(self.tab_historial)
        self.tabs.addTab(self.tab_historial, "🚛 Historial de Despachos")
        
        layout.addWidget(self.tabs)

    # --- UI Pestaña Existencias ---
    def _setup_tab_existencias(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        
        # Barra superior
        top_bar = QtWidgets.QHBoxLayout()
        self.search_exist = QtWidgets.QLineEdit()
        self.search_exist.setPlaceholderText("🔍 Buscar Lote, SKU...")
        self.search_exist.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 6px; border-radius: 4px;")
        self.search_exist.textChanged.connect(self._filtrar_existencias)
        
        btn_edit = QtWidgets.QPushButton("✎ Editar"); btn_edit.clicked.connect(self._editar_producto)
        btn_del = QtWidgets.QPushButton("🗑 Eliminar"); btn_del.clicked.connect(self._eliminar_producto)
        btn_xls = QtWidgets.QPushButton("📊 Excel"); btn_xls.clicked.connect(lambda: self._exportar_excel("existencias"))
        
        for b, c in [(btn_edit, theme.BTN_PRIMARY), (btn_del, theme.BTN_DANGER), (btn_xls, "#217346")]:
            b.setCursor(QtCore.Qt.PointingHandCursor)
            b.setStyleSheet(f"background-color: {c}; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        
        top_bar.addWidget(self.search_exist)
        top_bar.addWidget(btn_edit)
        top_bar.addWidget(btn_del)
        top_bar.addWidget(btn_xls)
        layout.addLayout(top_bar)

        # Tabla Existencias
        self.table_exist = QtWidgets.QTableWidget()
        cols = ["ID", "SKU", "LOTE", "Producto", "Existencia", "Bultos", "Largo", "Ancho", "Espesor", "Calidad", "F. Prod", "Estado"]
        self.table_exist.setColumnCount(len(cols))
        self.table_exist.setHorizontalHeaderLabels(cols)
        self._estilizar_tabla(self.table_exist)
        layout.addWidget(self.table_exist)

    # --- UI Pestaña Historial ---
    def _setup_tab_historial(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        
        # Barra superior
        top_bar = QtWidgets.QHBoxLayout()
        self.search_hist = QtWidgets.QLineEdit()
        self.search_hist.setPlaceholderText("🔍 Buscar por Cliente, Guía, Lote...")
        self.search_hist.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 6px; border-radius: 4px;")
        self.search_hist.textChanged.connect(self._filtrar_historial)
        
        btn_refresh = QtWidgets.QPushButton("🔄 Actualizar"); btn_refresh.clicked.connect(self.refresh)
        btn_xls = QtWidgets.QPushButton("📊 Excel Historial"); btn_xls.clicked.connect(lambda: self._exportar_excel("historial"))
        
        for b, c in [(btn_refresh, theme.BTN_PRIMARY), (btn_xls, "#217346")]:
            b.setCursor(QtCore.Qt.PointingHandCursor)
            b.setStyleSheet(f"background-color: {c}; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")

        top_bar.addWidget(self.search_hist)
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_xls)
        layout.addLayout(top_bar)

        # Tabla Historial
        self.table_hist = QtWidgets.QTableWidget()
        cols = ["ID", "Fecha", "Guía", "Cliente", "Producto", "Lote", "SKU", "Cant. Salida", "Bultos Salida"]
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

    # --- LOGICA DE DATOS ---
    def refresh(self):
        try:
            # 1. Cargar Existencias
            self.data_existencias = repo.list_inventory_rows()
            self._llenar_existencias(self.data_existencias)
            
            # 2. Cargar Historial
            self.data_historial = repo.list_dispatches_history()
            self._llenar_historial(self.data_historial)
            
        except Exception as e:
            print(f"Error refresh: {e}")

    def _llenar_existencias(self, data):
        self.table_exist.setRowCount(0)
        for r in data:
            row = self.table_exist.rowCount()
            self.table_exist.insertRow(row)
            
            tipo = str(r.get("product_type", ""))
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor)
            
            vals = [
                str(r.get("id")), r.get("sku"), r.get("nro_lote"), tipo,
                f"{qty:.0f}", f"{bultos}",
                str(r.get("largo")), str(r.get("ancho")), str(r.get("espesor")),
                r.get("quality"), str(r.get("prod_date")), r.get("status")
            ]
            for i, v in enumerate(vals):
                it = QtWidgets.QTableWidgetItem(str(v))
                if i==0: it.setData(QtCore.Qt.UserRole, r)
                self.table_exist.setItem(row, i, it)

    def _llenar_historial(self, data):
        self.table_hist.setRowCount(0)
        for r in data:
            row = self.table_hist.rowCount()
            self.table_hist.insertRow(row)
            
            tipo = str(r.get("type", ""))
            qty = float(r.get("quantity", 0))
            factor = FACTORES_CONVERSION.get(tipo, 1)
            bultos = int(qty / factor)
            
            vals = [
                str(r.get("id")), str(r.get("date")), r.get("guide"),
                r.get("client"), r.get("product"), r.get("lote"), r.get("sku"),
                f"{qty:.0f}", f"{bultos}"
            ]
            for i, v in enumerate(vals):
                self.table_hist.setItem(row, i, QtWidgets.QTableWidgetItem(str(v)))

    # --- FILTROS ---
    def _filtrar_existencias(self, text):
        t = text.lower()
        res = [x for x in self.data_existencias if t in str(x.get("sku")).lower() or t in str(x.get("nro_lote")).lower() or t in str(x.get("product_type")).lower()]
        self._llenar_existencias(res)

    def _filtrar_historial(self, text):
        t = text.lower()
        res = [x for x in self.data_historial if t in str(x.get("client")).lower() or t in str(x.get("guide")).lower() or t in str(x.get("lote")).lower()]
        self._llenar_historial(res)

    # --- ACCIONES ---
    def _get_selected_existencia(self):
        row = self.table_exist.currentRow()
        if row < 0: return None
        return self.table_exist.item(row, 0).data(QtCore.Qt.UserRole)

    def _eliminar_producto(self):
        data = self._get_selected_existencia()
        if not data: return
        if QtWidgets.QMessageBox.question(self, "Eliminar", "¿Borrar este lote?") == QtWidgets.QMessageBox.Yes:
            repo.delete_inventory(data['id'])
            self.refresh()

    def _editar_producto(self):
        data = self._get_selected_existencia()
        if not data: return
        dlg = EditarProductoDialog(data, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            repo.update_inventory(dlg.get_data())
            self.refresh()

    def _exportar_excel(self, tipo):
        if not OPENPYXL_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Error", "Instale openpyxl")
            return
        
        filename = "inventario.xlsx" if tipo == "existencias" else "historial_despachos.xlsx"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Guardar Excel", filename, "Excel (*.xlsx)")
        if not path: return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Datos"
            
            if tipo == "existencias":
                ws.append(["ID", "SKU", "LOTE", "Producto", "Existencia", "Bultos", "Largo", "Ancho", "Espesor", "Calidad", "F. Prod", "Estado"])
                for r in self.data_existencias:
                    f = FACTORES_CONVERSION.get(r.get("product_type"), 1)
                    q = float(r.get("quantity", 0))
                    ws.append([
                        r.get("id"), r.get("sku"), r.get("nro_lote"), r.get("product_type"),
                        q, int(q/f),
                        float(r.get("largo") or 0), float(r.get("ancho") or 0), float(r.get("espesor") or 0),
                        r.get("quality"), str(r.get("prod_date")), r.get("status")
                    ])
            else:
                ws.append(["ID", "Fecha", "Guía", "Cliente", "Producto", "Lote", "SKU", "Cant. Salida", "Bultos Salida", "Observación"])
                for r in self.data_historial:
                    f = FACTORES_CONVERSION.get(r.get("type"), 1)
                    q = float(r.get("quantity", 0))
                    ws.append([
                        r.get("id"), str(r.get("date")), r.get("guide"), r.get("client"),
                        r.get("product"), r.get("lote"), r.get("sku"),
                        q, int(q/f), r.get("obs")
                    ])
            
            wb.save(path)
            QtWidgets.QMessageBox.information(self, "Éxito", f"Archivo guardado en:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))