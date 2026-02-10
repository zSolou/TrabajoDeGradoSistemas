import random
from PySide6 import QtCore, QtWidgets, QtGui
from core import theme, repo

FACTORES_CONVERSION = { "Tablas": 30, "Tablones": 20, "Paletas": 10, "Machihembrado": 5 }

class MedidasManagerDialog(QtWidgets.QDialog):
    measure_selected = QtCore.Signal(dict) 
    def __init__(self, product_type, parent=None):
        super().__init__(parent); self.product_type = product_type
        self.setWindowTitle(f"Medidas: {product_type}"); self.resize(500, 450)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY};")
        self._build_ui(); self._load_measures()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px; padding: 5px;")
        self.list_widget.itemDoubleClicked.connect(self._usar_medida)
        layout.addWidget(QtWidgets.QLabel("Selecciona una medida:"))
        layout.addWidget(self.list_widget)

        new_frame = QtWidgets.QFrame()
        new_frame.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-top: 1px solid {theme.BORDER_COLOR}; margin-top: 10px;")
        form = QtWidgets.QHBoxLayout(new_frame); form.setContentsMargins(0, 15, 0, 0)
        
        self.inp_name = QtWidgets.QLineEdit(); self.inp_name.setPlaceholderText("Nombre")
        self.inp_l = QtWidgets.QDoubleSpinBox(); self.inp_l.setSuffix(" m"); self.inp_l.setRange(0, 10)
        self.inp_a = QtWidgets.QDoubleSpinBox(); self.inp_a.setSuffix(" cm"); self.inp_a.setRange(0, 100)
        self.inp_e = QtWidgets.QDoubleSpinBox(); self.inp_e.setSuffix(" cm"); self.inp_e.setRange(0, 100)
        for w in [self.inp_name, self.inp_l, self.inp_a, self.inp_e]: w.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 4px;")
        if self.product_type == "Machihembrado": self.inp_e.setVisible(False)

        btn_add = QtWidgets.QPushButton("+"); btn_add.clicked.connect(self._agregar_medida)
        btn_add.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold;")
        
        form.addWidget(self.inp_name); form.addWidget(self.inp_l); form.addWidget(self.inp_a)
        if self.product_type != "Machihembrado": form.addWidget(self.inp_e)
        form.addWidget(btn_add)
        layout.addWidget(new_frame)

        h = QtWidgets.QHBoxLayout()
        btn_del = QtWidgets.QPushButton("Desactivar"); btn_del.clicked.connect(self._eliminar_medida)
        btn_del.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; padding: 8px;")
        btn_use = QtWidgets.QPushButton("✅ Usar"); btn_use.clicked.connect(lambda: self._usar_medida(self.list_widget.currentItem()))
        btn_use.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; padding: 8px;")
        h.addWidget(btn_del); h.addStretch(); h.addWidget(btn_use)
        layout.addLayout(h)

    def _load_measures(self):
        self.list_widget.clear()
        for m in repo.get_measures_by_type(self.product_type):
            lbl = f"{m.name} | {m.largo}m x {m.ancho}cm" + (f" x {m.espesor}cm" if m.espesor else "")
            it = QtWidgets.QListWidgetItem(lbl); it.setData(QtCore.Qt.UserRole, m)
            self.list_widget.addItem(it)

    def _agregar_medida(self):
        if self.inp_l.value()==0: return
        repo.create_measure({"product_type":self.product_type,"name":self.inp_name.text() or "Standard","largo":self.inp_l.value(),"ancho":self.inp_a.value(),"espesor":self.inp_e.value()})
        self._load_measures(); self.inp_name.clear()

    def _eliminar_medida(self):
        it = self.list_widget.currentItem()
        if it: 
            if QtWidgets.QMessageBox.question(self, "Confimar", "Desactivar?") == QtWidgets.QMessageBox.Yes:
                repo.delete_measure(it.data(QtCore.Qt.UserRole).id); self._load_measures()

    def _usar_medida(self, it):
        if it: 
            m = it.data(QtCore.Qt.UserRole)
            self.measure_selected.emit({"largo":m.largo,"ancho":m.ancho,"espesor":m.espesor})
            self.accept()

