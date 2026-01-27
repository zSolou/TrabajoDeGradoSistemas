from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

class ClienteDialog(QtWidgets.QDialog):
    """Diálogo para Crear o Editar Cliente"""
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.setWindowTitle("Nuevo Cliente" if not data else "Editar Cliente")
        self.setModal(True)
        self.resize(400, 350)
        self.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; color: {theme.TEXT_PRIMARY};")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(15)

        self.inp_nombre = self._make_input(self.data.get("name", ""))
        self.inp_cedula = self._make_input(self.data.get("document_id", ""))
        self.inp_telefono = self._make_input(self.data.get("phone", ""))
        self.inp_email = self._make_input(self.data.get("email", ""))
        self.inp_direccion = QtWidgets.QPlainTextEdit()
        self.inp_direccion.setPlainText(self.data.get("address", ""))
        self.inp_direccion.setFixedHeight(60)
        self.inp_direccion.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; border-radius: 4px;")

        form_layout.addRow("Nombre / Razón Social *:", self.inp_nombre)
        form_layout.addRow("Cédula / RIF *:", self.inp_cedula)
        form_layout.addRow("Teléfono:", self.inp_telefono)
        form_layout.addRow("Email:", self.inp_email)
        form_layout.addRow("Dirección:", self.inp_direccion)

        layout.addLayout(form_layout)

        # Botones
        btn_layout = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Guardar")
        btn_save.setCursor(QtCore.Qt.PointingHandCursor)
        btn_save.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        btn_save.clicked.connect(self._validate_and_accept)
        
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; padding: 8px 16px; border-radius: 4px;")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _make_input(self, text):
        inp = QtWidgets.QLineEdit(text)
        inp.setStyleSheet(f"background-color: {theme.BG_INPUT}; border: 1px solid {theme.BORDER_COLOR}; padding: 5px; border-radius: 4px; color: white;")
        return inp

    def _validate_and_accept(self):
        if not self.inp_nombre.text().strip() or not self.inp_cedula.text().strip():
            QtWidgets.QMessageBox.warning(self, "Datos Faltantes", "Nombre y Cédula/RIF son obligatorios.")
            return
        self.accept()

    def get_data(self):
        return {
            "nombre": self.inp_nombre.text().strip(),
            "cedula_rif": self.inp_cedula.text().strip(),
            "telefono": self.inp_telefono.text().strip(),
            "email": self.inp_email.text().strip(),
            "direccion": self.inp_direccion.toPlainText().strip()
        }


class ClientesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Encabezado ---
        header = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("GESTIÓN DE CLIENTES")
        lbl.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        header.addWidget(lbl)
        header.addStretch()
        
        # Checkbox para ver desactivados
        self.chk_ver_inactivos = QtWidgets.QCheckBox("Ver Desactivados")
        self.chk_ver_inactivos.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-weight: bold;")
        self.chk_ver_inactivos.stateChanged.connect(self.refresh)
        header.addWidget(self.chk_ver_inactivos)
        
        # Botón Nuevo
        btn_nuevo = QtWidgets.QPushButton("+ Nuevo Cliente")
        btn_nuevo.setCursor(QtCore.Qt.PointingHandCursor)
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_SUCCESS}; color: black; border-radius: 5px; padding: 6px 15px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #00cfa5; }}
        """)
        btn_nuevo.clicked.connect(self._nuevo_cliente)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        # --- Barra de Acciones ---
        actions_layout = QtWidgets.QHBoxLayout()
        btn_edit = QtWidgets.QPushButton("✎ Editar Seleccionado")
        btn_edit.setCursor(QtCore.Qt.PointingHandCursor)
        btn_edit.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; border-radius: 4px; padding: 6px 12px;")
        btn_edit.clicked.connect(self._editar_cliente)
        
        self.btn_toggle = QtWidgets.QPushButton("Ban/Unban") # Se actualiza dinámicamente
        self.btn_toggle.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self._toggle_activo)
        
        actions_layout.addWidget(btn_edit)
        actions_layout.addWidget(self.btn_toggle)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # --- Tabla ---
        self.table = QtWidgets.QTableWidget()
        columns = ["ID", "Nombre", "Documento", "Teléfono", "Email", "Estado"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: white; border: 1px solid {theme.BORDER_COLOR}; border-radius: 5px; }}
            QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 5px; border: none; font-weight: bold; }}
            QTableWidget::item:selected {{ background-color: {theme.ACCENT_COLOR}; color: black; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self.table)
        
        # Inicializar estado de botones
        self._update_buttons()

    def refresh(self):
        self.table.setRowCount(0)
        ver_todos = self.chk_ver_inactivos.isChecked()
        try:
            # Si ver_todos es True, pasamos False a solo_activos para ver todo
            clientes = repo.list_clients(solo_activos=not ver_todos)
            
            for c in clientes:
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Estado
                is_active = getattr(c, "is_active", True)
                estado_str = "ACTIVO" if is_active else "INACTIVO"
                
                # Items
                items = [
                    str(c.id), c.name, c.document_id, 
                    c.phone or "", c.email or "", estado_str
                ]
                
                for i, val in enumerate(items):
                    it = QtWidgets.QTableWidgetItem(val)
                    # Colorear fila si está inactivo
                    if not is_active:
                        it.setForeground(QtGui.QColor("#ff6b6b")) # Rojo suave
                    
                    # Guardar objeto completo en columna 0
                    if i == 0:
                        it.setData(QtCore.Qt.UserRole, c)
                        
                    self.table.setItem(r, i, it)
                    
        except Exception as e:
            print(f"Error clientes: {e}")

    def _get_selected_client(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self.table.item(row, 0).data(QtCore.Qt.UserRole)

    def _update_buttons(self):
        client = self._get_selected_client()
        if not client:
            self.btn_toggle.setEnabled(False)
            self.btn_toggle.setText("Desactivar / Activar")
            self.btn_toggle.setStyleSheet(f"background-color: gray; color: white; border-radius: 4px; padding: 6px 12px;")
            return

        self.btn_toggle.setEnabled(True)
        is_active = getattr(client, "is_active", True)
        
        if is_active:
            self.btn_toggle.setText("🚫 Desactivar Cliente")
            self.btn_toggle.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; border-radius: 4px; padding: 6px 12px;")
        else:
            self.btn_toggle.setText("✅ Reactivar Cliente")
            self.btn_toggle.setStyleSheet(f"background-color: {theme.BTN_SUCCESS}; color: black; border-radius: 4px; padding: 6px 12px;")

    def _nuevo_cliente(self):
        dialog = ClienteDialog(parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            try:
                repo.create_client(data)
                QtWidgets.QMessageBox.information(self, "Éxito", "Cliente registrado.")
                self.refresh()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _editar_cliente(self):
        client = self._get_selected_client()
        if not client: return
        
        # Convertir objeto SQLAlchemy a dict para el diálogo
        data_dict = {
            "name": client.name,
            "document_id": client.document_id,
            "phone": client.phone,
            "email": client.email,
            "address": client.address
        }
        
        dialog = ClienteDialog(data=data_dict, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_data = dialog.get_data()
            try:
                repo.update_client(client.id, new_data)
                QtWidgets.QMessageBox.information(self, "Éxito", "Cliente actualizado.")
                self.refresh()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _toggle_activo(self):
        client = self._get_selected_client()
        if not client: return
        
        is_active = getattr(client, "is_active", True)
        action = "desactivar" if is_active else "reactivar"
        
        confirm = QtWidgets.QMessageBox.question(
            self, f"Confirmar {action}",
            f"¿Desea {action} al cliente '{client.name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if confirm == QtWidgets.QMessageBox.Yes:
            try:
                repo.toggle_client_active(client.id, not is_active)
                self.refresh()
                self._update_buttons()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))