import sys
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

lbl = QLabel("Testing Window Flags and Opacity")
lbl.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
lbl.setStyleSheet("background: rgba(20, 22, 28, 0.9); color: white; padding: 20px;")
lbl.resize(200, 50)
lbl.move(500, 500)
lbl.show()

sys.exit(app.exec())
