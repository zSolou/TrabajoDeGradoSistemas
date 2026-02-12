from PySide6 import QtCore, QtWidgets, QtGui
from screens.inventario import InventarioScreen
from screens.registrar import RegistrarForm
from screens.reportes import ReportesScreen
from screens.clientes import ClientesScreen
from screens.manual import ManualScreen
from screens.respaldo import RespaldoScreen
from screens.despacho import DespachoScreen
from core import theme

class MainScreen(QtWidgets.QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal (Horizontal: Menú + Contenido)
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. MENÚ LATERAL ---
        self.side_menu = QtWidgets.QFrame()
        self.side_menu.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-right: 1px solid {theme.BORDER_COLOR};")
        self.side_menu.setFixedWidth(240)
        
        menu_layout = QtWidgets.QVBoxLayout(self.side_menu)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(10)

        # Título / Logo
        lbl_title = QtWidgets.QLabel("SISTEMA DE INVENTARIO\nSERVICIOS Y ASTILLADOS DEL SUR")
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 10pt; color: white; margin-bottom: 20px;")
        menu_layout.addWidget(lbl_title)

        # Botones de Navegación
        self.btn_inv = self._create_nav_button("📦 Inventario")
        self.btn_reg = self._create_nav_button("📝 Registrar Prod.")
        self.btn_desp = self._create_nav_button("🚚 Despacho")
        self.btn_rep = self._create_nav_button("📊 Reportes")
        self.btn_cli = self._create_nav_button("👥 Clientes")
        self.btn_res = self._create_nav_button("💾 Respaldo")
        self.btn_man = self._create_nav_button("❓ Manual")
        
        # Logout
        self.btn_logout = QtWidgets.QPushButton("Cerrar Sesión")
        self.btn_logout.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet(f"background-color: {theme.BTN_DANGER}; color: white; border-radius: 5px; padding: 10px; font-weight: bold;")
        
        # Añadir al menú
        menu_layout.addWidget(self.btn_inv)
        menu_layout.addWidget(self.btn_reg)
        menu_layout.addWidget(self.btn_desp)
        menu_layout.addWidget(self.btn_rep)
        menu_layout.addWidget(self.btn_cli)
        menu_layout.addWidget(self.btn_res)
        menu_layout.addWidget(self.btn_man)
        menu_layout.addStretch()
        menu_layout.addWidget(self.btn_logout)

        main_layout.addWidget(self.side_menu)

        # --- 2. CONTENIDO (STACK) ---
        self.stack = QtWidgets.QStackedWidget()
        
        # Instancias de las pantallas
        self.inv_screen = InventarioScreen()   # Índice 0
        self.reg_screen = RegistrarForm()      # Índice 1
        self.desp_screen = DespachoScreen()    # Índice 2
        self.rep_screen = ReportesScreen()     # Índice 3
        self.cli_screen = ClientesScreen()     # Índice 4
        self.res_screen = RespaldoScreen()     # Índice 5
        self.man_screen = ManualScreen()       # Índice 6

        # Conectar señal de registro exitoso
        self.reg_screen.saved_signal.connect(self._on_product_registered)

        # Añadir al stack (El orden es CRÍTICO)
        self.stack.addWidget(self.inv_screen)
        self.stack.addWidget(self.reg_screen)
        self.stack.addWidget(self.desp_screen)
        self.stack.addWidget(self.rep_screen)
        self.stack.addWidget(self.cli_screen)
        self.stack.addWidget(self.res_screen)
        self.stack.addWidget(self.man_screen)

        main_layout.addWidget(self.stack)

        # Conectar clics a la navegación
        self.btn_inv.clicked.connect(lambda: self._navigate(0, self.btn_inv))
        self.btn_reg.clicked.connect(lambda: self._navigate(1, self.btn_reg))
        self.btn_desp.clicked.connect(lambda: self._navigate(2, self.btn_desp))
        self.btn_rep.clicked.connect(lambda: self._navigate(3, self.btn_rep))
        self.btn_cli.clicked.connect(lambda: self._navigate(4, self.btn_cli))
        self.btn_res.clicked.connect(lambda: self._navigate(5, self.btn_res))
        self.btn_man.clicked.connect(lambda: self._navigate(6, self.btn_man))

        # Iniciar en inventario
        self._navigate(0, self.btn_inv)

    def _create_nav_button(self, text):
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setMinimumHeight(45)
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 20px;
                color: {theme.TEXT_SECONDARY};
                background-color: transparent;
                border: none;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                color: {theme.TEXT_PRIMARY};
                background-color: {theme.BG_INPUT};
            }}
        """)
        return btn

    def _navigate(self, index, button):
        self.stack.setCurrentIndex(index)
        
        # 1. Limpiar estilo de TODOS los botones
        all_buttons = [
            self.btn_inv, self.btn_reg, self.btn_desp, 
            self.btn_rep, self.btn_cli, self.btn_res, self.btn_man
        ]
        
        for btn in all_buttons:
            style = btn.styleSheet()
            style = style.replace(f"color: {theme.ACCENT_COLOR};", f"color: {theme.TEXT_SECONDARY};")
            style = style.replace(f"border-left: 4px solid {theme.ACCENT_COLOR};", "border: none;")
            style = style.replace("font-weight: bold;", "")
            style = style.replace("background-color: #1b1b26;", "background-color: transparent;")
            btn.setStyleSheet(style)
        
        # 2. Marcar botón activo
        active_style = button.styleSheet()
        active_style = active_style.replace(f"color: {theme.TEXT_SECONDARY};", f"color: {theme.ACCENT_COLOR};")
        active_style += f" font-weight: bold; border-left: 4px solid {theme.ACCENT_COLOR}; background-color: #1b1b26;"
        button.setStyleSheet(active_style)
        
        # 3. Refrescar datos (Protegido contra errores)
        try:
            if index == 0: # Inventario
                self.inv_screen.refresh()
            elif index == 2: # Despacho
                self.desp_screen.refresh_clients()
            elif index == 4: # Clientes
                self.cli_screen.refresh()
        except Exception as e:
            print(f"Advertencia al refrescar pantalla {index}: {e}")
            # No mostramos popup para no interrumpir la navegación

    def _on_product_registered(self, data):
        """Al guardar un producto, volvemos al inventario."""
        self._navigate(0, self.btn_inv)