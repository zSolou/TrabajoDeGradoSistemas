from PySide6 import QtWidgets

class RespaldoScreen(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Respaldo")
        label.setAlignment(QtWidgets.Qt.AlignCenter)
        layout.addWidget(label)