import sys
from PySide6 import QtWidgets
from screens.login import LoginScreen
from screens.main_screen import MainScreen
import core.repo as repo
from core.theme import ThemeManager

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Aplicar tema desde el inicio (unificado)
    ThemeManager(app)

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
        
        # NOTA: MainScreen ya carga los datos automáticamente al iniciar
        # (en su constructor llama a _navigate(0) -> refresh()), 
        # por lo que no necesitamos llamar a nada manualmente aquí.
        
        w.show()
        login.close()

    # Conectar la señal de login exitoso
    login.success_signal.connect(on_success)

    # Mostrar login
    login.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()