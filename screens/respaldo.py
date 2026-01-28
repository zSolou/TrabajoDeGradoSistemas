import os
import sys
import subprocess
from datetime import datetime
from PySide6 import QtWidgets, QtCore
from core import theme

class RespaldoScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(25)

        # Icono o Título Grande
        title = QtWidgets.QLabel("COPIA DE SEGURIDAD")
        title.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: {theme.ACCENT_COLOR};")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Descripción
        desc = QtWidgets.QLabel(
            "Guarda una copia completa de tu base de datos (Productos, Clientes, Inventario).\n"
            "El archivo generado (.sql) puede usarse para restaurar el sistema en otra PC."
        )
        desc.setAlignment(QtCore.Qt.AlignCenter)
        desc.setStyleSheet(f"font-size: 12pt; color: {theme.TEXT_SECONDARY};")
        layout.addWidget(desc)

        # Contenedor del Botón
        btn_container = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 20, 0, 20)
        
        self.btn_backup = QtWidgets.QPushButton("  GENERAR RESPALDO AHORA  ")
        self.btn_backup.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_backup.setMinimumHeight(60)
        self.btn_backup.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.BTN_PRIMARY}; 
                color: white; 
                font-size: 14pt; 
                font-weight: bold;
                border-radius: 8px;
                padding: 10px 30px;
            }}
            QPushButton:hover {{ background-color: #0b5ed7; }}
            QPushButton:pressed {{ background-color: #0a58ca; }}
        """)
        self.btn_backup.clicked.connect(self._generar_respaldo)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_backup)
        btn_layout.addStretch()
        
        layout.addWidget(btn_container)
        layout.addStretch()

    def _find_pg_dump(self):
        """Intenta localizar el ejecutable pg_dump en el sistema."""
        # 1. Si está en el PATH global
        #return "pg_dump"
        
        # NOTA: Si sigue fallando, descomenta estas líneas y pon TU ruta real:
        return r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe"

    def _generar_respaldo(self):
        DB_NAME = "astillados_db"
        DB_USER = "postgres"
        
        # Nombre sugerido
        fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_archivo = f"respaldo_astillados_{fecha}.sql"
        
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Guardar Respaldo SQL", nombre_archivo, "SQL Files (*.sql)"
        )
        
        if not path: return

        # Preparar comando
        pg_dump_cmd = self._find_pg_dump()
        
        # Configurar entorno (Password vacía para evitar prompt)
        env = os.environ.copy()
        env["PGPASSWORD"] = "" # Asumiendo acceso confiable local

        comando = [
            pg_dump_cmd,
            "-h", "localhost",
            "-U", DB_USER,
            "-F", "p", # Formato plano (Plain Text)
            "-f", path,
            DB_NAME
        ]

        # Ejecutar
        try:
            # Ocultar ventana de consola en Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                comando, 
                env=env, 
                startupinfo=startupinfo,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE # Evitar bloqueo si pide input
            )
            
            _, stderr = process.communicate()

            if process.returncode == 0:
                QtWidgets.QMessageBox.information(
                    self, "Respaldo Exitoso", 
                    f"La base de datos se ha guardado correctamente en:\n\n{path}"
                )
            else:
                err_msg = stderr.decode('utf-8', errors='ignore')
                # Filtramos advertencias comunes que no son errores fatales
                if "version mismatch" in err_msg and os.path.exists(path) and os.path.getsize(path) > 0:
                     QtWidgets.QMessageBox.information(
                        self, "Aviso", 
                        f"El respaldo se creó, pero hubo advertencias de versión:\n{path}"
                    )
                else:
                    QtWidgets.QMessageBox.critical(
                        self, "Error de Respaldo", 
                        f"El proceso falló. Detalles técnicos:\n\n{err_msg}\n\n"
                        "Posible solución: Verifica que PostgreSQL esté corriendo y no tengas tablas bloqueadas."
                    )

        except FileNotFoundError:
            QtWidgets.QMessageBox.critical(
                self, "Error: pg_dump no encontrado", 
                "No se encontró el comando 'pg_dump'.\n"
                "Asegúrate de que PostgreSQL está instalado y la carpeta 'bin' está en el PATH de Windows."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error Inesperado", str(e))