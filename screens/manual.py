from PySide6 import QtCore, QtWidgets, QtGui
from core import theme

class ManualScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QtWidgets.QLabel("MANUAL DE USUARIO Y PROCEDIMIENTOS")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 22pt; font-weight: bold; color: {theme.ACCENT_COLOR}; margin-bottom: 10px;")
        layout.addWidget(title)

        # Visor de Texto con Formato HTML
        self.viewer = QtWidgets.QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setStyleSheet(f"""
            QTextEdit {{ 
                background-color: {theme.BG_INPUT}; 
                color: {theme.TEXT_PRIMARY}; 
                border: 1px solid {theme.BORDER_COLOR}; 
                border-radius: 8px; 
                padding: 15px; 
                font-size: 11pt; 
                line-height: 1.5;
            }}
        """)
        
        # Contenido del Manual (HTML Básico)
        manual_content = f"""
        <h2 style="color: {theme.ACCENT_COLOR}">1. Introducción</h2>
        <p>Bienvenido al <b>Sistema de Gestión de Inventario y Trazabilidad</b>. Este software permite controlar el ciclo completo de producción maderera, desde el aserrío hasta el despacho al cliente.</p>
        
        <hr>
        
        <h2 style="color: {theme.ACCENT_COLOR}">2. Módulo: Registrar Producción</h2>
        <p>Aquí se ingresan los nuevos lotes de madera al sistema (Entradas).</p>
        <ul>
            <li><b>Producto:</b> Seleccione el tipo (Tablas, Machihembrado, etc.).</li>
            <li><b>Lote:</b> Ingrese el número de lote físico (1-3 dígitos). El sistema validará que no exista previamente.</li>
            <li><b>Medidas:</b> Puede usar dimensiones estándar predefinidas o ingresar medidas personalizadas.</li>
            <li><b>Cantidades:</b> Ingrese la cantidad en <b>Bultos</b>. El sistema calculará las piezas totales automáticamente.</li>
            <li><b>Validación:</b> No se permite registrar duplicados exactos (mismo lote y producto).</li>
        </ul>

        <hr>

        <h2 style="color: {theme.ACCENT_COLOR}">3. Módulo: Inventario (Existencias)</h2>
        <p>Visualice el estado actual del patio.</p>
        <ul>
            <li><b>Búsqueda:</b> Use la barra superior para filtrar por Lote o SKU.</li>
            <li><b>Dar de Baja:</b> Si un producto se daña o pierde, use el botón <i>"Dar de Baja"</i>. Esto pondrá el stock en 0 y cambiará su estado a "BAJA", pero mantendrá el historial.</li>
            <li><b>Ver Agotados:</b> Marque la casilla "Mostrar Agotados" para ver el historial de productos que ya no tienen stock.</li>
            <li><b>Excel:</b> Exporte la tabla actual a formato Excel (.xlsx) con el botón verde.</li>
        </ul>

        <hr>

        <h2 style="color: {theme.ACCENT_COLOR}">4. Módulo: Despacho (Salidas)</h2>
        <p>Gestione la venta y salida de mercancía.</p>
        <ul>
            <li><b>Selección:</b> Presione "Buscar Lote" para elegir qué producto saldrá del inventario.</li>
            <li><b>Cliente:</b> Seleccione el destino. Si no existe, créelo en el módulo "Clientes".</li>
            <li><b>Guía:</b> Ingrese el número de guía de transporte (SADA/INSAI) para la trazabilidad.</li>
            <li><b>Validación de Fechas:</b> El sistema <b>bloqueará</b> el despacho si intenta sacar un producto con fecha anterior a su producción.</li>
        </ul>

        <hr>

        <h2 style="color: {theme.ACCENT_COLOR}">5. Módulo: Reportes</h2>
        <p>Analice la productividad y movimientos.</p>
        <ul>
            <li><b>Pestaña Producción:</b> Vea qué se fabricó en un periodo. Filtre por Calidad y Producto.</li>
            <li><b>Pestaña Despachos:</b> Vea qué salió, con qué guía y a qué cliente. Filtre por Nro. de Guía.</li>
            <li><b>Pestaña Lotes:</b> Rastree un rango específico de lotes (Ej: del 100 al 200).</li>
            <li><b>Gráficas:</b> Visualice la distribución porcentual de sus movimientos.</li>
            <li><b>Botón "Todos":</b> Ajusta las fechas para ver el historial histórico completo.</li>
        </ul>

        <hr>

        <h2 style="color: {theme.ACCENT_COLOR}">6. Módulo: Clientes</h2>
        <p>Gestione su cartera de clientes.</p>
        <ul>
            <li><b>Registro:</b> Ingrese Razón Social, RIF/Cédula y contacto.</li>
            <li><b>Bloqueo:</b> Puede desactivar clientes morosos o inactivos sin borrarlos del historial.</li>
        </ul>
        
        <br>
        <p><i>Para soporte técnico o restauración de base de datos, contacte al administrador del sistema.</i></p>
        """
        
        self.viewer.setHtml(manual_content)
        layout.addWidget(self.viewer)