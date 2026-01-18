# screens/manual.py
from PySide6 import QtCore, QtWidgets

class ManualScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("MANUAL DE USUARIO")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight:600;")
        layout.addWidget(title)

        # Contenido del manual (texto de ejemplo)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        ejemplo = (
            "Guía de uso del sistema\n\n"
            "1. Inicie sesión con sus credenciales.\n"
            "2. Use el menú lateral para navegar entre secciones.\n"
            "3. En 'Registrar' ingrese los datos del producto y guarde.\n"
            "4. En 'Clientes' gestione la lista de clientes.\n"
            "5. Para dudas contacte al administrador.\n"
        )
        text.setPlainText(ejemplo)
        layout.addWidget(text)