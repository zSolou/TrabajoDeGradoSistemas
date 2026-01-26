# screens/registrar.py
from PySide6 import QtCore, QtWidgets

class RegistrarForm(QtWidgets.QWidget):
    saved_signal = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # --- Encabezado ---
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title = QtWidgets.QLabel("REGISTRAR PRODUCTO")
        self.title.setStyleSheet("font-weight:600; font-size:16pt; color: #32D424;")
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.title, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        header_layout.addStretch(1)

        self.product_type = QtWidgets.QComboBox()
        self.product_type.setMinimumWidth(200)
        # Agregamos un item inválido al inicio para forzar la elección
        self.product_type.addItems(["-- Seleccione Producto --", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        header_layout.addWidget(self.product_type)
        header_layout.addWidget(self.product_type, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        main.addWidget(header)

        # --- Formulario ---
        self.form_container = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_container)
        form_layout.setSpacing(12)

        self.sku = QtWidgets.QLineEdit()
        self.sku.setVisible(False)

        self.prod_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.prod_date.setDate(QtCore.QDate.currentDate())
        self.prod_date.setDisplayFormat("dd/MM/yyyy") # Formato latino

        self.dispatch_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.dispatch_date.setDate(QtCore.QDate.currentDate())
        self.dispatch_date.setDisplayFormat("dd/MM/yyyy")

        # Configuración de SpinBoxes para evitar negativos
        # El rango 0-1000 evita negativos, pero permitiremos 0 visualmente y lo bloquearemos al guardar
        self.largo = self._create_spinbox("m")
        self.ancho = self._create_spinbox("cm")
        self.espesor = self._create_spinbox("cm")
        
        self.piezas = QtWidgets.QSpinBox()
        self.piezas.setRange(0, 1000000)
        self.piezas.setSuffix(" un.")

        # Combos
        self.quality = QtWidgets.QComboBox()
        self.quality.addItems(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        
        self.drying = QtWidgets.QComboBox(); self.drying.addItems(["Sí", "No"])
        self.planing = QtWidgets.QComboBox(); self.planing.addItems(["Sí", "No"])
        self.impregnated = QtWidgets.QComboBox(); self.impregnated.addItems(["Sí", "No"])
        
        self.obs = QtWidgets.QPlainTextEdit()
        self.obs.setFixedHeight(60)
        self.obs.setPlaceholderText("Observaciones opcionales...")

        # Filas
        self.rows = {}
        self.rows['prod_date'] = self._add_row(form_layout, "Fecha Producción:", self.prod_date)
        self.rows['dispatch_date'] = self._add_row(form_layout, "Fecha Despacho:", self.dispatch_date)
        self.rows['largo'] = self._add_row(form_layout, "Largo (m):", self.largo)
        self.rows['ancho'] = self._add_row(form_layout, "Ancho (cm):", self.ancho)
        self.rows['espesor'] = self._add_row(form_layout, "Espesor (cm):", self.espesor)
        self.rows['piezas'] = self._add_row(form_layout, "Nº Piezas:", self.piezas)
        self.rows['quality'] = self._add_row(form_layout, "Calidad:", self.quality)
        self.rows['drying'] = self._add_row(form_layout, "Secado:", self.drying)
        self.rows['planing'] = self._add_row(form_layout, "Cepillado:", self.planing)
        self.rows['impregnated'] = self._add_row(form_layout, "Impregnado:", self.impregnated)
        self.rows['obs'] = self._add_row(form_layout, "Observación:", self.obs)

        self.form_container.setVisible(False)
        main.addWidget(self.form_container)

        # --- Botón ---
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QtWidgets.QPushButton("Guardar Producto")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setMinimumWidth(150)
        # Estilo para que destaque
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #0d6efd; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        main.addLayout(btn_layout)

        self.product_type.currentTextChanged.connect(self._on_product_change)

    def _create_spinbox(self, suffix):
        sb = QtWidgets.QDoubleSpinBox()
        sb.setRange(0.00, 1000.00) # Rango seguro
        sb.setDecimals(2)
        sb.setSingleStep(0.1)
        sb.setSuffix(f" {suffix}")
        return sb

    def _add_row(self, layout, label, widget):
        container = QtWidgets.QWidget()
        l = QtWidgets.QHBoxLayout(container)
        l.setContentsMargins(0,0,0,0)
        lbl = QtWidgets.QLabel(label)
        lbl.setMinimumWidth(140)
        l.addWidget(lbl)
        l.addWidget(widget)
        layout.addRow(container)
        return container

    def _on_product_change(self, text):
        if text.startswith("--"):
            self.form_container.setVisible(False)
            return
        
        self.form_container.setVisible(True)
        # Lógica de visibilidad (simplificada)
        show_map = {
            "Tablas": ["largo", "ancho", "espesor", "piezas"],
            "Tablones": ["largo", "ancho", "espesor", "piezas"],
            "Paletas": ["largo", "ancho", "espesor", "piezas"],
            "Machihembrado": ["largo", "ancho", "piezas"] # Machihembrado no usa espesor en tu lógica
        }
        
        commons = ["prod_date", "dispatch_date", "quality", "drying", "planing", "impregnated", "obs"]
        
        # Ocultar todo primero
        for w in self.rows.values(): w.setVisible(False)
        
        # Mostrar lo necesario
        targets = show_map.get(text, []) + commons
        for key in targets:
            if key in self.rows:
                self.rows[key].setVisible(True)

    def _validate_input(self, tipo):
        """Retorna True si todo es válido, o muestra error y retorna False."""
        
        # Validación genérica: Piezas
        if self.piezas.value() <= 0:
            QtWidgets.QMessageBox.warning(self, "Dato Faltante", "El número de **Piezas** no puede ser 0.")
            self.piezas.setFocus()
            return False

        # Validaciones específicas
        if tipo in ("Tablas", "Tablones", "Paletas"):
            if self.largo.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medida Inválida", "Ingrese el **Largo**.")
                self.largo.setFocus()
                return False
            if self.ancho.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medida Inválida", "Ingrese el **Ancho**.")
                self.ancho.setFocus()
                return False
            if self.espesor.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medida Inválida", "Ingrese el **Espesor**.")
                self.espesor.setFocus()
                return False

        elif tipo == "Machihembrado":
            if self.largo.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medida Inválida", "Ingrese el **Largo**.")
                self.largo.setFocus()
                return False
            if self.ancho.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medida Inválida", "Ingrese el **Ancho**.")
                self.ancho.setFocus()
                return False
            
        return True

    def _on_save(self):
        tipo = self.product_type.currentText()
        if tipo.startswith("--"):
            QtWidgets.QMessageBox.warning(self, "Error", "Seleccione un tipo de producto.")
            return

        # 1. Validar Inputs
        if not self._validate_input(tipo):
            return

        # 2. Confirmación (Fundamental para Tesis)
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar Registro",
            f"¿Está seguro de registrar:\n\nProducto: {tipo}\nCantidad: {self.piezas.value()} piezas?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm == QtWidgets.QMessageBox.No:
            return

        # 3. Cálculo
        sku = self._generate_sku(tipo)
        if tipo in ("Tablas", "Tablones", "Paletas"):
            cantidad = self.largo.value() * self.ancho.value() * self.espesor.value() * self.piezas.value()
            unidad = "m3"
        elif tipo == "Machihembrado":
            cantidad = self.largo.value() * self.ancho.value() * self.piezas.value()
            unidad = "m2"
        
        # Construcción del dict
        data = {
            "sku": sku,
            "name": tipo,
            "product_type": tipo,
            "quantity": cantidad,
            "unit": unidad,
            "largo": self.largo.value(),
            "ancho": self.ancho.value(),
            "espesor": self.espesor.value() if tipo != "Machihembrado" else 0,
            "piezas": self.piezas.value(),
            "prod_date": self.prod_date.date().toString(QtCore.Qt.ISODate),
            "dispatch_date": self.dispatch_date.date().toString(QtCore.Qt.ISODate),
            "quality": self.quality.currentText(),
            "drying": self.drying.currentText(),
            "planing": self.planing.currentText(),
            "impregnated": self.impregnated.currentText(),
            "obs": self.obs.toPlainText()
        }

        self.saved_signal.emit(data)
        
        QtWidgets.QMessageBox.information(self, "Éxito", "Producto registrado correctamente en Inventario.")
        self._clear_form()

    def _clear_form(self):
        self.product_type.setCurrentIndex(0)
        self.largo.setValue(0); self.ancho.setValue(0); self.espesor.setValue(0); self.piezas.setValue(0)
        self.obs.clear()
        # Resetear fechas a hoy
        self.prod_date.setDate(QtCore.QDate.currentDate())
        self.dispatch_date.setDate(QtCore.QDate.currentDate())

    def _generate_sku(self, base: str) -> str:
        # Generamos un SKU único basado en fecha/hora
        base_clean = "".join(ch for ch in base.upper() if ch.isalnum())[:3]
        ts = QtCore.QDateTime.currentDateTime().toString("ddHHmmss")
        return f"{base_clean}-{ts}"