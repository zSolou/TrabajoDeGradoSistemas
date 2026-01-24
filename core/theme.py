# core/theme.py
from typing import Optional
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings

# Intentamos importar los estilos, si no existen, definimos unos vacíos para que no falle
try:
    from core.styles import DARK_THEME, LIGHT_THEME
except ImportError:
    DARK_THEME = ""
    LIGHT_THEME = ""

# --- 1. CONSTANTES DE COLOR (Necesarias para main_screen.py) ---
# Estas son las variables que causaban el error al faltar
BG_MAIN = "#1e1e2f"       # Fondo principal
BG_SIDEBAR = "#27293d"    # Fondo menú lateral
BG_INPUT = "#2b3553"      # Fondo inputs
TEXT_PRIMARY = "#ffffff"  # Texto blanco
TEXT_SECONDARY = "#a9a9b3" # Texto gris
ACCENT_COLOR = "#32D424"  # Color de acento (verde como tu título)
HOVER_SIDEBAR = "rgba(255, 255, 255, 0.1)" # Efecto hover
# ---------------------------------------------------------------


# --- 2. TU CLASE THEME MANAGER (Original) ---
class ThemeManager:
    """
    Centraliza el manejo de tema (Oscuro/Claro) para la app PySide6.
    Aplica el tema a toda la aplicación mediante QApplication.setStyleSheet.
    Persistencia de preferencia usando QSettings.
    """
    THEME_KEY = "theme"
    THEME_DARK = "dark"
    THEME_LIGHT = "light"

    def __init__(
        self,
        app: Optional[QtWidgets.QApplication] = None,
        default_theme: Optional[str] = None
    ) -> None:
        self.app = app or QtWidgets.QApplication.instance()

        # If a default theme is provided, use it and persist it; otherwise load from store.
        if default_theme in (self.THEME_DARK, self.THEME_LIGHT):
            self._theme = default_theme
            self._save_theme(self._theme)
        else:
            self._theme = self._load_theme()

        self._apply(self._theme)

    def _load_theme(self) -> str:
        try:
            settings = QSettings("TrabajoDeGradoSistemas", "OpenCode")
            t = settings.value(self.THEME_KEY, self.THEME_DARK)
            if isinstance(t, str) and t in (self.THEME_DARK, self.THEME_LIGHT):
                return t
        except Exception:
            pass
        return self.THEME_DARK

    def _save_theme(self, theme: str):
        try:
            settings = QSettings("TrabajoDeGradoSistemas", "OpenCode")
            settings.setValue(self.THEME_KEY, theme)
        except Exception:
            pass

    def _apply(self, theme: str):
        if not self.app:
            return
        self.app.setStyleSheet(DARK_THEME if theme == self.THEME_DARK else LIGHT_THEME)

    def apply_theme(self, theme: Optional[str] = None) -> None:
        if theme is None:
            theme = self._theme
        if theme not in (self.THEME_DARK, self.THEME_LIGHT):
            theme = self.THEME_DARK
        self._theme = theme
        self._apply(theme)
        self._save_theme(theme)

    def toggle_theme(self) -> None:
        new_theme = self.THEME_LIGHT if self._theme == self.THEME_DARK else self.THEME_DARK
        self.apply_theme(new_theme)

    @property
    def current_theme(self) -> str:
        """
        Propiedad pública para obtener el tema actual ('dark' | 'light').
        Útil para mostrar en la UI el estado actual.
        """
        return self._theme