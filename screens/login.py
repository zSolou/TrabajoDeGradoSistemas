# screens/login.py
from PySide6 import QtCore, QtGui, QtWidgets
import core.repo as repo   # importa tu capa de persistencia

class LoginScreen(QtWidgets.QWidget):
    # Emitimos el usuario autenticado (dict con id, username, role) si el login es correcto
    success_signal = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setAlignment(QtCore.Qt.AlignCenter)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(12)

        # Logo
        logo = QtWidgets.QLabel()
        pix = QtGui.QPixmap("logo.png")
        if not pix.isNull():
            pix = pix.scaled(220, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("SERVICIOS Y ASTILLADOS DEL SUR")
            logo.setStyleSheet("font-weight:700; color: #fbbf24;")
        logo.setAlignment(QtCore.Qt.AlignCenter)
        logo.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)

        logo_container = QtWidgets.QWidget()
        hc = QtWidgets.QHBoxLayout(logo_container)
        hc.setContentsMargins(0, 0, 0, 0)
        hc.addStretch(1)
        hc.addWidget(logo)
        hc.addStretch(1)

        main.addWidget(logo_container)

        # Card
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setSpacing(8)

        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("Usuario")
        card_layout.addWidget(self.user_input)

        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setPlaceholderText("Clave")
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.Password)
        card_layout.addWidget(self.pass_input)

        btn = QtWidgets.QPushButton("Acceder")
        btn.setFixedHeight(36)
        btn.clicked.connect(self._on_login)
        card_layout.addWidget(btn)

        main.addWidget(card)

        footer = QtWidgets.QLabel("Ingrese sus credenciales registradas en el sistema")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        footer.setStyleSheet("font-size: 10px; color: #94a3b8;")
        main.addWidget(footer)

        # Styles
        self.setStyleSheet("""
        QWidget { background: #0b1220; color: #e6eef8; font-family: Segoe UI, Arial; }
        QFrame#card {
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 14px;
            min-width: 300px;
        }
        QLineEdit {
            background: #0f1724;
            border: 1px solid rgba(255,255,255,0.04);
            color: #e6eef8;
            border-radius: 8px;
            padding: 8px;
            font-size: 11pt;
        }
        QLineEdit:focus { border: 1px solid #2563eb; }
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
            color: white;
            border-radius: 8px;
            font-weight: 600;
        }
        QPushButton:hover { opacity: 0.95; }
        """)

    def _on_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Error", "Debe ingresar usuario y clave.")
            return

        try:
            user = repo.authenticate_user_plain(username, password)
            if user:
                # Emitimos el dict con id, username, role
                self.success_signal.emit(user)
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Usuario o clave incorrectos.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al autenticar: {e}")