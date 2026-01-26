from PySide6 import QtCore, QtWidgets, QtGui
from core import repo, theme

class InventarioScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()  # Cargar datos al iniciar

    def _setup_ui(self):
        # Layout principal
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Encabezado ---
        header = QtWidgets.QHBoxLayout()
        
        lbl_title = QtWidgets.QLabel("INVENTARIO ACTUAL")
        lbl_title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        header.addWidget(lbl_title)
        
        header.addStretch()
        
        # Buscador
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por SKU o Tipo...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.BG_INPUT};
                color: {theme.TEXT_PRIMARY};
                border: 1px solid {theme.BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        self.search_input.textChanged.connect(self._filtrar_tabla)
        header.addWidget(self.search_input)

        # Botón Exportar
        self.btn_export = QtWidgets.QPushButton("Exportar CSV")
        self.btn_export.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BTN_PRIMARY};
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #0b5ed7; }}
        """)
        # Puedes conectar la lógica de exportar aquí si la tienes
        header.addWidget(self.btn_export)

        layout.addLayout(header)

        # --- Tabla ---
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "SKU", "Producto", "Cant.", "Unidad", 
            "Largo", "Ancho", "Espesor", "Piezas", "Calidad", "Fecha Prod."
        ])
        
        # Estilo de la tabla
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {theme.BG_SIDEBAR};
                color: {theme.TEXT_PRIMARY};
                gridline-color: {theme.BORDER_COLOR};
                border: none;
            }}
            QHeaderView::section {{
                background-color: #1b1b26;
                color: {theme.TEXT_SECONDARY};
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {theme.ACCENT_COLOR};
                color: black;
            }}
        """)
        
        # Configuración de columnas
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header_view.setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers) # Solo lectura
        
        layout.addWidget(self.table)
        
        # Pie de página (Contador)
        self.lbl_status = QtWidgets.QLabel("Registros: 0")
        self.lbl_status.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        layout.addWidget(self.lbl_status)

        # Guardamos los datos crudos para filtrar
        self.all_data = []

    def refresh(self):
        """Recarga los datos desde la base de datos"""
        try:
            self.all_data = repo.list_inventory_rows() # Asegúrate de que esta función exista en repo
            self._llenar_tabla(self.all_data)
        except Exception as e:
            print(f"Error cargando inventario: {e}")

    def _llenar_tabla(self, datos):
        self.table.setRowCount(0)
        for row_data in datos:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            # Mapeo de columnas según tu repo.list_inventory_rows
            # Ajusta los índices si tu diccionario trae otras claves
            valores = [
                str(row_data.get("id", "")),
                str(row_data.get("sku", "")),
                str(row_data.get("product_type", "")), # O 'name'
                f"{row_data.get('quantity', 0):.2f}",
                str(row_data.get("unit", "")),
                str(row_data.get("largo", 0)),
                str(row_data.get("ancho", 0)),
                str(row_data.get("espesor", 0)),
                str(row_data.get("piezas", 0)),
                str(row_data.get("quality", "")),
                str(row_data.get("prod_date", ""))
            ]
            
            for col_idx, valor in enumerate(valores):
                item = QtWidgets.QTableWidgetItem(valor)
                # Alinear números a la derecha
                if col_idx in [3, 5, 6, 7, 8]: 
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                else:
                    item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)
        
        self.lbl_status.setText(f"Registros: {self.table.rowCount()}")

    def _filtrar_tabla(self, texto):
        texto = texto.lower()
        filtrados = [
            d for d in self.all_data 
            if texto in str(d.get("sku", "")).lower() or texto in str(d.get("product_type", "")).lower()
        ]
        self._llenar_tabla(filtrados)