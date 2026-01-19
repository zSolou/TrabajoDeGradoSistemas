from PySide6 import QtCore, QtWidgets
from decimal import Decimal
import csv
import core.repo as repo

class InventarioScreen(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.on_create = None
        self.on_update = None
        self.on_delete = None
        self._all_rows = []
        self._build_ui()
        self.btn_delete = QtWidgets.QPushButton("Eliminar")
        self._connect_signals()
        self.btn_delete.clicked.connect(self._on_delete)
        
    def _build_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(8)

        title = QtWidgets.QLabel("INVENTARIO")
        title.setStyleSheet("font-size: 16pt; font-weight:600; color: #32D424;")
        v.addWidget(title)

        # Toolbar búsqueda
        toolbar = QtWidgets.QWidget()
        th = QtWidgets.QHBoxLayout(toolbar)
        th.setContentsMargins(0, 0, 0, 0)
        th.setSpacing(8)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Buscar por SKU o tipo...")
        self.btn_search_clear = QtWidgets.QToolButton()
        self.btn_search_clear.setText("X")

        th.addWidget(self.search_input)
        th.addWidget(self.btn_search_clear)
        v.addWidget(toolbar)

        # Tabla
        headers = [
            "ID", "SKU", "Tipo", "Cantidad", "Unidad",
            "Largo(m)", "Ancho(cm)", "Espesor(cm)", "Piezas",
            "Producción", "Despacho",
            "Calidad", "Secado", "Cepillado", "Impregnado", "Obs"
        ]
        self.table = QtWidgets.QTableWidget(0, len(headers))
        self.table.horizontalHeader().setStyleSheet("color: #e6eef8; background: #0b1220;")
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setColumnHidden(0, True)  # ocultar ID
        v.addWidget(self.table, 1)

        # Botones
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Actualizar")
        self.btn_export = QtWidgets.QPushButton("Exportar CSV")
        for b in (self.btn_refresh, self.btn_export):
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        v.addLayout(btn_row)

        self.info_lbl = QtWidgets.QLabel("")
        self.info_lbl.setStyleSheet("color:#94a3b8;")
        v.addWidget(self.info_lbl)
        
    def _on_delete(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Eliminar", "Seleccione un registro para eliminar.")
            return

        row = sel[0].row()
        current_id = self.table.item(row, 0).text()

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Está seguro de eliminar este producto del inventario?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        try:
            if self.on_delete:
                self.on_delete(int(current_id))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error BD", f"No se pudo eliminar: {e}")
            return

        # Eliminar de la lista local
        self._all_rows = [r for r in self._all_rows if str(r[0]) != current_id]
        self._refresh_table()
        self._update_info()
        QtWidgets.QMessageBox.information(self, "Eliminado", "Producto eliminado correctamente.")
    
    def _connect_signals(self):
        self.search_input.textChanged.connect(self._apply_filter)
        self.btn_search_clear.clicked.connect(self._clear_search)
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_export.clicked.connect(self._on_export)
        self.table.itemDoubleClicked.connect(self._on_double_click)

    # -------------------------
    # Integración con BD
    # -------------------------
    def refresh_from_db(self, repo):
        try:
            rows = repo.list_inventory_rows()
            self.load_data(rows)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error BD", f"No se pudo cargar inventario: {e}")

    # -------------------------
    # API pública
    # -------------------------
    def load_data(self, rows):
        self._all_rows = []
        for r in rows:
            row = (
                r.get("id"),
                r.get("sku", ""),
                r.get("product_type", ""),
                Decimal(r.get("quantity") or 0),
                r.get("unit", ""),
                Decimal(r.get("largo") or 0),
                Decimal(r.get("ancho") or 0),
                Decimal(r.get("espesor") or 0),
                int(r.get("piezas") or 0),
                r.get("prod_date", ""),
                r.get("dispatch_date", ""),
                r.get("quality", ""),
                r.get("drying", ""),
                r.get("planing", ""),
                r.get("impregnated", ""),
                r.get("obs", "")
            )
            self._all_rows.append(row)
        self._refresh_table()
        self._update_info()

    def add_row_from_registrar(self, data: dict):
        try:
            new_id = self.on_create(data) if self.on_create else None
            if new_id:
                data["id"] = new_id
            row = (
                data.get("id"),
                data.get("sku", ""),
                data.get("product_type", ""),
                Decimal(data.get("quantity") or 0),
                data.get("unit", ""),
                Decimal(data.get("largo") or 0),
                Decimal(data.get("ancho") or 0),
                Decimal(data.get("espesor") or 0),
                int(data.get("piezas") or 0),
                data.get("prod_date", ""),
                data.get("dispatch_date", ""),
                data.get("quality", ""),
                data.get("drying", ""),
                data.get("planing", ""),
                data.get("impregnated", ""),
                data.get("obs", "")
            )
            self._all_rows.append(row)
            self._insert_table_row(row)
            self._update_info()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error BD", f"No se pudo guardar: {e}")


    # -------------------------
    # UI helpers
    # -------------------------
    def _refresh_table(self):
        self.table.setRowCount(0)
        for row in self._all_rows:
            self._insert_table_row(row)
        self._apply_filter()

    def _insert_table_row(self, row):
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, val in enumerate(row):
            if isinstance(val, Decimal):
                item = QtWidgets.QTableWidgetItem(f"{val:.2f}")
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif isinstance(val, int):
                item = QtWidgets.QTableWidgetItem(str(val))
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            else:
                item = QtWidgets.QTableWidgetItem("" if val is None else str(val))
            self.table.setItem(r, c, item)

    def _apply_filter(self):
        text = self.search_input.text().strip().lower()
        for r in range(self.table.rowCount()):
            sku = self.table.item(r, 1).text().lower() if self.table.item(r, 1) else ""
            tipo = self.table.item(r, 2).text().lower() if self.table.item(r, 2) else ""
            visible = (text in sku) or (text in tipo) or (text == "")
            self.table.setRowHidden(r, not visible)
        self._update_info()

    def _clear_search(self):
        self.search_input.clear()

    def _update_info(self):
        total_rows = len(self._all_rows)
        visible = sum(0 if self.table.isRowHidden(r) else 1 for r in range(self.table.rowCount()))
        self.info_lbl.setText(f"Registros: {visible} / {total_rows}")

    def _on_refresh(self):
        self._refresh_table()

    def _on_export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Exportar CSV", "inventario.csv", "CSV Files (*.csv)")
        if not path:
            return
        headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount()) if not self.table.isColumnHidden(c)]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for r in range(self.table.rowCount()):
                if self.table.isRowHidden(r):
                    continue
                row_vals = []
                for c in range(self.table.columnCount()):
                    if self.table.isColumnHidden(c):
                        continue
                    item = self.table.item(r, c)
                    row_vals.append(item.text() if item else "")
                writer.writerow(row_vals)
        QtWidgets.QMessageBox.information(self, "Exportado", f"CSV exportado a: {path}")

    def _on_double_click(self, item):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        row = sel[0].row()
        current_id = self.table.item(row, 0).text()
        current = next((r for r in self._all_rows if str(r[0]) == current_id), None)
        if not current:
            return

        # Construir diccionario con los datos actuales
        data = {
            "id": current[0],
            "sku": current[1],
            "product_type": current[2],
            "quantity": float(current[3]),
            "unit": current[4],
            "largo": float(current[5]),
            "ancho": float(current[6]),
            "espesor": float(current[7]),
            "piezas": int(current[8]),
            "prod_date": current[9],
            "dispatch_date": current[10],
            "quality": current[11],
            "drying": current[12],
            "planing": current[13],
            "impregnated": current[14],
            "obs": current[15]
        }

        # Abrir diálogo de edición
        dlg = InventarioDialog(self, data)
        result = dlg.exec()

        if result == QtWidgets.QDialog.Accepted:
            # 🔹 Actualizar
            new = dlg.get_data()
            new["id"] = data["id"]
            try:
                if self.on_update:
                    self.on_update(new)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error BD", f"No se pudo actualizar: {e}")
                return
            # Refrescar desde BD para ver datos reales
            try:
                self.refresh_from_db(repo)
            except Exception:
                self._refresh_table()

        elif result == 99:  # 🔹 nuestro código especial para "Eliminar"
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setWindowTitle("Confirmar eliminación")
            msg.setText("¿Eliminar definitivamente este registro?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.button(QtWidgets.QMessageBox.Yes).setText("Sí")
            msg.button(QtWidgets.QMessageBox.No).setText("No")

            confirm = msg.exec()
            if confirm == QtWidgets.QMessageBox.Yes:
                try:
                    if self.on_delete:
                        self.on_delete(int(data["id"]))
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error BD", f"No se pudo eliminar: {e}")
                    return
                # Eliminar de la lista local
                self._all_rows = [r for r in self._all_rows if r[0] != data["id"]]
                self._refresh_table()
                self._update_info()
                QtWidgets.QMessageBox.information(self, "Eliminado", "Registro eliminado correctamente.")
        
class InventarioDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Editar registro de inventario")
        self.setModal(True)
        self._build_ui()
        if data:
            self._set_data(data)

    def _build_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        # Campos principales
        self.input_sku = QtWidgets.QLineEdit()
        self.input_type = QtWidgets.QComboBox()
        self.input_type.addItems(["Tablas", "Machihembrado", "Aserrín"])
        self.input_quantity = QtWidgets.QDoubleSpinBox(); self.input_quantity.setDecimals(2); self.input_quantity.setRange(0, 1_000_000)
        self.input_unit = QtWidgets.QLineEdit()

        # Medidas
        self.input_largo = QtWidgets.QDoubleSpinBox(); self.input_largo.setDecimals(2); self.input_largo.setRange(0, 1000)
        self.input_ancho = QtWidgets.QDoubleSpinBox(); self.input_ancho.setDecimals(2); self.input_ancho.setRange(0, 1000)
        self.input_espesor = QtWidgets.QDoubleSpinBox(); self.input_espesor.setDecimals(2); self.input_espesor.setRange(0, 1000)
        self.input_piezas = QtWidgets.QSpinBox(); self.input_piezas.setRange(0, 1_000_000)

        # Fechas
        self.input_prod_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.input_dispatch_date = QtWidgets.QDateEdit(calendarPopup=True)

        # Otros atributos
        self.input_quality = QtWidgets.QComboBox(); self.input_quality.addItems(["Tipo 1","Tipo 2","Tipo 3","Tipo 4"])
        self.input_drying = QtWidgets.QComboBox(); self.input_drying.addItems(["Sí","No"])
        self.input_planing = QtWidgets.QComboBox(); self.input_planing.addItems(["Sí","No"])
        self.input_impregnated = QtWidgets.QComboBox(); self.input_impregnated.addItems(["Sí","No"])
        self.input_obs = QtWidgets.QPlainTextEdit(); self.input_obs.setFixedHeight(80)

        # Añadir al formulario
        form.addRow("SKU", self.input_sku)
        form.addRow("Tipo", self.input_type)
        form.addRow("Cantidad", self.input_quantity)
        form.addRow("Unidad", self.input_unit)
        form.addRow("Largo", self.input_largo)
        form.addRow("Ancho", self.input_ancho)
        form.addRow("Espesor", self.input_espesor)
        form.addRow("Piezas", self.input_piezas)
        form.addRow("Producción", self.input_prod_date)
        form.addRow("Despacho", self.input_dispatch_date)
        form.addRow("Calidad", self.input_quality)
        form.addRow("Secado", self.input_drying)
        form.addRow("Cepillado", self.input_planing)
        form.addRow("Impregnado", self.input_impregnated)
        form.addRow("Observación", self.input_obs)

        v.addLayout(form)

        # Botones aceptar/cancelar
        btns = QtWidgets.QDialogButtonBox(
    QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btns.button(QtWidgets.QDialogButtonBox.Cancel).setText("Cancelar")

        # Crear botón eliminar
        self.btn_delete = btns.addButton("Eliminar", QtWidgets.QDialogButtonBox.DestructiveRole)
        self.btn_delete.clicked.connect(self._on_delete)

        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)
        
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    def _set_data(self, data):
        self.input_sku.setText(data.get("sku", ""))
        self.input_type.setCurrentText(data.get("product_type", ""))
        self.input_quantity.setValue(float(data.get("quantity") or 0))
        self.input_unit.setText(data.get("unit", ""))

        self.input_largo.setValue(float(data.get("largo") or 0))
        self.input_ancho.setValue(float(data.get("ancho") or 0))
        self.input_espesor.setValue(float(data.get("espesor") or 0))
        self.input_piezas.setValue(int(data.get("piezas") or 0))

        def set_qdate(widget, s):
            if not s:
                return
            qd = QtCore.QDate.fromString(s, QtCore.Qt.ISODate)
            if qd.isValid():
                widget.setDate(qd)

        set_qdate(self.input_prod_date, data.get("prod_date", ""))
        set_qdate(self.input_dispatch_date, data.get("dispatch_date", ""))

        self.input_quality.setCurrentText(data.get("quality", ""))
        self.input_drying.setCurrentText(data.get("drying", ""))
        self.input_planing.setCurrentText(data.get("planing", ""))
        self.input_impregnated.setCurrentText(data.get("impregnated", ""))
        self.input_obs.setPlainText(data.get("obs", ""))

    def _on_accept(self):
        if not self.input_sku.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validación", "SKU es obligatorio.")
            return
        self.accept()
        
    def _on_delete(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText("¿Está seguro de eliminar este registro de inventario?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        # Cambiar textos de los botones
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sí")
        msg.button(QtWidgets.QMessageBox.No).setText("No")

        result = msg.exec()
        if result == QtWidgets.QMessageBox.Yes:
            # devolvemos un código especial para que InventarioScreen sepa que fue "Eliminar"
            self.done(99)
        
    def get_data(self):
        return {
            "sku": self.input_sku.text().strip(),
            "product_type": self.input_type.currentText(),
            "quantity": float(self.input_quantity.value()),
            "unit": self.input_unit.text().strip(),

            # Medidas individuales
            "largo": float(self.input_largo.value()),
            "ancho": float(self.input_ancho.value()),
            "espesor": float(self.input_espesor.value()),
            "piezas": int(self.input_piezas.value()),

            # Fechas
            "prod_date": self.input_prod_date.date().toString(QtCore.Qt.ISODate),
            "dispatch_date": self.input_dispatch_date.date().toString(QtCore.Qt.ISODate),

            # Otros atributos
            "quality": self.input_quality.currentText(),
            "drying": self.input_drying.currentText(),
            "planing": self.input_planing.currentText(),
            "impregnated": self.input_impregnated.currentText(),
            "obs": self.input_obs.toPlainText()
        }