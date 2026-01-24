# screens/respaldo.py
import os
import subprocess
from datetime import datetime
from PySide6 import QtWidgets, QtCore

class RespaldoScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)

        # Título
        title = QtWidgets.QLabel("COPIA DE SEGURIDAD DE BASE DE DATOS")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #32D424;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Descripción
        desc = QtWidgets.QLabel(
            "Esta herramienta generará un archivo .sql con toda la información\n"
            "actual del sistema (productos, inventario, clientes).\n"
            "Guarde este archivo en un lugar seguro (disco externo o nube)."
        )
        desc.setAlignment(QtCore.Qt.AlignCenter)
        desc.setStyleSheet("font-size: 11pt; color: #ccc;")
        layout.addWidget(desc)

        # Botón Grande
        self.btn_backup = QtWidgets.QPushButton("Generar Respaldo Ahora")
        self.btn_backup.setMinimumSize(250, 60)
        self.btn_backup.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd; 
                color: white; 
                font-size: 14pt; 
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.btn_backup.clicked.connect(self._generar_respaldo)
        layout.addWidget(self.btn_backup)
        
        layout.addStretch() # Empujar todo hacia arriba/centro

    def _generar_respaldo(self):
        # CONFIGURACIÓN
        DB_NAME = "astillados_db"
        DB_USER = "postgres"
        # Si pg_dump no está en el PATH, pon la ruta completa. Ej:
        # PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe"
        PG_DUMP_PATH = "pg_dump"

        fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nombre_default = f"respaldo_{DB_NAME}_{fecha_hoy}.sql"

        archivo_destino, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Guardar Respaldo", nombre_default, "Archivos SQL (*.sql)"
        )

        if not archivo_destino:
            return

        try:
            # Configurar entorno para evitar password prompt si es local confiable
            env = os.environ.copy()
            env["PGPASSWORD"] = "" # Asumiendo que no tiene pass o está en .pgpass

            comando = [
                PG_DUMP_PATH,
                "-h", "localhost",
                "-U", DB_USER,
                "-F", "p", # Formato plano (Plain)
                "-f", archivo_destino,
                DB_NAME
            ]

            # Ocultar ventana de consola en Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            process = subprocess.Popen(
                comando, 
                env=env, 
                startupinfo=startupinfo,
                stderr=subprocess.PIPE
            )
            
            _, stderr = process.communicate()

            if process.returncode == 0:
                QtWidgets.QMessageBox.information(
                    self, "Respaldo Exitoso", 
                    f"La base de datos se ha guardado correctamente en:\n{archivo_destino}"
                )
            else:
                err_msg = stderr.decode('utf-8', errors='ignore')
                QtWidgets.QMessageBox.critical(
                    self, "Error de Respaldo", 
                    f"Hubo un problema al generar el respaldo:\n{err_msg}\n\n"
                    "Verifique que PostgreSQL esté instalado y en el PATH."
                )

        except FileNotFoundError:
             QtWidgets.QMessageBox.critical(
                self, "Error", 
                "No se encontró el comando 'pg_dump'.\n"
                "Asegúrese de instalar PostgreSQL o agregar la carpeta 'bin' al PATH de Windows."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error Inesperado", str(e))