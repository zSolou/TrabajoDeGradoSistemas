from PySide6 import QtCore, QtWidgets, QtGui
from datetime import date
from core import repo, theme

# Factores de conversión
FACTORES_CONVERSION = {
    "Tablas": 30,
    "Tablones": 20,
    "Paletas": 10,
    "Machihembrado": 5
}

class DespachoScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_inventory = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_title = QtWidgets.QLabel("DESPACHO DE MERCANCÍA")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        layout.addWidget(lbl_title)

        form_frame = QtWidgets.QFrame()
        form_frame.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-radius: 8px; border: 1px solid {theme.BORDER_COLOR};")
        form_layout = QtWidgets.QFormLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        self.cb_client = QtWidgets.QComboBox()
        self.cb_client.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 5px;")
        form_layout.addRow("Cliente / Destino:", self.cb_client)

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

        self.spin_qty = QtWidgets.QSpinBox() 
        self.spin_qty.setRange(0, 999999)
        self.spin_qty.setSuffix(" Bultos")
        self.spin_qty.setEnabled(False) 
        self.spin_qty.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")
        form_layout.addRow("Cantidad a Despachar:", self.spin_qty)

        self.inp_guide = QtWidgets.QLineEdit()
        self.inp_guide.setPlaceholderText("Nro. Guía de Movilización (SADA/INSAI)")
        self.inp_guide.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; padding: 5px;")
        
        # --- CAMBIO: LÍMITE MÁXIMO DE CARACTERES PARA LA GUÍA ---
        self.inp_guide.setMaxLength(10)
        # --------------------------------------------------------
        
        self.date_edit = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_edit.setDate(date.today())
        self.date_edit.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white;")
        
        form_layout.addRow("Nro. Guía (Máx 10):", self.inp_guide) # Etiqueta actualizada
        form_layout.addRow("Fecha Despacho:", self.date_edit)

        layout.addWidget(form_frame)

        self.btn_process = QtWidgets.QPushButton("CONFIRMAR SALIDA")
        self.btn_process.setMinimumHeight(50)
        self.btn_process.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_process.setStyleSheet(f"QPushButton {{ background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; font-size: 12pt; border-radius: 5px; }} QPushButton:hover {{ background-color: #00cfa5; }}")
        self.btn_process.clicked.connect(self._process_dispatch)
        layout.addWidget(self.btn_process)
        
        layout.addStretch()
        self.refresh_clients()

    def refresh_clients(self):
        self.cb_client.clear()
        try:
            clients = repo.list_clients(solo_activos=True)
            if not clients:
                self.cb_client.addItem("-- Sin Clientes Registrados --", None)
            else:
                for c in clients: self.cb_client.addItem(c.name, c.id)
        except: pass

    def _open_product_selector(self):
        dialog = ProductSelectorDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.selected_inventory = dialog.selected_data
            self._update_ui_with_product()

    def _update_ui_with_product(self):
        if not self.selected_inventory: return
        
        inv = self.selected_inventory
        p_name = getattr(inv, 'product_name', 'Producto')
        
        factor = FACTORES_CONVERSION.get(p_name, 1)
        bultos_disponibles = float(inv.quantity) / factor
        
        # Formatear fecha de producción para mostrar
        f_prod = "Sin Fecha"
        if inv.prod_date:
            f_prod = inv.prod_date.strftime("%d/%m/%Y")

        info = (f"PROD: {p_name} | LOTE: {inv.nro_lote or '-'}\n"
                f"📅 FABRICADO: {f_prod}\n" 
                f"DISPONIBLE: {inv.quantity:.0f} Piezas (~{int(bultos_disponibles)} Bultos)")
        
        self.lbl_prod_info.setText(info)
        self.lbl_prod_info.setStyleSheet("color: #00f2c3; font-weight: bold;")
        
        self.spin_qty.setEnabled(True)
        self.spin_qty.setMaximum(int(bultos_disponibles))
        self.spin_qty.setValue(0)
        self.spin_qty.setFocus()

    def _process_dispatch(self):
        # 1. Validar Lote Seleccionado
        if not self.selected_inventory:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleccione un lote para despachar.")
            return
        
        # 2. Validar Cliente
        client_id = self.cb_client.currentData()
        if not client_id:
            QtWidgets.QMessageBox.warning(self, "Error", "Seleccione un Cliente válido.")
            self.cb_client.setFocus()
            return

        # 3. Validar Cantidad
        bultos_out = self.spin_qty.value()
        if bultos_out <= 0:
            QtWidgets.QMessageBox.warning(self, "Error", "La cantidad a despachar debe ser mayor a 0.")
            self.spin_qty.setFocus()
            return

        # 4. Validar Número de Guía (OBLIGATORIO)
        nro_guia = self.inp_guide.text().strip()
        if not nro_guia:
            QtWidgets.QMessageBox.warning(self, "Falta Dato", "El **Número de Guía** es obligatorio para procesar el despacho.")
            self.inp_guide.setFocus()
            return

        # 5. Validar Fechas (Despacho >= Producción)
        fecha_despacho = self.date_edit.date()
        if self.selected_inventory.prod_date:
            py_date = self.selected_inventory.prod_date
            fecha_prod = QtCore.QDate(py_date.year, py_date.month, py_date.day)
            
            if fecha_despacho < fecha_prod:
                QtWidgets.QMessageBox.warning(
                    self, "Fecha Inválida", 
                    f"⛔ Error de Cronología.\n\n"
                    f"El producto fue fabricado el: {fecha_prod.toString('dd/MM/yyyy')}\n"
                    f"No puede despacharse con fecha anterior.\n"
                )
                return

        # --- Confirmación ---
        prod_type = getattr(self.selected_inventory, 'product_name', '')
        factor = FACTORES_CONVERSION.get(prod_type, 1)
        piezas_out = bultos_out * factor
        client_name = self.cb_client.currentText()

        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar Despacho",
            f"¿Procesar salida de mercancía?\n\n"
            f"📦 Producto: {prod_type}\n"
            f"🔢 Cantidad: {bultos_out} Bultos ({piezas_out:.0f} pzas)\n"
            f"🚛 Cliente: {client_name}\n"
            f"📄 Guía: {nro_guia}",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                data = {
                    "inventory_id": self.selected_inventory.id,
                    "client_id": client_id,
                    "quantity": piezas_out, 
                    "date": self.date_edit.date().toPython(),
                    "guide": nro_guia,
                    "obs": f"Salida de {bultos_out} bultos"
                }
                repo.create_dispatch(data)
                
                QtWidgets.QMessageBox.information(self, "Éxito", "Despacho registrado correctamente.")
                
                # Limpiar formulario
                self.selected_inventory = None
                self.lbl_prod_info.setText("Ningún lote seleccionado")
                self.lbl_prod_info.setStyleSheet("color: #ff6b6b; font-style: italic;")
                self.spin_qty.setValue(0)
                self.spin_qty.setEnabled(False)
                self.inp_guide.clear()
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

class ProductSelectorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Lote Disponible")
        self.resize(800, 450)
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
        cols = ["Producto", "Lote", "SKU", "Existencia", "Bultos", "F. Prod"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet(f"background-color: {theme.BG_INPUT}; alternate-background-color: {theme.BG_SIDEBAR};")
        self.table.doubleClicked.connect(self._select)
        layout.addWidget(self.table)

        btn = QtWidgets.QPushButton("Seleccionar Lote")
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
            factor = FACTORES_CONVERSION.get(p_name, 1)
            bultos = float(inv.quantity) / factor

            vals = [
                p_name,
                inv.nro_lote or "-", 
                inv.sku, 
                f"{inv.quantity:.0f}", 
                f"{int(bultos)}", 
                str(inv.prod_date) # Ya muestra la fecha aquí
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