from PySide6 import QtCore, QtWidgets
from core import theme

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
        self.title.setStyleSheet(f"font-weight:600; font-size:14pt; color: {theme.ACCENT_COLOR};")
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.title, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        
        header_layout.addStretch(1)

        self.product_type = QtWidgets.QComboBox()
        self.product_type.setMinimumWidth(200)
        self.product_type.addItems(["-- Seleccione Producto --", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        self.product_type.setStyleSheet(f"""
            QComboBox {{ background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 5px; border-radius: 4px; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        header_layout.addWidget(self.product_type)
        header_layout.addWidget(self.product_type, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        main.addWidget(header)

        # --- Formulario ---
        self.form_container = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_container)
        form_layout.setSpacing(12)

        self.sku = QtWidgets.QLineEdit()
        self.sku.setVisible(False)

        # FECHAS
        self.prod_date = self._create_date_edit()
        self.dispatch_date = self._create_date_edit()

        # MEDIDAS (Validaciones aplicadas aquí)
        # Largo: Máximo 6 metros (estándar de madera), 2 decimales
        self.largo = self._create_spinbox("m", max_val=6.00) 
        
        # Ancho y Espesor: Máximo 30 cm, 2 decimales
        self.ancho = self._create_spinbox("cm", max_val=30.00)
        self.espesor = self._create_spinbox("cm", max_val=30.00)
        
        # Piezas
        self.piezas = QtWidgets.QSpinBox()
        self.piezas.setRange(0, 1000000)
        self.piezas.setSuffix(" un.")
        self.piezas.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; border-radius: 4px;")

        # Combos
        self.quality = self._create_combo(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self.drying = self._create_combo(["Sí", "No"])
        self.planing = self._create_combo(["Sí", "No"])
        self.impregnated = self._create_combo(["Sí", "No"])
        
        self.obs = QtWidgets.QPlainTextEdit()
        self.obs.setFixedHeight(60)
        self.obs.setPlaceholderText("Observaciones opcionales...")
        self.obs.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px;")

        # Filas
        self.rows = {}
        self.rows['prod_date'] = self._add_row(form_layout, "Fecha Producción:", self.prod_date)
        self.rows['dispatch_date'] = self._add_row(form_layout, "Fecha Despacho:", self.dispatch_date)
        self.rows['largo'] = self._add_row(form_layout, "Largo (Máx 6m):", self.largo)
        self.rows['ancho'] = self._add_row(form_layout, "Ancho (Máx 30cm):", self.ancho)
        self.rows['espesor'] = self._add_row(form_layout, "Espesor (Máx 30cm):", self.espesor)
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
        self.save_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_PRIMARY}; color: white; font-weight: bold; border-radius: 4px; }}
            QPushButton:hover {{ background-color: #0b5ed7; }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        main.addLayout(btn_layout)

        self.product_type.currentTextChanged.connect(self._on_product_change)

    def _create_spinbox(self, suffix, max_val=1000.00):
        sb = QtWidgets.QDoubleSpinBox()
        sb.setRange(0.00, max_val)
        sb.setDecimals(2)
        sb.setSingleStep(0.1)
        sb.setSuffix(f" {suffix}")
        sb.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; border-radius: 4px;")
        return sb

    def _create_date_edit(self):
        de = QtWidgets.QDateEdit(calendarPopup=True)
        de.setDate(QtCore.QDate.currentDate())
        de.setDisplayFormat("dd/MM/yyyy")
        de.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; border-radius: 4px;")
        return de

    def _create_combo(self, items):
        cb = QtWidgets.QComboBox()
        cb.addItems(items)
        cb.setStyleSheet(f"""
            QComboBox {{ background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; border-radius: 4px; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        return cb

    def _add_row(self, layout, label, widget):
        container = QtWidgets.QWidget()
        l = QtWidgets.QHBoxLayout(container)
        l.setContentsMargins(0,0,0,0)
        lbl = QtWidgets.QLabel(label)
        lbl.setMinimumWidth(140)
        lbl.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")
        l.addWidget(lbl)
        l.addWidget(widget)
        layout.addRow(container)
        return container

    def _on_product_change(self, text):
        if text.startswith("--"):
            self.form_container.setVisible(False)
            return
        
        self.form_container.setVisible(True)
        
        show_map = {
            "Tablas": ["largo", "ancho", "espesor", "piezas"],
            "Tablones": ["largo", "ancho", "espesor", "piezas"],
            "Paletas": ["largo", "ancho", "espesor", "piezas"],
            "Machihembrado": ["largo", "ancho", "piezas"] # Machihembrado no usa espesor
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
        
        # 1. Validación de Fechas
        f_prod = self.prod_date.date()
        f_desp = self.dispatch_date.date()
        
        if f_desp < f_prod:
            QtWidgets.QMessageBox.warning(self, "Fecha Inválida", 
                "La **Fecha de Despacho** no puede ser anterior a la Fecha de Producción.\n"
                "Verifique las fechas ingresadas.")
            self.dispatch_date.setFocus()
            return False

        # 2. Validación de Piezas
        if self.piezas.value() <= 0:
            QtWidgets.QMessageBox.warning(self, "Dato Faltante", "El número de **Piezas** no puede ser 0.")
            self.piezas.setFocus()
            return False

        # 3. Validaciones de Medidas
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

        # Validar Inputs
        if not self._validate_input(tipo):
            return

        # Confirmación
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar Registro",
            f"¿Está seguro de registrar:\n\nProducto: {tipo}\nCantidad: {self.piezas.value()} piezas?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm == QtWidgets.QMessageBox.No:
            return

        # Cálculo
        sku = self._generate_sku(tipo)
        # Cálculo de volumen: m * m * m = m3. (Ojo: ancho y espesor vienen en cm, convertir a m)
        largo_m = self.largo.value()
        ancho_m = self.ancho.value() / 100.0
        espesor_m = self.espesor.value() / 100.0
        
        if tipo in ("Tablas", "Tablones", "Paletas"):
            cantidad = largo_m * ancho_m * espesor_m * self.piezas.value()
            unidad = "m3"
        elif tipo == "Machihembrado":
            # Machihembrado suele venderse por m2 cubiertos
            cantidad = largo_m * ancho_m * self.piezas.value()
            unidad = "m2"
        else:
            cantidad = 0
            unidad = "u"

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
        self.prod_date.setDate(QtCore.QDate.currentDate())
        self.dispatch_date.setDate(QtCore.QDate.currentDate())

    def _generate_sku(self, base: str) -> str:
        base_clean = "".join(ch for ch in base.upper() if ch.isalnum())[:3]
        ts = QtCore.QDateTime.currentDateTime().toString("ddHHmmss")
        return f"{base_clean}-{ts}"