class RegistrarForm(QtWidgets.QWidget):
    saved_signal = QtCore.Signal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_saving = False
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self); main.setContentsMargins(12, 20, 12, 12)
        
        lbl = QtWidgets.QLabel("REGISTRAR PRODUCTO"); lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet(f"font-weight: bold; font-size: 20pt; color: {theme.ACCENT_COLOR};")
        main.addWidget(lbl)

        self.btn_measures = QtWidgets.QPushButton("⭐ Cargar Medidas"); self.btn_measures.setVisible(False)
        self.btn_measures.clicked.connect(self._open_measures_dialog)
        self.btn_measures.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold; padding: 6px;")
        main.addWidget(self.btn_measures)

        self.product_type = QtWidgets.QComboBox()
        self.product_type.addItems(["-- Seleccione --", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        self.product_type.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 8px;")
        self.product_type.currentTextChanged.connect(self._on_change); main.addWidget(self.product_type)

        self.form = QtWidgets.QWidget(); self.fl = QtWidgets.QFormLayout(self.form); self.fl.setSpacing(12)
        
        self.nro_lote = QtWidgets.QLineEdit()
        self.nro_lote.setPlaceholderText("Ej: 101")
        self.nro_lote.setValidator(QtGui.QRegularExpressionValidator(QtCore.QRegularExpression("^[0-9]{1,3}$")))
        self.nro_lote.setStyleSheet(f"background-color: {theme.BG_INPUT}; padding: 5px;")

        self.date = QtWidgets.QDateEdit(QtCore.QDate.currentDate()); self.date.setCalendarPopup(True)
        self.date.setStyleSheet(f"background-color: {theme.BG_INPUT};")

        self.largo = self._sb("m", locked=True); self.ancho = self._sb("cm", locked=True); self.espesor = self._sb("cm", locked=True)
        self.piezas = self._sb(" Bultos", 1000000); self.piezas.setReadOnly(False); self.piezas.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
        
        self.quality = self._cb(["Tipo 1", "Tipo 2", "Tipo 3"]); self.drying = self._cb(["Sí", "No"])
        self.planing = self._cb(["Sí", "No"]); self.impregnated = self._cb(["Sí", "No"])
        self.obs = QtWidgets.QPlainTextEdit(); self.obs.setFixedHeight(60)
        self.obs.setStyleSheet(f"background-color: {theme.BG_INPUT};")

        self.rows = {}
        self.rows['lote'] = self._row("Nro. Lote:", self.nro_lote)
        self.rows['date'] = self._row("Fecha:", self.date)
        self.rows['l'] = self._row("Largo:", self.largo)
        self.rows['a'] = self._row("Ancho:", self.ancho)
        self.rows['e'] = self._row("Espesor:", self.espesor)
        self.rows['p'] = self._row("Bultos:", self.piezas)
        self.rows['q'] = self._row("Calidad:", self.quality)
        self.rows['d'] = self._row("Secado:", self.drying)
        self.rows['pl'] = self._row("Cepillado:", self.planing)
        self.rows['i'] = self._row("Impregnado:", self.impregnated)
        self.rows['o'] = self._row("Obs:", self.obs)
        
        self.form.setVisible(False); main.addWidget(self.form)

        self.btn_save = QtWidgets.QPushButton("Guardar Producto")
        self.btn_save.setMinimumHeight(45); self.btn_save.clicked.connect(self._save)
        self.btn_save.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; font-weight: bold; font-size: 11pt;")
        main.addWidget(self.btn_save)

    def eventFilter(self, s, e):
        if e.type() == QtCore.QEvent.MouseButtonRelease and s in (self.largo, self.ancho, self.espesor):
            self._open_measures_dialog(); return True
        return super().eventFilter(s, e)

    def _sb(self, suf, maxv=1000, locked=False):
        sb = QtWidgets.QDoubleSpinBox() if maxv==1000 else QtWidgets.QSpinBox()
        sb.setRange(0, maxv); sb.setSuffix(suf)
        if locked: 
            sb.setReadOnly(True); sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            sb.setCursor(QtCore.Qt.PointingHandCursor); sb.installEventFilter(self)
            sb.setStyleSheet(f"background-color: #2b3553; color: gray;")
        else: sb.setStyleSheet(f"background-color: {theme.BG_INPUT};")
        return sb

    def _cb(self, items):
        c = QtWidgets.QComboBox(); c.addItems(items); c.setStyleSheet(f"background-color: {theme.BG_INPUT};")
        return c

    def _row(self, txt, w):
        c = QtWidgets.QWidget(); l = QtWidgets.QHBoxLayout(c); l.setContentsMargins(0,0,0,0)
        l.addWidget(QtWidgets.QLabel(txt)); l.addWidget(w); self.fl.addRow(c); return c

    def _on_change(self, t):
        if t.startswith("--"): self.form.setVisible(False); self.btn_measures.setVisible(False); return
        self.form.setVisible(True); self.btn_measures.setVisible(True); self.btn_measures.setText(f"⭐ Medidas {t}")
        v = ["lote", "date", "q", "d", "pl", "i", "o", "l", "a", "p"]
        if t != "Machihembrado": v.append("e")
        for k, w in self.rows.items(): w.setVisible(k in v)

    def _open_measures_dialog(self):
        d = MedidasManagerDialog(self.product_type.currentText(), self)
        d.measure_selected.connect(lambda x: (self.largo.setValue(x["largo"]), self.ancho.setValue(x["ancho"]), self.espesor.setValue(x["espesor"])))
        d.exec_()

    # --- ESTA FUNCION ESTÁ DENTRO DE LA CLASE AHORA ---
    def _validate_input(self, t):
        if self.piezas.value() <= 0: QtWidgets.QMessageBox.warning(self, "Error", "Faltan Bultos"); return False
        if not self.nro_lote.text().strip(): QtWidgets.QMessageBox.warning(self, "Error", "Falta Lote"); return False
        if t!="Machihembrado" and self.espesor.value()<=0: QtWidgets.QMessageBox.warning(self, "Error", "Falta Espesor"); return False
        return True

    def _save(self):
        t = self.product_type.currentText()
        if t.startswith("--"): return
        if not self._validate_input(t): return

        factor = FACTORES_CONVERSION.get(t, 1)
        total = self.piezas.value() * factor

        # --- MENSAJE DE CONFIRMACIÓN DETALLADO ---
        mensaje = (
            f"¿Confirmar registro?\n\n"
            f"📦 Producto: {t}\n"
            f"🏷️ Lote: {self.nro_lote.text()}\n"
            f"📅 Fecha Prod: {self.date.date().toString('dd/MM/yyyy')}\n"
            f"📊 Cantidad: {self.piezas.value()} Bultos\n"
            f"(Total piezas: {total:.0f})"
        )

        if QtWidgets.QMessageBox.question(self, "Confirmar Registro", mensaje, 
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No: 
            return
        # -----------------------------------------

        # BLOQUEO BOTÓN
        self.btn_save.setEnabled(False); self.btn_save.setText("Guardando...")
        QtWidgets.QApplication.processEvents()

        try:
            data = {
                "sku": f"{t[:3].upper()}-{random.randint(10000,99999)}",
                "nro_lote": self.nro_lote.text().strip(),
                "name": t, "product_type": t,
                "quantity": total, "unit": "pzas",
                "largo": self.largo.value(), "ancho": self.ancho.value(),
                "espesor": self.espesor.value() if t!="Machihembrado" else 0,
                "piezas": total,
                "prod_date": self.date.date().toString("yyyy-MM-dd"),
                "quality": self.quality.currentText(), "drying": self.drying.currentText(),
                "planing": self.planing.currentText(), "impregnated": self.impregnated.currentText(),
                "obs": self.obs.toPlainText()
            }
            repo.create_product_with_inventory(data)
            self.saved_signal.emit(data)
            QtWidgets.QMessageBox.information(self, "Éxito", "Registrado correctamente.")
            self.nro_lote.clear(); self.piezas.setValue(0); self.obs.clear()
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
        
        finally:
            self.btn_save.setEnabled(True); self.btn_save.setText("Guardar Producto")