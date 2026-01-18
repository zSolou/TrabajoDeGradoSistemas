# core/app.py
from PySide6 import QtWidgets
from screens.login import LoginScreen
from screens.main_screen import MainScreen
from core.styles import DARK_THEME, LIGHT_THEME

class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema - Servicios y Astillidos del Sur")
        self.resize(1000, 600)

        # estado de tema: True = dark, False = light
        self._dark_mode = True
        self.setStyleSheet(DARK_THEME)

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

    def toggle_theme(self):
        """Alterna entre tema oscuro y claro."""
        if self._dark_mode:
            self.setStyleSheet(LIGHT_THEME)
            self._dark_mode = False
        else:
            self.setStyleSheet(DARK_THEME)
            self._dark_mode = True