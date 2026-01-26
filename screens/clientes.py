from PySide6 import QtCore, QtWidgets
from core import repo, theme

class ClientesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Encabezado
        header = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("GESTIÓN DE CLIENTES")
        lbl.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        header.addWidget(lbl)
        header.addStretch()
        
        btn_nuevo = QtWidgets.QPushButton("+ Nuevo Cliente")
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_SUCCESS}; color: black; border-radius: 5px; padding: 6px 12px; font-weight: bold; }}
            QPushButton:hover {{ background-color: #00cfa5; }}
        """)
        btn_nuevo.clicked.connect(self._nuevo_cliente)
        header.addWidget(btn_nuevo)
        layout.addLayout(header)

        # Tabla
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Documento (RIF/CI)", "Teléfono", "Email"])
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {theme.BG_SIDEBAR}; color: white; border: none; }}
            QHeaderView::section {{ background-color: #1b1b26; color: {theme.TEXT_SECONDARY}; padding: 5px; border: none; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

    def refresh(self):
        self.table.setRowCount(0)
        try:
            clientes = repo.list_clients() # Asegúrate de tener esto en repo.py
            for c in clientes:
                r = self.table.rowCount()
                self.table.insertRow(r)
                # Asumiendo que c es un objeto SQLAlchemy o dict
                # Si es objeto: c.id, c.name. Si es dict: c['id'], c['name']
                # Ajusta según tu repo. Usaré getattr para seguridad
                self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(getattr(c, 'id', ''))))
                self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(str(getattr(c, 'name', ''))))
                self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(getattr(c, 'document_id', ''))))
                self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(str(getattr(c, 'phone', ''))))
                self.table.setItem(r, 4, QtWidgets.QTableWidgetItem(str(getattr(c, 'email', ''))))
        except Exception as e:
            print(f"Error clientes: {e}")

    def _nuevo_cliente(self):
        # Aquí podrías abrir un QDialog simple para agregar
        QtWidgets.QMessageBox.information(self, "En desarrollo", "Función para agregar cliente pendiente de implementar popup.")