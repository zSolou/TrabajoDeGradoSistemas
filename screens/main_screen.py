from PySide6 import QtCore, QtWidgets, QtGui
from screens.inventario import InventarioScreen
from screens.registrar import RegistrarForm
from screens.reportes import ReportesScreen
from screens.clientes import ClientesScreen
from screens.manual import ManualScreen
from screens.respaldo import RespaldoScreen  
from screens.despacho import DespachoScreen

from core import theme

# En screens/main_screen.py

class MainScreen(QtWidgets.QWidget):
    # CORRECCIÓN: Cambiamos 'auth_data' por 'current_user'
    def __init__(self, current_user=None): 
        super().__init__()
        # Guardamos el usuario en self.auth_data para usarlo en el resto de la clase
        self.auth_data = current_user 
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        # Layout principal horizontal (Menú lateral + Contenido)
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- MENÚ LATERAL ---
        self.side_menu = QtWidgets.QFrame()
        self.side_menu.setStyleSheet(f"background-color: {theme.BG_SIDEBAR};")
        self.side_menu.setFixedWidth(240)
        
        menu_layout = QtWidgets.QVBoxLayout(self.side_menu)
        menu_layout.setContentsMargins(10, 20, 10, 20)
        menu_layout.setSpacing(10)

        # Logo / Título
        title = QtWidgets.QLabel("SERVICIOS Y\nASTILLADOS DEL SUR")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 11pt;")
        title.setAlignment(QtCore.Qt.AlignLeft)
        menu_layout.addWidget(title)
        menu_layout.addSpacing(20)

        # Botones de Navegación
        self.btn_inv = self._create_nav_button("INVENTARIO", "inventory")
        self.btn_despacho = self._create_nav_button("DESPACHOS", "truck") # Icono sugerido
        self.btn_reg = self._create_nav_button("REGISTRAR", "add")
        self.btn_rep = self._create_nav_button("REPORTES", "chart")
        self.btn_cli = self._create_nav_button("CLIENTES", "group")
        
        # --- 2. BOTÓN DE RESPALDO (Debajo de Clientes) ---
        # Usamos un icono genérico 'save' o texto si no tienes iconos
        self.btn_res = self._create_nav_button("RESPALDO", "save") 
        # --------------------------------------------------

        self.btn_man = self._create_nav_button("MANUAL", "help")

        menu_layout.addWidget(self.btn_inv)
        menu_layout.addWidget(self.btn_despacho)
        menu_layout.addWidget(self.btn_reg)
        menu_layout.addWidget(self.btn_rep)
        menu_layout.addWidget(self.btn_cli)
        menu_layout.addWidget(self.btn_res) # <--- Agregamos al layout
        menu_layout.addWidget(self.btn_man)

        menu_layout.addStretch()

        # Footer del menú (Usuario / Tema)
        self.lbl_user = QtWidgets.QLabel(f"Usuario: {self.auth_data.get('username','Guest')}" if self.auth_data else "")
        self.lbl_user.setStyleSheet("color: #888; font-size: 9pt;")
        menu_layout.addWidget(self.lbl_user)
        
        self.theme_switch = QtWidgets.QLabel("Tema: Oscuro")
        self.theme_switch.setStyleSheet("color: #aaa;")
        menu_layout.addWidget(self.theme_switch)

        main_layout.addWidget(self.side_menu)

        # --- ÁREA DE CONTENIDO (STACK) ---
        self.content_area = QtWidgets.QFrame()
        self.content_area.setStyleSheet(f"background-color: {theme.BG_MAIN};")
        content_layout = QtWidgets.QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QtWidgets.QStackedWidget()
        
        # Instanciar Pantallas
        self.inv_screen = InventarioScreen()
        self.despacho_screen = DespachoScreen()
        self.reg_screen = RegistrarForm()
        self.rep_screen = ReportesScreen()
        self.cli_screen = ClientesScreen()
        self.res_screen = RespaldoScreen() # <--- 3. INSTANCIAMOS LA PANTALLA
        self.man_screen = ManualScreen()

        # Agregar al Stack en orden
        self.stack.addWidget(self.inv_screen) # Index 0
        self.stack.addWidget(self.despacho_screen) # Index 1
        self.stack.addWidget(self.reg_screen) # Index 2
        self.stack.addWidget(self.rep_screen) # Index 3
        self.stack.addWidget(self.cli_screen) # Index 4
        self.stack.addWidget(self.res_screen) # Index 5 <--- Agregada
        self.stack.addWidget(self.man_screen) # Index 6

        content_layout.addWidget(self.stack)
        main_layout.addWidget(self.content_area)

    def _create_nav_button(self, text, icon_name):
        """Helper para crear botones del menú con estilo uniforme."""
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedHeight(45)
        # Estilo base (se puede mejorar en styles.py)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.TEXT_SECONDARY};
                text-align: left;
                padding-left: 10px;
                border: none;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.HOVER_SIDEBAR};
                color: {theme.TEXT_PRIMARY};
                border-left: 4px solid {theme.ACCENT_COLOR};
            }}
            QPushButton:checked {{
                color: {theme.ACCENT_COLOR};
            }}
        """)
        # Si tuvieras sistema de iconos, aquí se asignaría icon_name
        return btn

    def _connect_signals(self):
        # Conectar botones al cambio de página
        self.btn_inv.clicked.connect(lambda: self._navigate(0, self.btn_inv))
        self.btn_despacho.clicked.connect(lambda: self._navigate(1, self.btn_despacho))
        self.btn_reg.clicked.connect(lambda: self._navigate(2, self.btn_reg))
        self.btn_rep.clicked.connect(lambda: self._navigate(3, self.btn_rep))
        self.btn_cli.clicked.connect(lambda: self._navigate(4, self.btn_cli))
        self.btn_res.clicked.connect(lambda: self._navigate(5, self.btn_res)) # <--- 4. CONEXIÓN
        self.btn_man.clicked.connect(lambda: self._navigate(6, self.btn_man))

        # Señales internas de las pantallas
        self.reg_screen.saved_signal.connect(self._on_product_registered)

        # Iniciar en inventario
        self._navigate(0, self.btn_inv)

    def _navigate(self, index, button):
        self.stack.setCurrentIndex(index)
        
        # Resetear estilos de todos los botones
        for btn in [self.btn_inv, self.btn_reg, self.btn_rep, self.btn_cli, self.btn_res, self.btn_man]:
            btn.setStyleSheet(btn.styleSheet().replace(f"color: {theme.ACCENT_COLOR};", f"color: {theme.TEXT_SECONDARY};"))
        
        # Marcar activo
        button.setStyleSheet(button.styleSheet().replace(f"color: {theme.TEXT_SECONDARY};", f"color: {theme.ACCENT_COLOR};"))
        
        # Refrescar datos si es necesario
        if index == 0: # Inventario
            if hasattr(self.inv_screen, "refresh"):
                self.inv_screen.refresh()
        elif index == 2: # Reportes
             if hasattr(self.rep_screen, "_load_data"):
                self.rep_screen._load_data()

    def _on_product_registered(self, data):
        """Callback cuando se registra un producto exitosamente."""
        from core import repo
        try:
            repo.create_product_with_inventory(data)
            # Ir al inventario para ver el nuevo producto
            self._navigate(0, self.btn_inv)
            QtWidgets.QMessageBox.information(self, "Éxito", "Producto registrado correctamente.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar en BD: {e}")