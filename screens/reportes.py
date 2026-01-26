from PySide6 import QtCore, QtWidgets
from datetime import date, timedelta
import math
from core import repo, theme

# Manejo de Matplotlib (Gráficos)
try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        lbl_title = QtWidgets.QLabel("ANÁLISIS DE PRODUCCIÓN")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        layout.addWidget(lbl_title)

        # --- Filtros ---
        filter_container = QtWidgets.QFrame()
        filter_container.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-radius: 8px;")
        filter_layout = QtWidgets.QHBoxLayout(filter_container)
        
        self.cb_tipo = QtWidgets.QComboBox()
        self.cb_tipo.addItems(["Todos los Tipos", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        self._estilizar_combo(self.cb_tipo)
        
        self.cb_fecha = QtWidgets.QComboBox()
        self.cb_fecha.addItems(["Cualquier Fecha", "Última Semana", "Último Mes"])
        self._estilizar_combo(self.cb_fecha)

        btn_aplicar = QtWidgets.QPushButton("Actualizar Gráfico")
        btn_aplicar.setStyleSheet(f"""
            QPushButton {{ background-color: {theme.BTN_PRIMARY}; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold;}}
            QPushButton:hover {{ background-color: #0b5ed7; }}
        """)
        btn_aplicar.clicked.connect(self._aplicar_filtros)

        filter_layout.addWidget(QtWidgets.QLabel("Filtrar por:", parent=filter_container))
        filter_layout.addWidget(self.cb_tipo)
        filter_layout.addWidget(self.cb_fecha)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_aplicar)
        
        layout.addWidget(filter_container)

        # --- Gráfico ---
        self.chart_container = QtWidgets.QWidget()
        chart_layout = QtWidgets.QVBoxLayout(self.chart_container)
        
        if MATPLOTLIB_AVAILABLE:
            # Configurar colores de matplotlib para modo oscuro
            self.figure = Figure(figsize=(5, 4), facecolor=theme.BG_MAIN) # Fondo externo
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")
            chart_layout.addWidget(self.canvas)
        else:
            lbl_error = QtWidgets.QLabel("Librería 'matplotlib' no instalada.\nNo se pueden ver gráficos.")
            lbl_error.setAlignment(QtCore.Qt.AlignCenter)
            lbl_error.setStyleSheet("color: white;")
            chart_layout.addWidget(lbl_error)
            
        layout.addWidget(self.chart_container, 1) # Expandir

    def _estilizar_combo(self, combo):
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.BG_INPUT};
                color: {theme.TEXT_PRIMARY};
                border: 1px solid {theme.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)

    def _load_data(self):
        try:
            self.all_rows = repo.list_inventory_rows()
            self._aplicar_filtros()
        except Exception as e:
            print(f"Error cargando datos reportes: {e}")

    def _aplicar_filtros(self):
        if not MATPLOTLIB_AVAILABLE: return

        tipo_filtro = self.cb_tipo.currentText()
        fecha_filtro = self.cb_fecha.currentText()
        
        # Lógica de filtrado simple
        filtrados = []
        hoy = date.today()
        
        for r in self.all_rows:
            # Filtro Tipo
            prod_type = r.get("product_type", "")
            if tipo_filtro != "Todos los Tipos" and prod_type != tipo_filtro:
                continue
            
            # Filtro Fecha (asumiendo formato ISO YYYY-MM-DD o datetime)
            f_prod_str = r.get("prod_date")
            if fecha_filtro != "Cualquier Fecha" and f_prod_str:
                try:
                    # Convertir si es string
                    if isinstance(f_prod_str, str):
                        f_prod = date.fromisoformat(f_prod_str)
                    else:
                        f_prod = f_prod_str # Asumimos objeto date
                    
                    if fecha_filtro == "Última Semana" and (hoy - f_prod).days > 7:
                        continue
                    if fecha_filtro == "Último Mes" and (hoy - f_prod).days > 30:
                        continue
                except:
                    pass # Si falla la fecha, lo incluimos o excluimos según lógica
            
            filtrados.append(r)

        # Generar datos para el Pie Chart
        totales = {}
        for r in filtrados:
            t = r.get("product_type", "Otros")
            q = float(r.get("quantity") or 0)
            totales[t] = totales.get(t, 0) + q

        self._dibujar_grafico(totales)

    def _dibujar_grafico(self, data_dict):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(theme.BG_MAIN) # Fondo interno

        labels = [k for k, v in data_dict.items() if v > 0]
        sizes = [v for k, v in data_dict.items() if v > 0]
        
        if not sizes:
            ax.text(0.5, 0.5, "Sin datos para mostrar", color="white", ha="center")
        else:
            # Colores personalizados
            colores = ['#32D424', '#0d6efd', '#e14eca', '#ffc107', '#0dcaf0']
            
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', 
                startangle=90, colors=colores,
                textprops={'color':"white"} # Texto blanco
            )
            ax.set_title("Distribución de Inventario (Volumen)", color=theme.ACCENT_COLOR, fontsize=12)

        self.canvas.draw()