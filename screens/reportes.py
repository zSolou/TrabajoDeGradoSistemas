# screens/reportes.py
from PySide6 import QtCore, QtWidgets

class ReportesScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel("Reportes")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16pt;")
        l.addWidget(lbl)