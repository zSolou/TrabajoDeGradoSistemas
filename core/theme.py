# core/theme.py
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings
from core.styles import DARK_THEME, LIGHT_THEME

class ThemeManager:
    """
    Centraliza el manejo de tema (oscuro/claro) para la app PySide6.
    Aplica el tema a toda la aplicación mediante QApplication.setStyleSheet.
    Persistencia de preferencia usando QSettings.
    """
    THEME_KEY = "theme"
    THEME_DARK = "dark"
    THEME_LIGHT = "light"

    def __init__(self, app: 'QtWidgets.QApplication' | None = None):
        # Obtiene la instancia de la app si no se le pasa explícitamente
        self.app = app or QtWidgets.QApplication.instance()
        self._theme = self._load_theme()
        self._apply(self._theme)

    def _load_theme(self) -> str:
        try:
            settings = QSettings("TesisSistemas", "OpenCode")
            t = settings.value(self.THEME_KEY, self.THEME_DARK)
            if isinstance(t, str) and t in (self.THEME_DARK, self.THEME_LIGHT):
                return t
        except Exception:
            pass
        return self.THEME_DARK

    def _save_theme(self, theme: str):
        try:
            settings = QSettings("TesisSistemas", "OpenCode")
            settings.setValue(self.THEME_KEY, theme)
        except Exception:
            pass

    def _apply(self, theme: str):
        if not self.app:
            return
        if theme == self.THEME_DARK:
            self.app.setStyleSheet(DARK_THEME)
        else:
            self.app.setStyleSheet(LIGHT_THEME)

    def apply_theme(self, theme: str | None = None):
        if theme is None:
            theme = self._theme
        if theme not in (self.THEME_DARK, self.THEME_LIGHT):
            theme = self.THEME_DARK
        self._theme = theme
        self._apply(theme)
        self._save_theme(theme)

    def toggle_theme(self):
        new_theme = self.THEME_LIGHT if self._theme == self.THEME_DARK else self.THEME_DARK
        self.apply_theme(new_theme)