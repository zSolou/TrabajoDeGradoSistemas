from PySide6 import QtCore, QtWidgets, QtGui
from datetime import date
from core import repo, theme

class DespachoScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_inventory = None # Guardará el objeto Inventory seleccionado
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        lbl_title = QtWidgets.QLabel("DESPACHO DE MERCANCÍA")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        layout.addWidget(lbl_title)

        # --- Formulario ---
        form_frame = QtWidgets.QFrame()
        form_frame.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-radius: 8px; border: 1px solid {theme.BORDER_COLOR};")
        form_layout = QtWidgets.QFormLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # 1. Cliente
        self.cb_client = QtWidgets.QComboBox()
        self.cb_client.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 5px;")
        form_layout.addRow("Cliente / Destino:", self.cb_client)

        # 2. Selección de Producto (Buscador + Info)
        prod_layout = QtWidgets.QHBoxLayout()
        self.btn_select_prod = QtWidgets.QPushButton("🔍 Buscar Lote en Inventario")
        self.btn_select_prod.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_select_prod.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; padding: 6px; font-weight: bold;")
        self.btn_select_prod.clicked.connect(self._open_product_selector)
        
        self.lbl_prod_info = QtWidgets.QLabel("Ningún lote seleccionado")
        self.lbl_prod_info.setStyleSheet("color: #ff6b6b; font-style: italic;")
        
        prod_layout.addWidget(self.btn_select_prod)
        prod_layout.addWidget(self.lbl_prod_info)
        form_layout.addRow("Producto a Despachar:", prod_layout)

        # 3. Cantidad a Sacar
        self.spin_qty = QtWidgets.QDoubleSpinBox()
        self.spin_qty.setRange(0, 999999)
        self.spin_qty.setDecimals(2)
        self.spin_qty.setEnabled(False) # Se activa al elegir producto
        self.spin_qty.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")
        form_layout.addRow("Cantidad a Despachar:", self.spin_qty)

        # 4. Guía y Fecha
        self.inp_guide = QtWidgets.QLineEdit()
        self.inp_guide.setPlaceholderText("Nro. Guía de Movilización (SADA/INSAI)")
        self.inp_guide.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 5px;")
        
        self.date_edit = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_edit.setDate(date.today())
        self.date_edit.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")
        
        form_layout.addRow("Nro. Guía:", self.inp_guide)
        form_layout.addRow("Fecha Despacho:", self.date_edit)

        layout.addWidget(form_frame)

        # Botón Acción
        self.btn_process = QtWidgets.QPushButton("CONFIRMAR SALIDA")
        self.btn_process.setMinimumHeight(50)
        self.btn_process.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_process.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; font-size: 12pt; border-radius: 5px; }}
            QPushButton:hover {{ background-color: #00cfa5; }}
        """)
        self.btn_process.clicked.connect(self._process_dispatch)
        layout.addWidget(self.btn_process)
        
        layout.addStretch()
        self.refresh_clients()

    def refresh_clients(self):
        self.cb_client.clear()
        try:
            clients = repo.list_clients(solo_activos=True)
            for c in clients:
                self.cb_client.addItem(c.name, c.id)
        except: pass

    def _open_product_selector(self):
        dialog = ProductSelectorDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.selected_inventory = dialog.selected_data
            self._update_ui_with_product()

    def _update_ui_with_product(self):
        if not self.selected_inventory: return
        
        inv = self.selected_inventory
        # Mostrar info clara: Nombre del producto + SKU del lote
        # inv.product_name viene de la consulta en repo.py
        p_name = getattr(inv, 'product_name', 'Producto') 
        
        info = f"PROD: {p_name}\nLOTE: {inv.nro_lote or 'Sin Lote'} (SKU: {inv.sku})\nDISPONIBLE: {inv.quantity:.2f}"
        self.lbl_prod_info.setText(info)
        self.lbl_prod_info.setStyleSheet("color: #00f2c3; font-weight: bold;")
        
        # Configurar limites del spinbox
        self.spin_qty.setEnabled(True)
        self.spin_qty.setMaximum(float(inv.quantity))
        self.spin_qty.setValue(0)
        self.spin_qty.setFocus()

    def _process_dispatch(self):
        if not self.selected_inventory:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleccione un lote del inventario primero.")
            return
        
        qty = self.spin_qty.value()
        if qty <= 0:
            QtWidgets.QMessageBox.warning(self, "Error", "La cantidad debe ser mayor a 0.")
            return

        client_name = self.cb_client.currentText()
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar Despacho",
            f"¿Confirma la salida de {qty} unidades?\n"
            f"Cliente: {client_name}\n\n"
            "El inventario se descontará automáticamente.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                data = {
                    "inventory_id": self.selected_inventory.id,
                    "client_id": self.cb_client.currentData(),
                    "quantity": qty,
                    "date": self.date_edit.date().toPython(),
                    "guide": self.inp_guide.text(),
                    "obs": ""
                }
                repo.create_dispatch(data)
                
                QtWidgets.QMessageBox.information(self, "Éxito", "Despacho registrado correctamente.\nInventario actualizado.")
                
                # Reset UI
                self.selected_inventory = None
                self.lbl_prod_info.setText("Ningún lote seleccionado")
                self.lbl_prod_info.setStyleSheet("color: #ff6b6b;")
                self.spin_qty.setValue(0)
                self.spin_qty.setEnabled(False)
                self.inp_guide.clear()
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

class ProductSelectorDialog(QtWidgets.QDialog):
    """Buscador emergente de lotes disponibles"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Lote Disponible")
        self.resize(750, 450)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: white;")
        self.selected_data = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Filtrar por Nombre, SKU o Lote...")
        self.search.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 6px; border: 1px solid {theme.BORDER_COLOR};")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        self.table = QtWidgets.QTableWidget()
        cols = ["Producto", "Lote", "SKU", "Disponible", "Calidad", "F. Prod"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"background-color: {theme.BG_INPUT}; alternate-background-color: {theme.BG_SIDEBAR}; gridline-color: {theme.BORDER_COLOR};")
        self.table.doubleClicked.connect(self._select)
        layout.addWidget(self.table)

        btn = QtWidgets.QPushButton("Seleccionar Lote")
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; padding: 10px; font-weight: bold;")
        btn.clicked.connect(self._select)
        layout.addWidget(btn)

    def _load_data(self):
        self.inventory_items = repo.get_available_inventory()
        self._populate(self.inventory_items)

    def _populate(self, data):
        self.table.setRowCount(0)
        for inv in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            p_name = getattr(inv, 'product_name', '---')
            
            vals = [
                p_name,
                inv.nro_lote or "-", 
                inv.sku, 
                f"{inv.quantity:.2f}", 
                inv.quality or "", 
                str(inv.prod_date)
            ]
            
            for i, v in enumerate(vals):
                item = QtWidgets.QTableWidgetItem(str(v))
                if i == 0: item.setData(QtCore.Qt.UserRole, inv)
                self.table.setItem(r, i, item)

    def _filter(self, text):
        text = text.lower()
        filtered = []
        for inv in self.inventory_items:
            p_name = getattr(inv, 'product_name', '').lower()
            sku = (inv.sku or '').lower()
            lote = (inv.nro_lote or '').lower()
            
            if text in p_name or text in sku or text in lote:
                filtered.append(inv)
        self._populate(filtered)

    def _select(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_data = self.table.item(row, 0).data(QtCore.Qt.UserRole)
            self.accept()