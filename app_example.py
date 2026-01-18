# app_example.py
import sys
from PySide6 import QtCore, QtGui, QtWidgets

# ---------------------------
# LoginScreen
# ---------------------------
class LoginScreen(QtWidgets.QWidget):
    success_signal = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setAlignment(QtCore.Qt.AlignCenter)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(12)

        # Logo (ajusta ruta si es necesario)
        logo = QtWidgets.QLabel()
        pix = QtGui.QPixmap("logo.png")
        if not pix.isNull():
            pix = pix.scaled(220, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("SERVICIOS Y ASTILLADOS DEL SUR")
            logo.setAlignment(QtCore.Qt.AlignCenter)
            logo.setStyleSheet("font-weight:700; color: #fbbf24;")
        main.addWidget(logo)

        # Card-like container
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

        # Small helper
        footer = QtWidgets.QLabel("Usuario demo: admin  |  Clave demo: 12345")
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
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()
        # Validación demo
        if user == "admin" and pwd == "12345":
            self.success_signal.emit()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Usuario o clave incorrectos.")


# ---------------------------
# Screens para MainScreen
# ---------------------------
class InventarioScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Inventario")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        l.addWidget(lbl)

class RegistrarForm(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("REGISTRAR PRODUCTO")
        title.setStyleSheet("font-weight:600; font-size:14pt;")
        main.addWidget(title)

        form = QtWidgets.QFormLayout()
        self.name = QtWidgets.QLineEdit()
        self.m3 = QtWidgets.QDoubleSpinBox(); self.m3.setDecimals(3); self.m3.setRange(0, 1_000_000)
        self.pieces = QtWidgets.QSpinBox(); self.pieces.setRange(0, 1_000_000)
        self.quality = QtWidgets.QComboBox(); self.quality.addItems(["Alta","Media","Baja"])
        self.obs = QtWidgets.QPlainTextEdit(); self.obs.setFixedHeight(80)

        form.addRow("Nombre Producto", self.name)
        form.addRow("Medidas M3", self.m3)
        form.addRow("Nº Piezas", self.pieces)
        form.addRow("Calidad", self.quality)
        form.addRow("Observación", self.obs)
        main.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        save = QtWidgets.QPushButton("Guardar")
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)
        main.addLayout(btn_row)

    def _on_save(self):
        if not self.name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validación", "El nombre del producto es obligatorio.")
            return
        QtWidgets.QMessageBox.information(self, "Guardado", "Producto registrado correctamente.")
        self.name.clear()
        self.m3.setValue(0)
        self.pieces.setValue(0)
        self.obs.clear()

class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QtWidgets.QVBoxLayout(self)
        l.addWidget(QtWidgets.QLabel("Reportes"))


# ---------------------------
# MainScreen (menú lateral + stack interno)
# ---------------------------
class MainScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0,0,0,0)

        # Sidebar
        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f1720, stop:1 #111827);")
        side_layout = QtWidgets.QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12,12,12,12)
        logo_lbl = QtWidgets.QLabel("SERVICIOS Y\nASTILLADOS DEL SUR")
        logo_lbl.setStyleSheet("color:#fbbf24; font-weight:700;")
        side_layout.addWidget(logo_lbl)
        side_layout.addSpacing(12)

        # Botones
        self.buttons = {}
        for name in ["INVENTARIO","REGISTRAR","REPORTES"]:
            btn = QtWidgets.QPushButton(name)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setStyleSheet("background: none; color: #e6eef8; text-align:left; padding-left:8px;")
            btn.setFixedHeight(36)
            btn.clicked.connect(self._on_nav)
            side_layout.addWidget(btn)
            self.buttons[name] = btn
        side_layout.addStretch(1)

        # Stack central con pantallas internas
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(InventarioScreen())   # idx 0
        self.stack.addWidget(RegistrarForm())      # idx 1
        self.stack.addWidget(ReportesScreen())     # idx 2

        h.addWidget(sidebar)
        h.addWidget(self.stack, 1)

    def _on_nav(self):
        sender = self.sender()
        mapping = {"INVENTARIO":0, "REGISTRAR":1, "REPORTES":2}
        idx = mapping.get(sender.text(), 0)
        self.stack.setCurrentIndex(idx)


# ---------------------------
# MainApp (QMainWindow con QStackedWidget: login + main)
# ---------------------------
class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema - Servicios y Astillidos del Sur")
        self.resize(1000, 600)

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # crear pantallas
        self.login = LoginScreen()
        self.main = MainScreen()

        # añadir al stack de la aplicación
        self.stack.addWidget(self.login)  # idx 0
        self.stack.addWidget(self.main)   # idx 1

        # conectar señal del login
        self.login.success_signal.connect(self._show_main)

    def _show_main(self):
        self.stack.setCurrentWidget(self.main)


# ---------------------------
# Ejecutar
# ---------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # alta DPI
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    win = MainApp()
    win.show()
    sys.exit(app.exec())