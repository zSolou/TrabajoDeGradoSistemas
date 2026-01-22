# screens/registrar.py
from PySide6 import QtCore, QtWidgets

class RegistrarForm(QtWidgets.QWidget):
    saved_signal = QtCore.Signal(dict)  # emite los datos del producto al guardarse

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # Layout principal
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # Encabezado: título a la izquierda, selector de tipo a la derecha
        header = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        self.title = QtWidgets.QLabel("REGISTRAR PRODUCTO")
        self.title.setStyleSheet("font-weight:600; font-size:14pt; color: #32D424;")
        header_layout.addWidget(self.title, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        # Spacer para empujar el selector a la derecha
        header_layout.addStretch(1)

        # Selector de tipo de producto (sin Aserrín, con Tablones y Paletas)
        self.product_type = QtWidgets.QComboBox()
        self.product_type.setMinimumWidth(180)
        self.product_type.addItems(["Seleccionar producto", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        header_layout.addWidget(self.product_type, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        main.addWidget(header)

        # Contenedor del formulario dinámico (todo oculto hasta seleccionar tipo)
        self.form_container = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_container)
        form_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        form_layout.setFormAlignment(QtCore.Qt.AlignTop)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(8)

        # Campo SKU (oculto visualmente pero disponible internamente)
        self.sku = QtWidgets.QLineEdit()
        self.sku.setVisible(False)  # no mostrar en UI

        # Fechas
        self.prod_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.prod_date.setDate(QtCore.QDate.currentDate())
        self.dispatch_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.dispatch_date.setDate(QtCore.QDate.currentDate())

        # Medidas: ahora con 2 decimales
        self.largo = QtWidgets.QDoubleSpinBox()
        self.largo.setRange(0, 1000)
        self.largo.setDecimals(2)
        self.largo.setSingleStep(0.01)

        self.ancho = QtWidgets.QDoubleSpinBox()
        self.ancho.setRange(0, 1000)
        self.ancho.setDecimals(2)
        self.ancho.setSingleStep(0.01)

        self.espesor = QtWidgets.QDoubleSpinBox()
        self.espesor.setRange(0, 1000)
        self.espesor.setDecimals(2)
        self.espesor.setSingleStep(0.01)

        self.piezas = QtWidgets.QSpinBox()
        self.piezas.setRange(0, 1_000_000)

        # Otros campos
        self.quality = QtWidgets.QComboBox(); self.quality.addItems(["Tipo 1","Tipo 2","Tipo 3","Tipo 4"])
        self.drying = QtWidgets.QComboBox(); self.drying.addItems(["Sí","No"])
        self.planing = QtWidgets.QComboBox(); self.planing.addItems(["Sí","No"])
        self.impregnated = QtWidgets.QComboBox(); self.impregnated.addItems(["Sí","No"])
        self.obs = QtWidgets.QPlainTextEdit(); self.obs.setFixedHeight(80)

        # Añadir filas al form_layout (se controlará visibilidad por fila)
        self.row_prod_date = self._add_form_row(form_layout, "Fecha de producción", self.prod_date)
        self.row_dispatch_date = self._add_form_row(form_layout, "Fecha de despacho", self.dispatch_date)
        self.row_largo = self._add_form_row(form_layout, "Largo (m)", self.largo)
        self.row_ancho = self._add_form_row(form_layout, "Ancho (cm)", self.ancho)
        self.row_espesor = self._add_form_row(form_layout, "Espesor (cm)", self.espesor)
        self.row_piezas = self._add_form_row(form_layout, "Nº Piezas", self.piezas)
        self.row_quality = self._add_form_row(form_layout, "Calidad", self.quality)
        self.row_drying = self._add_form_row(form_layout, "Secado", self.drying)
        self.row_planing = self._add_form_row(form_layout, "Cepillado", self.planing)
        self.row_impregnated = self._add_form_row(form_layout, "Impregnado", self.impregnated)
        self.row_obs = self._add_form_row(form_layout, "Observación", self.obs)

        # Inicialmente ocultamos el contenedor completo (hasta seleccionar tipo)
        self.form_container.setVisible(True)
        main.addWidget(self.form_container)

        # Botón guardar (debajo del formulario)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.save_btn = QtWidgets.QPushButton("Guardar")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        main.addLayout(btn_row)

        # Conectar selector para mostrar/ocultar y reordenar visualmente
        self.product_type.currentTextChanged.connect(self._on_product_change)
        self._on_product_change(self.product_type.currentText())

    def _add_form_row(self, layout, label_text, widget):
        """Helper: añade una fila al form layout y devuelve el widget contenedor (para visibilidad)."""
        container = QtWidgets.QWidget()
        hl = QtWidgets.QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        lbl = QtWidgets.QLabel(label_text)
        lbl.setMinimumWidth(160)
        hl.addWidget(lbl)
        hl.addWidget(widget, 1)
        layout.addRow(container)
        return container

    def _on_product_change(self, tipo):
        tipo = tipo.strip()
        if tipo not in ("Tablas", "Machihembrado", "Tablones", "Paletas"):
            self.form_container.setVisible(False)
            return

        self.form_container.setVisible(True)

        # Ocultar todas las filas
        for row in (
            self.row_prod_date, self.row_dispatch_date,
            self.row_largo, self.row_ancho, self.row_espesor, self.row_piezas,
            self.row_quality, self.row_drying, self.row_planing, self.row_impregnated, self.row_obs
        ):
            row.setVisible(False)

        # Mostrar según tipo
        if tipo in ("Tablas", "Tablones", "Paletas"):
            for row in (self.row_prod_date, self.row_dispatch_date,
                        self.row_largo, self.row_ancho, self.row_espesor, self.row_piezas):
                row.setVisible(True)
        elif tipo == "Machihembrado":
            for row in (self.row_prod_date, self.row_dispatch_date,
                        self.row_largo, self.row_ancho, self.row_piezas):
                row.setVisible(True)

        # Campos comunes
        for row in (self.row_quality, self.row_drying, self.row_planing, self.row_impregnated, self.row_obs):
            row.setVisible(True)

    def _on_save(self):
        tipo = self.product_type.currentText().strip()
        if tipo not in ("Tablas","Machihembrado","Tablones","Paletas"):
            QtWidgets.QMessageBox.warning(self, "Validación", "Seleccione el tipo de producto.")
            return

        sku = self.sku.text().strip() or self._generate_sku(tipo)

        if tipo in ("Tablas","Tablones","Paletas"):
            if any(v <= 0 for v in (self.largo.value(), self.ancho.value(), self.espesor.value())) or self.piezas.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Validación", "Complete Largo, Ancho, Espesor y Nº Piezas.")
                return
            cantidad = self.largo.value() * self.ancho.value() * self.espesor.value() * self.piezas.value()
            unidad = "m3"
        elif tipo == "Machihembrado":
            if any(v <= 0 for v in (self.largo.value(), self.ancho.value())) or self.piezas.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Validación", "Complete Largo, Ancho y Nº Piezas.")
                return
            cantidad = self.largo.value() * self.ancho.value() * self.piezas.value()
            unidad = "m²"

        data = {
            "id": None,
            "sku": sku,
            "name": tipo,
            "product_type": tipo,
            "quantity": cantidad,
            "unit": unidad,
            "largo": self.largo.value(),
            "ancho": self.ancho.value(),
            "espesor": self.espesor.value(),
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
        self._clear_form()

    def _clear_form(self):
        """Resetea el formulario para registrar un nuevo producto."""
        self.product_type.setCurrentIndex(0)
        self.sku.clear()
        self.largo.setValue(0)
        self.ancho.setValue(0)
        self.espesor.setValue(0)
        self.piezas.setValue(0)
        self.quality.setCurrentIndex(0)
        self.drying.setCurrentIndex(0)
        self.planing.setCurrentIndex(0)
        self.impregnated.setCurrentIndex(0)
        self.obs.clear()
        self.form_container.setVisible(False)

    def _generate_sku(self, base: str) -> str:
        base_clean = "".join(ch for ch in base.upper() if ch.isalnum())[:10]
        ts = QtCore.QDateTime.currentDateTime().toString("yyMMddhhmmss")
        return f"{base_clean}-{ts}"