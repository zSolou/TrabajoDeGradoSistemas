# screens/clientes.py
from PySide6 import QtCore, QtWidgets, QtGui
import core.repo as repo


class ClientesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._clientes = []  # lista de dicts con datos + id
        self._build_ui()
        self.refresh_from_db()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("CLIENTES")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight:600;")
        layout.addWidget(title)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_nuevo = QtWidgets.QPushButton("Nuevo cliente")
        self.btn_editar = QtWidgets.QPushButton("Editar seleccionado")
        self.btn_eliminar = QtWidgets.QPushButton("Eliminar seleccionado")
        btn_row.addWidget(self.btn_nuevo)
        btn_row.addWidget(self.btn_editar)
        btn_row.addWidget(self.btn_eliminar)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Nombre", "Teléfono", "Dirección", "Email", "Cédula/RIF"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.btn_nuevo.clicked.connect(self._on_nuevo)
        self.btn_editar.clicked.connect(self._on_editar)
        self.btn_eliminar.clicked.connect(self._on_eliminar)
        self.table.itemDoubleClicked.connect(self._on_double_click)

    def refresh_from_db(self):
        self.table.setRowCount(0)
        self._clientes = []
        for c in repo.list_clients():
            data = {
                "id": c.id,
                "nombre": c.name,
                "telefono": c.phone or "",
                "direccion": c.address or "",
                "email": c.email or "",
                "cedula_rif": c.document_id or ""
            }
            self._clientes.append(data)
            self._add_row(data)

    def _add_row(self, data):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(data.get("nombre", "")))
        self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(data.get("telefono", "")))
        self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(data.get("direccion", "")))
        self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(data.get("email", "")))
        self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(data.get("cedula_rif", "")))

    def _get_selected_index(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QtWidgets.QMessageBox.information(self, "Seleccionar", "Por favor seleccione una fila primero.")
            return None
        return sel[0].row()

    def _on_nuevo(self):
        dlg = ClienteDialog(parent=self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            data = dlg.get_data()
            new_id = repo.create_client(data)
            data["id"] = new_id
            self._clientes.append(data)
            self._add_row(data)

    def _on_editar(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        current = self._clientes[idx]
        dlg = ClienteDialog(parent=self, data=current)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            updated = dlg.get_data()
            updated["id"] = current["id"]
            try:
                repo.update_client(updated["id"], updated)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error BD", f"No se pudo actualizar: {e}")
                return
            self._clientes[idx] = updated
            for i, key in enumerate(["nombre", "telefono", "direccion", "email", "cedula_rif"]):
                self.table.item(idx, i).setText(updated.get(key, ""))

    def _on_eliminar(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        nombre = self.table.item(idx, 0).text()
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setWindowTitle("Confirmar eliminación")
        msg.setText(f"¿Eliminar cliente '{nombre}'?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Sí")
        msg.button(QtWidgets.QMessageBox.No).setText("No")
        result = msg.exec()
        if result == QtWidgets.QMessageBox.Yes:
            try:
                repo.delete_client(self._clientes[idx]["id"])
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error BD", f"No se pudo eliminar: {e}")
                return
            self.table.removeRow(idx)
            del self._clientes[idx]

    def _on_double_click(self, item):
        self._on_editar()


class ClienteDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Cliente")
        self.setModal(True)
        self._build_ui()
        if data:
            self._set_data(data)

    def _build_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.input_nombre = QtWidgets.QLineEdit()
        self.input_telefono = QtWidgets.QLineEdit()
        self.input_direccion = QtWidgets.QLineEdit()
        self.input_email = QtWidgets.QLineEdit()

        # Nueva estructura: selector de tipo ID y número
        self.input_tipo_rif = QtWidgets.QComboBox()
        self.input_tipo_rif.addItems(["V-", "J-"])
        self.input_rif_num = QtWidgets.QLineEdit()

        form.addRow("Nombre", self.input_nombre)
        form.addRow("Teléfono", self.input_telefono)
        form.addRow("Dirección", self.input_direccion)
        form.addRow("Email", self.input_email)
        form.addRow("Tipo ID", self.input_tipo_rif)
        form.addRow("Número", self.input_rif_num)
        v.addLayout(form)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    def _set_data(self, data):
        self.input_nombre.setText(data.get("nombre", ""))
        self.input_telefono.setText(data.get("telefono", ""))
        self.input_direccion.setText(data.get("direccion", ""))
        self.input_email.setText(data.get("email", ""))

        ced = data.get("cedula_rif", "")
        if ced:
            if ced.startswith("V-") or ced.startswith("J-"):
                t = ced[:2]
                num = ced[2:]
            else:
                t = "V-"
                num = ced
        else:
            t = "V-"
            num = ""

        self.input_tipo_rif.setCurrentText(t)
        self.input_rif_num.setText(num)

    def _on_accept(self):
        if not self.input_nombre.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
            return

        numero = self.input_rif_num.text().strip()
        if not numero:
            QtWidgets.QMessageBox.warning(self, "Validación", "Debe ingresar el número de identificación.")
            return
        if not numero.isdigit():
            QtWidgets.QMessageBox.warning(self, "Validación", "Formato inválido. Ingrese sólo dígitos en el número.")
            return

        tipo = self.input_tipo_rif.currentText()
        if tipo == "V-" and len(numero) > 8:
            QtWidgets.QMessageBox.warning(self, "Validación", "La cédula (V-) no debe exceder 8 dígitos.")
            return
        if tipo == "J-" and len(numero) > 12:
            QtWidgets.QMessageBox.warning(self, "Validación", "La cédula (J-) no debe exceder 12 dígitos.")
            return

        self.accept()

    def _on_delete(self):
        # Mantener eliminación si exists (opcional para future)
        self.done(99)

    def get_data(self):
        numero = self.input_rif_num.text().strip()
        cedula_rif = f"{self.input_tipo_rif.currentText()}{numero}"
        return {
            "nombre": self.input_nombre.text().strip(),
            "telefono": self.input_telefono.text().strip(),
            "direccion": self.input_direccion.text().strip(),
            "email": self.input_email.text().strip(),
            "cedula_rif": cedula_rif,
        }