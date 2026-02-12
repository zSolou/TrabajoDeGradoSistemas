from PySide6 import QtCore, QtGui, QtWidgets
from core import repo, theme
import os

class LoginScreen(QtWidgets.QWidget):
    # Señal de éxito al loguearse (pasa los datos del usuario)
    success_signal = QtCore.Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # Layout principal (Fondo completo)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Estilo Global de la Pantalla
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.BG_SIDEBAR}; 
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)

        # --- TARJETA DE LOGIN (Card) ---
        self.card = QtWidgets.QFrame()
        self.card.setFixedWidth(400)
        self.card.setObjectName("LoginCard")
        # Estilo específico para la tarjeta y sus componentes internos
        self.card.setStyleSheet(f"""
            QFrame#LoginCard {{
                background-color: {theme.BG_INPUT};
                border: 1px solid {theme.BORDER_COLOR};
                border-radius: 12px;
            }}
            QLabel {{
                background-color: transparent;
                color: {theme.TEXT_PRIMARY};
                border: none;
            }}
            QLineEdit {{
                background-color: {theme.BG_SIDEBAR};
                border: 1px solid {theme.BORDER_COLOR};
                color: {theme.TEXT_PRIMARY};
                border-radius: 6px;
                padding: 10px;
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme.ACCENT_COLOR};
            }}
            QPushButton {{
                background-color: {theme.BTN_PRIMARY};
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 10px;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_COLOR};
            }}
        """)

        card_layout = QtWidgets.QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # 1. LOGO / TÍTULO DE EMPRESA
        logo_lbl = QtWidgets.QLabel()
        logo_lbl.setAlignment(QtCore.Qt.AlignCenter)
        
        if os.path.exists("logo.png"):
            pix = QtGui.QPixmap("logo.png")
            # Escalar manteniendo relación de aspecto (Ancho máx 250, Alto máx 100)
            pix = pix.scaled(250, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        else:
            # Fallback si no hay logo
            logo_lbl.setText("SERVICIOS Y\nASTILLADOS DEL SUR")
            logo_lbl.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {theme.ACCENT_COLOR};")
        
        card_layout.addWidget(logo_lbl)

        # 2. TÍTULO "INICIAR SESIÓN"
        lbl_title = QtWidgets.QLabel("Bienvenido")
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 14pt; color: #a0aec0; font-weight: 500; margin-bottom: 10px;")
        card_layout.addWidget(lbl_title)

        # 3. FORMULARIO
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("👤 Usuario")
        self.user_input.setMinimumHeight(45)
        
        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setPlaceholderText("🔒 Contraseña")
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_input.setMinimumHeight(45)
        self.pass_input.returnPressed.connect(self._on_login) # Enter para entrar

        card_layout.addWidget(self.user_input)
        card_layout.addWidget(self.pass_input)

        # 4. BOTÓN ACCEDER
        self.btn_login = QtWidgets.QPushButton("INGRESAR AL SISTEMA")
        self.btn_login.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_login.setMinimumHeight(50)
        self.btn_login.clicked.connect(self._on_login)
        card_layout.addWidget(self.btn_login)

        # 5. PIE DE PÁGINA (Versión)
        lbl_ver = QtWidgets.QLabel("Sistema de Gestión")
        lbl_ver.setAlignment(QtCore.Qt.AlignCenter)
        lbl_ver.setStyleSheet("color: #555; font-size: 9pt; margin-top: 10px;")
        card_layout.addWidget(lbl_ver)

        # Añadir tarjeta al centro
        main_layout.addWidget(self.card)

        # Sombra suave para la tarjeta (Efecto de elevación)
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)

    def _on_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            QtWidgets.QMessageBox.warning(self, "Datos Incompletos", "Por favor ingrese usuario y contraseña.")
            self.user_input.setFocus()
            return

        # Bloquear botón momentáneamente
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Verificando...")
        QtWidgets.QApplication.processEvents()

        try:
            user = repo.authenticate_user_plain(username, password)
            if user:
                # Login Exitoso
                self.success_signal.emit(user)
            else:
                QtWidgets.QMessageBox.critical(self, "Acceso Denegado", "Usuario o contraseña incorrectos.")
                self.pass_input.clear()
                self.pass_input.setFocus()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error de Conexión", f"No se pudo conectar a la base de datos.\nDetalle: {str(e)}")
        finally:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("INGRESAR AL SISTEMA")