# core/styles.py

# Tema oscuro estilo Windows 11 (valores pensados para tu paleta)
DARK_THEME = """
QWidget {
    background-color: #0b1220;
    color: #e6eef8;
    font-family: Segoe UI, Arial;
    font-size: 10pt;
}
QFrame#card {
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    padding: 14px;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QPlainTextEdit {
    background-color: #0f1724;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 6px;
    color: #e6eef8;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #2563eb;
}
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: white;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { opacity: 0.95; }
QPushButton:disabled {
    background-color: #475569;
    color: #cbd5e1;
}
QLabel { color: #e6eef8; }
"""

# Tema claro estilo Windows 11
LIGHT_THEME = """
QWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: Segoe UI, Arial;
    font-size: 10pt;
}
QFrame#card {
    background: #ffffff;
    border-radius: 10px;
    padding: 14px;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px;
    color: #1e293b;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {
    border: 1px solid #2563eb;
}
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2563eb, stop:1 #1d4ed8);
    color: white;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover { opacity: 0.95; }
QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}
QLabel { color: #1e293b; }
"""