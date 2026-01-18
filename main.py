# main.py
import sys
from PySide6 import QtWidgets
from screens.login import LoginScreen
from screens.main_screen import MainScreen
import core.repo as repo

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Crear la pantalla de login
    login = LoginScreen()
    w = None

    def on_success(user):
        """
        Handler llamado cuando LoginScreen emite success_signal con el usuario autenticado.
        """
        nonlocal w
        # Crear la ventana principal pasando el usuario actual
        w = MainScreen(current_user=user)
        try:
            # Cargar inventario inicial desde la BD
            w.inventario.refresh_from_db(repo)
        except Exception as e:
            QtWidgets.QMessageBox.warning(None, "Advertencia", f"No se pudo cargar inventario: {e}")
        w.show()
        login.close()

    # Conectar la señal de login exitoso
    login.success_signal.connect(on_success)

    # Mostrar login
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()