# screens/main_screen.py
from PySide6 import QtCore, QtGui, QtWidgets
from datetime import datetime, date
from screens.inventario import InventarioScreen
from screens.registrar import RegistrarForm
from screens.reportes import ReportesScreen
from screens.manual import ManualScreen
from screens.clientes import ClientesScreen
import core.repo as repo
from core.theme import ThemeManager


class MainScreen(QtWidgets.QWidget):
    def __init__(self, parent=None, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        # Gestor de tema global
        self.theme_manager = ThemeManager()
        self._build_ui()

        # Conectar CRUD de Inventario (DB) a través de wrappers
        self.inventario.on_create = self._inventario_create
        self.inventario.on_update = self._inventario_update
        self.inventario.on_delete = self._inventario_delete

        # Señal de registrar (persistencia y actualización de UI)
        try:
            self.registrar.saved_signal.connect(self._on_registrar_saved)
        except Exception:
            pass

        self._update_theme_label()

    def _build_ui(self):
        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f1720, stop:1 #111827);")
        side_layout = QtWidgets.QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12,12,12,12)

        logo_lbl = QtWidgets.QLabel("SERVICIOS Y\nASTILLADOS DEL SUR")
        logo_lbl.setStyleSheet("color:#e6eef8; font-weight:700;")
        side_layout.addWidget(logo_lbl)
        side_layout.addSpacing(12)

        # Botones
        self.buttons = {}
        sections = ["INVENTARIO","REGISTRAR","REPORTES","CLIENTES","MANUAL"]
        for name in sections:
            btn = QtWidgets.QPushButton(name)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setStyleSheet("background: none; color: #e6eef8; text-align:left; padding-left:8px;")
            btn.setFixedHeight(36)
            btn.clicked.connect(self._on_nav)
            side_layout.addWidget(btn)
            self.buttons[name] = btn

        # Botón de tema (dinámico)
        self.btn_theme = QtWidgets.QPushButton()
        self.btn_theme.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_theme.setStyleSheet("background: none; color: #e6eef8; text-align:left; padding-left:8px;")
        self.btn_theme.setFixedHeight(36)
        self.btn_theme.clicked.connect(self._on_toggle_theme)
        side_layout.addWidget(self.btn_theme)

        side_layout.addStretch(1)

        # Centro (Stack)
        self.stack = QtWidgets.QStackedWidget()

        # Crear instancias y guardarlas
        self.inventario = InventarioScreen()
        self.registrar = RegistrarForm()
        self.reportes = ReportesScreen()
        self.clientes = ClientesScreen()
        self.manual = ManualScreen()

        # Añadir al stack
        self.stack.addWidget(self.inventario)   # idx 0
        self.stack.addWidget(self.registrar)    # idx 1
        self.stack.addWidget(self.reportes)     # idx 2
        self.stack.addWidget(self.clientes)     # idx 3
        self.stack.addWidget(self.manual)       # idx 4

        # Señales
        try:
            self.registrar.saved_signal.connect(self._on_registrar_saved)
        except Exception:
            pass

        h.addWidget(sidebar)
        h.addWidget(self.stack, 1)

        # Actualizar etiqueta de tema al iniciar
        self._update_theme_label()

    def _on_nav(self):
        sender = self.sender()
        mapping = {"INVENTARIO":0, "REGISTRAR":1, "REPORTES":2, "CLIENTES":3, "MANUAL":4}
        idx = mapping.get(sender.text(), 0)
        self.stack.setCurrentIndex(idx)

    def _on_registrar_saved(self, data: dict):
        """
        Persistir en BD y actualizar la vista.
        """
        try:
            # Añadir performed_by si tenemos usuario autenticado
            if self.current_user:
                data["performed_by"] = self.current_user.get("id")

            # Persistir en la BD
            result = repo.create_product_with_inventory(data)
            data["id"] = result.get("inventory_id") or data.get("id")

            # Añadir a la vista local (opcional)
            if hasattr(self.inventario, "add_row_from_registrar"):
                self.inventario.add_row_from_registrar(data)

            # Refrescar desde BD para asegurar consistencia
            try:
                self.inventario.refresh_from_db(__import__("core.repo", fromlist=["core"]).repo)
            except Exception:
                pass

            # Cambiar a inventario
            self.stack.setCurrentIndex(0)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar en la base de datos: {e}")

    def _on_toggle_theme(self):
        """Toggle theme using ThemeManager and refresh label."""
        try:
            if self.theme_manager:
                self.theme_manager.toggle_theme()
                self._update_theme_label()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"No se pudo cambiar el tema: {e}")

    def _update_theme_label(self):
        """Actualiza el texto del botón de tema para reflejar el estado actual."""
        try:
            if self.theme_manager:
                current = getattr(self.theme_manager, "current_theme", None)
                if current == self.theme_manager.THEME_DARK:
                    self.btn_theme.setText("Tema: Oscuro")
                else:
                    self.btn_theme.setText("Tema: Claro")
            else:
                self.btn_theme.setText("Tema")
        except Exception:
            self.btn_theme.setText("Tema")

    # --- CRUD wrappers para Inventario (conexión DB) ---
    def _inventario_create(self, data: dict):
        """Crea inventario en DB y devuelve el id de inventario (si aplica)."""
        prod = data.get("prod_date")
        if isinstance(prod, (datetime, date)):
            if isinstance(prod, datetime):
                data["prod_date"] = prod.date().isoformat()
            else:
                data["prod_date"] = prod.isoformat()
        disp = data.get("dispatch_date")
        if isinstance(disp, (datetime, date)):
            if isinstance(disp, datetime):
                data["dispatch_date"] = disp.date().isoformat()
            else:
                data["dispatch_date"] = disp.isoformat()

        resp = repo.create_product_with_inventory(data)
        if isinstance(resp, dict):
            inv_id = resp.get("inventory_id") or resp.get("inventoryId")
            if inv_id is not None:
                return int(inv_id)
        if isinstance(resp, int):
            return resp
        return None

    def _inventario_update(self, data: dict):
        """Actualiza inventario en DB."""
        prod = data.get("prod_date")
        if isinstance(prod, (datetime, date)):
            data["prod_date"] = prod.date().isoformat() if isinstance(prod, datetime) else prod.isoformat()
        disp = data.get("dispatch_date")
        if isinstance(disp, (datetime, date)):
            data["dispatch_date"] = disp.date().isoformat() if isinstance(disp, datetime) else disp.isoformat()
        try:
            repo.update_inventory(data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error BD", f"No se pudo actualizar: {e}")

    def _inventario_delete(self, inventory_id: int):
        """Elimina inventario de DB."""
        try:
            repo.delete_inventory(inventory_id)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error BD", f"No se pudo eliminar: {e}")