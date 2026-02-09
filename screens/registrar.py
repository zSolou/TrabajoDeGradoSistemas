from PySide6 import QtCore, QtWidgets, QtGui
from core import theme, repo

# Factores de conversión
FACTORES_CONVERSION = {
    "Tablas": 30,
    "Tablones": 20,
    "Paletas": 10,
    "Machihembrado": 5
}

class MedidasManagerDialog(QtWidgets.QDialog):
    """Ventana para gestionar y seleccionar medidas favoritas"""
    measure_selected = QtCore.Signal(dict) 

    def __init__(self, product_type, parent=None):
        super().__init__(parent)
        self.product_type = product_type
        self.setWindowTitle(f"Medidas: {product_type}")
        self.resize(500, 450)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY};")
        self._build_ui()
        self._load_measures()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Lista
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px; padding: 5px; }}
            QListWidget::item {{ padding: 8px; border-bottom: 1px solid #444; }}
            QListWidget::item:selected {{ background-color: {theme.BTN_PRIMARY}; color: white; }}
        """)
        self.list_widget.itemDoubleClicked.connect(self._usar_medida)
        layout.addWidget(QtWidgets.QLabel("Selecciona una medida:"))
        layout.addWidget(self.list_widget)

        # Formulario Nueva Medida
        new_frame = QtWidgets.QFrame()
        new_frame.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-top: 1px solid {theme.BORDER_COLOR}; margin-top: 10px;")
        form_layout = QtWidgets.QHBoxLayout(new_frame)
        form_layout.setContentsMargins(0, 15, 0, 0)
        
        self.inp_name = QtWidgets.QLineEdit(); self.inp_name.setPlaceholderText("Nombre (Ej: Estándar)")
        self.inp_name.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        
        self.inp_l = QtWidgets.QDoubleSpinBox(); self.inp_l.setSuffix(" m"); self.inp_l.setRange(0, 10); self.inp_l.setValue(0)
        self.inp_l.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        
        self.inp_a = QtWidgets.QDoubleSpinBox(); self.inp_a.setSuffix(" cm"); self.inp_a.setRange(0, 100); self.inp_a.setValue(0)
        self.inp_a.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        
        self.inp_e = QtWidgets.QDoubleSpinBox(); self.inp_e.setSuffix(" cm"); self.inp_e.setRange(0, 100); self.inp_e.setValue(0)
        self.inp_e.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 4px;")
        
        if self.product_type == "Machihembrado":
            self.inp_e.setVisible(False)

        btn_add = QtWidgets.QPushButton("+")
        btn_add.setCursor(QtCore.Qt.PointingHandCursor)
        btn_add.setToolTip("Guardar nueva medida")
        btn_add.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; padding: 5px 15px; border-radius: 4px; font-size: 14pt;")
        btn_add.clicked.connect(self._agregar_medida)

        form_layout.addWidget(self.inp_name)
        form_layout.addWidget(self.inp_l)
        form_layout.addWidget(self.inp_a)
        if self.product_type != "Machihembrado":
            form_layout.addWidget(self.inp_e)
        form_layout.addWidget(btn_add)
        
        layout.addWidget(new_frame)

        # --- BOTONES DE ACCIÓN (Restaurados) ---
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.btn_del = QtWidgets.QPushButton("Desactivar Seleccionada") # Cambiado texto
        self.btn_del.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_del.setStyleSheet(f"background-color: {theme.BTN_DANGER}; padding: 8px; border-radius: 4px; color: white;")
        self.btn_del.clicked.connect(self._eliminar_medida)
        
        self.btn_use = QtWidgets.QPushButton("✅ Usar Medida") # BOTÓN RESTAURADO
        self.btn_use.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_use.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; padding: 8px; font-weight: bold; border-radius: 4px; color: white; font-size: 11pt;")
        self.btn_use.clicked.connect(lambda: self._usar_medida(self.list_widget.currentItem()))

        btn_layout.addWidget(self.btn_del)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_use)
        layout.addLayout(btn_layout)

    def _load_measures(self):
        self.list_widget.clear()
        measures = repo.get_measures_by_type(self.product_type)
        for m in measures:
            label = f"{m.name or 'Sin Nombre'} | {m.largo}m x {m.ancho}cm"
            if m.espesor and m.espesor > 0:
                label += f" x {m.espesor}cm"
            
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, m) 
            self.list_widget.addItem(item)

    def _agregar_medida(self):
        name = self.inp_name.text().strip() or "Medida Personalizada"
        if self.inp_l.value() == 0 or self.inp_a.value() == 0:
             QtWidgets.QMessageBox.warning(self, "Error", "Largo y Ancho son obligatorios.")
             return

        data = {
            "product_type": self.product_type,
            "name": name,
            "largo": self.inp_l.value(),
            "ancho": self.inp_a.value(),
            "espesor": self.inp_e.value()
        }
        repo.create_measure(data)
        self._load_measures()
        self.inp_name.clear()

    def _eliminar_medida(self):
        item = self.list_widget.currentItem()
        if not item: return
        m = item.data(QtCore.Qt.UserRole)
        
        # Confirmación de desactivación
        if QtWidgets.QMessageBox.question(self, "Desactivar", f"¿Ocultar la medida '{m.name}'?", 
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            
            repo.delete_measure(m.id) # Ahora esto solo desactiva
            self._load_measures()

    def _usar_medida(self, item):
        if not item: return
        m = item.data(QtCore.Qt.UserRole)
        self.measure_selected.emit({
            "largo": m.largo,
            "ancho": m.ancho,
            "espesor": m.espesor
        })
        self.accept()


class RegistrarForm(QtWidgets.QWidget):
    saved_signal = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(12, 20, 12, 12)
        main.setSpacing(10)

        # Header
        header_widget = QtWidgets.QWidget()
        self.header_layout = QtWidgets.QVBoxLayout(header_widget)
        self.header_layout.setContentsMargins(0,0,0,0)
        self.header_layout.setSpacing(15)

        self.title = QtWidgets.QLabel("REGISTRAR PRODUCTO")
        self.title.setStyleSheet(f"font-weight: bold; font-size: 20pt; color: {theme.ACCENT_COLOR};")
        self.title.setAlignment(QtCore.Qt.AlignCenter) 
        self.header_layout.addWidget(self.title)

        # Botón Acceso Directo a Medidas
        self.btn_measures = QtWidgets.QPushButton("⭐ Cargar Lista de Medidas")
        self.btn_measures.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_measures.setVisible(False) 
        self.btn_measures.setStyleSheet(f"""
            QPushButton {{ background-color: #ffc107; color: black; font-weight: bold; border-radius: 4px; padding: 6px; }}
            QPushButton:hover {{ background-color: #ffca2c; }}
        """)
        self.btn_measures.clicked.connect(self._open_measures_dialog)
        self.header_layout.addWidget(self.btn_measures)

        self.product_type = QtWidgets.QComboBox()
        self.product_type.setMinimumWidth(200)
        self.product_type.addItems(["-- Seleccione Producto --", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        self.product_type.setStyleSheet(f"""
            QComboBox {{ background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 8px; border-radius: 4px; font-size: 11pt; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.header_layout.addWidget(self.product_type)
        
        main.addWidget(header_widget)

        # Formulario
        self.form_container = QtWidgets.QWidget()
        form_layout = QtWidgets.QFormLayout(self.form_container)
        form_layout.setSpacing(12)

        self.sku = QtWidgets.QLineEdit()
        self.sku.setVisible(False)

        self.nro_lote = QtWidgets.QLineEdit()
        self.nro_lote.setPlaceholderText("Ej: L-2026-A")
        self.nro_lote.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 5px; border-radius: 4px;")

        self.prod_date = self._create_date_edit()

        # Medidas (Bloqueadas y Clickables)
        self.largo = self._create_spinbox("m", 6.00) 
        self.ancho = self._create_spinbox("cm", 30.00)
        self.espesor = self._create_spinbox("cm", 30.00)
        
        # Cantidad en Bultos
        self.piezas = QtWidgets.QSpinBox()
        self.piezas.setRange(0, 1000000)
        self.piezas.setSuffix(" Bultos")
        self.piezas.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; padding: 4px; border-radius: 4px;")

        self.quality = self._create_combo(["Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4"])
        self.drying = self._create_combo(["Sí", "No"])
        self.planing = self._create_combo(["Sí", "No"])
        self.impregnated = self._create_combo(["Sí", "No"])
        
        self.obs = QtWidgets.QPlainTextEdit()
        self.obs.setFixedHeight(60)
        self.obs.setPlaceholderText("Observaciones opcionales...")
        self.obs.setStyleSheet(f"background-color: {theme.BG_INPUT}; color: white; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px;")

        self.rows = {}
        self.rows['nro_lote'] = self._add_row(form_layout, "Nro. Lote / Código:", self.nro_lote)
        self.rows['prod_date'] = self._add_row(form_layout, "Fecha Producción:", self.prod_date)
        self.rows['largo'] = self._add_row(form_layout, "Largo (Clic para medidas):", self.largo)
        self.rows['ancho'] = self._add_row(form_layout, "Ancho (Clic para medidas):", self.ancho)
        self.rows['espesor'] = self._add_row(form_layout, "Espesor (Clic para medidas):", self.espesor)
        self.rows['piezas'] = self._add_row(form_layout, "Cantidad (Bultos):", self.piezas)
        self.rows['quality'] = self._add_row(form_layout, "Calidad:", self.quality)
        self.rows['drying'] = self._add_row(form_layout, "Secado:", self.drying)
        self.rows['planing'] = self._add_row(form_layout, "Cepillado:", self.planing)
        self.rows['impregnated'] = self._add_row(form_layout, "Impregnado:", self.impregnated)
        self.rows['obs'] = self._add_row(form_layout, "Observación:", self.obs)

        self.form_container.setVisible(False)
        main.addWidget(self.form_container)

        # Botón Guardar
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QtWidgets.QPushButton("Guardar Producto")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setMinimumWidth(200)
        self.save_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_PRIMARY}; color: white; font-weight: bold; border-radius: 4px; font-size: 11pt; }}
            QPushButton:hover {{ background-color: #0b5ed7; }}
        """)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        main.addLayout(btn_layout)

        self.product_type.currentTextChanged.connect(self._on_product_change)

    def eventFilter(self, source, event):
        """Detecta clic en los campos de medidas bloqueados"""
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if source in (self.largo, self.ancho, self.espesor):
                if self.largo.isReadOnly():
                    self._open_measures_dialog()
                    return True
        return super().eventFilter(source, event)

    def _create_spinbox(self, suffix, max_val=1000.00):
        sb = QtWidgets.QDoubleSpinBox()
        sb.setRange(0.00, max_val)
        sb.setDecimals(2)
        sb.setSuffix(f" {suffix}")
        
        # Bloqueo para obligar a usar el selector
        sb.setReadOnly(True) 
        sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons) 
        sb.setCursor(QtCore.Qt.PointingHandCursor) 
        sb.installEventFilter(self) 

        sb.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {theme.BG_INPUT}; 
                color: white; 
                border: 1px solid {theme.BORDER_COLOR}; 
                padding: 4px; 
                border-radius: 4px;
            }}
            QDoubleSpinBox:read-only {{
                background-color: #2b3553; 
                color: #a9a9b3;
            }}
        """)
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
            self.btn_measures.setVisible(False)
            self.title.setAlignment(QtCore.Qt.AlignCenter)
            return
        
        self.form_container.setVisible(True)
        self.btn_measures.setVisible(True)
        self.btn_measures.setText(f"⭐ Ver Medidas para {text}")
        self.title.setAlignment(QtCore.Qt.AlignLeft)
        
        show_map = {
            "Tablas": ["largo", "ancho", "espesor", "piezas"],
            "Tablones": ["largo", "ancho", "espesor", "piezas"],
            "Paletas": ["largo", "ancho", "espesor", "piezas"],
            "Machihembrado": ["largo", "ancho", "piezas"]
        }
        
        commons = ["nro_lote", "prod_date", "quality", "drying", "planing", "impregnated", "obs"]
        
        for w in self.rows.values(): w.setVisible(False)
        targets = show_map.get(text, []) + commons
        for key in targets:
            if key in self.rows: self.rows[key].setVisible(True)

    def _open_measures_dialog(self):
        ptype = self.product_type.currentText()
        if ptype.startswith("--"): return
        dialog = MedidasManagerDialog(ptype, self)
        dialog.measure_selected.connect(self._apply_measure)
        dialog.exec_()

    def _apply_measure(self, data):
        if "largo" in data: self.largo.setValue(float(data["largo"]))
        if "ancho" in data: self.ancho.setValue(float(data["ancho"]))
        if "espesor" in data: self.espesor.setValue(float(data["espesor"]))
        QtWidgets.QMessageBox.information(self, "Medida Aplicada", "Se han cargado las dimensiones correctamente.")

    def _validate_input(self, tipo):
        if self.piezas.value() <= 0:
            QtWidgets.QMessageBox.warning(self, "Dato Faltante", "El número de **Bultos** no puede ser 0.")
            self.piezas.setFocus()
            return False
        
        if not self.nro_lote.text().strip():
            QtWidgets.QMessageBox.warning(self, "Falta Lote", "Debe ingresar un **Número de Lote**.")
            self.nro_lote.setFocus()
            return False

        if tipo in ("Tablas", "Tablones", "Paletas"):
            if self.largo.value() <= 0 or self.ancho.value() <= 0 or self.espesor.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medidas", "Haga clic en los campos de medida para seleccionar una válida.")
                return False
        elif tipo == "Machihembrado":
            if self.largo.value() <= 0 or self.ancho.value() <= 0:
                QtWidgets.QMessageBox.warning(self, "Medidas", "Haga clic en los campos de medida para seleccionar una válida.")
                return False
        return True

    def _on_save(self):
        tipo = self.product_type.currentText()
        if tipo.startswith("--"):
            QtWidgets.QMessageBox.warning(self, "Error", "Seleccione un tipo de producto.")
            return

        if not self._validate_input(tipo): return

        # Conversión
        factor = FACTORES_CONVERSION.get(tipo, 1)
        cant_bultos = self.piezas.value()
        total_piezas = cant_bultos * factor

        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmar Registro",
            f"Producto: {tipo}\nLote: {self.nro_lote.text()}\n"
            f"Entrada: {cant_bultos} Bultos\nTotal Real: {total_piezas} Piezas\n\n¿Es correcto?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if confirm == QtWidgets.QMessageBox.No: return

        sku = self._generate_sku(tipo)
        
        data = {
            "sku": sku,
            "nro_lote": self.nro_lote.text().strip(),
            "name": tipo,
            "product_type": tipo,
            "quantity": total_piezas,
            "unit": "pzas",
            "largo": self.largo.value(),
            "ancho": self.ancho.value(),
            "espesor": self.espesor.value() if tipo != "Machihembrado" else 0,
            "piezas": total_piezas,
            "prod_date": self.prod_date.date().toString("yyyy-MM-dd"),
            "quality": self.quality.currentText(),
            "drying": self.drying.currentText(),
            "planing": self.planing.currentText(),
            "impregnated": self.impregnated.currentText(),
            "obs": self.obs.toPlainText() + f"\n(Original: {cant_bultos} Bultos)"
        }

        try:
            repo.create_product_with_inventory(data) # GUARDAR EN DB
            self.saved_signal.emit(data)
            QtWidgets.QMessageBox.information(self, "Éxito", f"Registrado: {total_piezas} piezas en inventario.")
            self._clear_form()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")

    def _clear_form(self):
        self.nro_lote.clear()
        self.largo.setValue(0); self.ancho.setValue(0); self.espesor.setValue(0); self.piezas.setValue(0)
        self.obs.clear()
        self.prod_date.setDate(QtCore.QDate.currentDate())

    def _generate_sku(self, base: str) -> str:
        base_clean = "".join(ch for ch in base.upper() if ch.isalnum())[:3]
        ts = QtCore.QDateTime.currentDateTime().toString("ddHHmmss")
        return f"{base_clean}-{ts}"