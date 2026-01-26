import os
from datetime import date, datetime, timedelta
from PySide6 import QtCore, QtWidgets, QtGui
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

# Manejo de Excel
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []      # Todos los datos crudos
        self.filtered_rows = [] # Datos después de aplicar filtros
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- Título ---
        lbl_title = QtWidgets.QLabel("REPORTE DE PRODUCCIÓN")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        layout.addWidget(lbl_title)

        # --- Panel de Filtros ---
        filter_frame = QtWidgets.QFrame()
        filter_frame.setStyleSheet(f"background-color: {theme.BG_SIDEBAR}; border-radius: 8px; border: 1px solid {theme.BORDER_COLOR};")
        filter_layout = QtWidgets.QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        
        # Combo Tipo
        self.cb_tipo = QtWidgets.QComboBox()
        self.cb_tipo.addItems(["Todos los Tipos", "Tablas", "Machihembrado", "Tablones", "Paletas"])
        self._estilizar_input(self.cb_tipo)
        
        # Combo Fecha
        self.cb_fecha = QtWidgets.QComboBox()
        self.cb_fecha.addItems(["Cualquier Fecha", "Última Semana", "Último Mes", "Personalizado"])
        self._estilizar_input(self.cb_fecha)
        self.cb_fecha.currentTextChanged.connect(self._on_fecha_changed)

        # Fechas Personalizadas (Ocultas por defecto)
        self.date_frame = QtWidgets.QWidget()
        df_layout = QtWidgets.QHBoxLayout(self.date_frame)
        df_layout.setContentsMargins(0,0,0,0)
        
        self.date_start = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_start.setDate(QtCore.QDate.currentDate().addDays(-7))
        self._estilizar_input(self.date_start)
        
        self.date_end = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_end.setDate(QtCore.QDate.currentDate())
        self._estilizar_input(self.date_end)
        
        df_layout.addWidget(QtWidgets.QLabel("Desde:"))
        df_layout.addWidget(self.date_start)
        df_layout.addWidget(QtWidgets.QLabel("Hasta:"))
        df_layout.addWidget(self.date_end)
        
        self.date_frame.setVisible(False) # Inicialmente oculto

        # Botón Aplicar
        btn_aplicar = QtWidgets.QPushButton("Aplicar Filtros")
        btn_aplicar.setCursor(QtCore.Qt.PointingHandCursor)
        btn_aplicar.setStyleSheet(f"background-color: {theme.BTN_PRIMARY}; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
        btn_aplicar.clicked.connect(self._aplicar_filtros)

        # Botón Excel
        btn_excel = QtWidgets.QPushButton("Generar Excel")
        btn_excel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_excel.setStyleSheet("background-color: #217346; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
        btn_excel.clicked.connect(self._exportar_excel)

        # Agregar al layout de filtros
        filter_layout.addWidget(QtWidgets.QLabel("Producto:"))
        filter_layout.addWidget(self.cb_tipo)
        filter_layout.addWidget(QtWidgets.QLabel("Período:"))
        filter_layout.addWidget(self.cb_fecha)
        filter_layout.addWidget(self.date_frame)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_aplicar)
        filter_layout.addWidget(btn_excel)
        
        layout.addWidget(filter_frame)

        # --- Área Principal (Gráfico + Tabla) ---
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        
        # 1. Gráfico
        self.chart_container = QtWidgets.QWidget()
        chart_layout = QtWidgets.QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(0, 10, 0, 10)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(5, 4), facecolor=theme.BG_MAIN)
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: transparent;")
            chart_layout.addWidget(self.canvas)
        else:
            lbl = QtWidgets.QLabel("Matplotlib no instalado. No se puede mostrar el gráfico.")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            chart_layout.addWidget(lbl)
            
        splitter.addWidget(self.chart_container)

        # 2. Tabla de Detalle
        table_container = QtWidgets.QWidget()
        table_layout = QtWidgets.QVBoxLayout(table_container)
        
        lbl_table = QtWidgets.QLabel("Detalle de Inventario Filtrado")
        lbl_table.setStyleSheet(f"font-weight: bold; color: {theme.TEXT_SECONDARY};")
        table_layout.addWidget(lbl_table)

        self.table = QtWidgets.QTableWidget()
        columns = ["SKU", "Tipo", "Cantidad", "Unidad", "Calidad", "F. Producción", "Obs"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {theme.BG_SIDEBAR};
                color: {theme.TEXT_PRIMARY};
                gridline-color: {theme.BORDER_COLOR};
                border: 1px solid {theme.BORDER_COLOR};
            }}
            QHeaderView::section {{
                background-color: #1b1b26;
                color: {theme.TEXT_SECONDARY};
                padding: 5px;
                border: none;
                font-weight: bold;
            }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        table_layout.addWidget(self.table)
        
        # Totalizador
        self.lbl_total = QtWidgets.QLabel("Total Volumen: 0.00")
        self.lbl_total.setAlignment(QtCore.Qt.AlignRight)
        self.lbl_total.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        table_layout.addWidget(self.lbl_total)

        splitter.addWidget(table_container)
        
        # Configurar tamaños iniciales del splitter
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)

    def _estilizar_input(self, widget):
        widget.setStyleSheet(f"""
            background-color: {theme.BG_INPUT}; 
            color: white; 
            border: 1px solid {theme.BORDER_COLOR}; 
            padding: 4px; 
            border-radius: 4px;
        """)

    def _on_fecha_changed(self, text):
        self.date_frame.setVisible(text == "Personalizado")

    def _load_data(self):
        try:
            self.all_rows = repo.list_inventory_rows()
            self._aplicar_filtros()
        except Exception as e:
            print(f"Error loading report data: {e}")

    def _aplicar_filtros(self):
        tipo_filtro = self.cb_tipo.currentText()
        fecha_filtro = self.cb_fecha.currentText()
        
        # Rango de fechas
        fecha_inicio = None
        fecha_fin = date.today()
        
        if fecha_filtro == "Última Semana":
            fecha_inicio = fecha_fin - timedelta(days=7)
        elif fecha_filtro == "Último Mes":
            fecha_inicio = fecha_fin - timedelta(days=30)
        elif fecha_filtro == "Personalizado":
            fecha_inicio = self.date_start.date().toPython()
            fecha_fin = self.date_end.date().toPython()

        self.filtered_rows = []
        
        for r in self.all_rows:
            # 1. Filtro Tipo
            prod_type = r.get("product_type", "")
            if tipo_filtro != "Todos los Tipos" and prod_type != tipo_filtro:
                continue
            
            # 2. Filtro Fecha (prod_date)
            f_prod_str = r.get("prod_date")
            valid_date = True
            
            if fecha_inicio: # Si hay filtro de fecha activo
                if not f_prod_str:
                    valid_date = False 
                else:
                    try:
                        # Convertir a objeto date
                        if isinstance(f_prod_str, str):
                            if "T" in f_prod_str: 
                                f_prod_str = f_prod_str.split("T")[0]
                            d_obj = date.fromisoformat(f_prod_str)
                        elif isinstance(f_prod_str, datetime):
                            d_obj = f_prod_str.date()
                        else:
                            d_obj = f_prod_str
                        
                        # Comparación segura
                        if not (fecha_inicio <= d_obj <= fecha_fin):
                            valid_date = False
                    except:
                        valid_date = False
            
            if valid_date:
                self.filtered_rows.append(r)

        # Actualizar UI
        self._actualizar_grafico()
        self._actualizar_tabla()

    def _actualizar_grafico(self):
        if not MATPLOTLIB_AVAILABLE: return

        # Agrupar datos para el Pie Chart
        totales = {}
        for r in self.filtered_rows:
            t = r.get("product_type", "Otros")
            q = float(r.get("quantity") or 0)
            totales[t] = totales.get(t, 0) + q

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(theme.BG_MAIN) 

        labels = [k for k, v in totales.items() if v > 0]
        sizes = [v for k, v in totales.items() if v > 0]
        
        if not sizes:
            ax.text(0.5, 0.5, "Sin datos", color="white", ha="center")
            ax.axis('off')
        else:
            colores = ['#32D424', '#0d6efd', '#e14eca', '#ffc107', '#0dcaf0']
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', 
                startangle=90, colors=colores,
                textprops={'color':"white"}
            )
            ax.set_title(f"Distribución (Total: {sum(sizes):.2f})", color=theme.ACCENT_COLOR, fontsize=10)

        self.canvas.draw()

    def _actualizar_tabla(self):
        self.table.setRowCount(0)
        total_volumen = 0.0
        
        for r in self.filtered_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            cant = float(r.get("quantity") or 0)
            total_volumen += cant
            
            valores = [
                str(r.get("sku", "")),
                str(r.get("product_type", "")),
                f"{cant:.2f}",
                str(r.get("unit", "")),
                str(r.get("quality", "")),
                str(r.get("prod_date", "")),
                str(r.get("obs", ""))
            ]
            
            for i, val in enumerate(valores):
                item = QtWidgets.QTableWidgetItem(val)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.table.setItem(row, i, item)

        self.lbl_total.setText(f"Total Volumen Filtrado: {total_volumen:.2f}")

    def _exportar_excel(self):
        # 1. Verificar Librería
        if not OPENPYXL_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Error de Dependencia", 
                "No se encontró la librería 'openpyxl'.\n\n"
                "Por favor instálela ejecutando:\n"
                "pip install openpyxl")
            return
            
        # 2. Verificar Datos
        if not self.filtered_rows:
            QtWidgets.QMessageBox.warning(self, "Sin Datos", 
                "No hay información visible en la tabla para exportar.\n"
                "Ajuste los filtros para ver resultados.")
            return

        # 3. Seleccionar Archivo
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Guardar Reporte Excel", "reporte_produccion.xlsx", "Excel Files (*.xlsx)"
        )
        
        if not path: 
            return # Usuario canceló

        # 4. Intentar Generar el Archivo (Bloque Seguro)
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte"
            
            # Título y Encabezados
            ws.append([f"REPORTE DE PRODUCCIÓN - {date.today()}"])
            ws.append(["SKU", "Tipo", "Cantidad", "Unidad", "Calidad", "F. Producción", "Observación"])
            
            # Estilos Simples (Menos propensos a fallar)
            header_row = ws[2]
            for cell in header_row:
                cell.font = Font(bold=True)
                
            # Datos
            for r in self.filtered_rows:
                ws.append([
                    str(r.get("sku") or ""),
                    str(r.get("product_type") or ""),
                    float(r.get("quantity") or 0),
                    str(r.get("unit") or ""),
                    str(r.get("quality") or ""),
                    str(r.get("prod_date") or ""),
                    str(r.get("obs") or "")
                ])
                
            # Guardar
            wb.save(path)
            QtWidgets.QMessageBox.information(self, "Éxito", f"Reporte guardado correctamente en:\n{path}")

        except PermissionError:
             QtWidgets.QMessageBox.critical(self, "Error de Permisos", 
                f"No se pudo guardar el archivo.\n\n"
                "¿Tiene el archivo '{os.path.basename(path)}' abierto en Excel?\n"
                "Si es así, ciérrelo e intente de nuevo.")
                
        except Exception as e:
            # Captura cualquier otro error y lo muestra
            QtWidgets.QMessageBox.critical(self, "Error Desconocido", 
                f"Ocurrió un error al generar el Excel:\n{str(e)}")