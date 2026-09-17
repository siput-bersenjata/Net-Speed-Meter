from PySide6.QtGui import QGuiApplication, QPixmap, QPainter, QColor, QFont, QPen, QPolygon
from PySide6.QtCore import Qt, QPoint
import sys

app = QGuiApplication(sys.argv)

size = 128
pixmap = QPixmap(size, size)
pixmap.fill(Qt.GlobalColor.transparent)

painter = QPainter(pixmap)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

# Background rounded card
painter.setBrush(QColor('#0F172A'))
painter.setPen(QPen(QColor('#38BDF8'), 4))
painter.drawRoundedRect(6, 6, size - 12, size - 12, 28, 28)

# Neon arrow UP (Emerald)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor('#00E676'))
up_poly = QPolygon([
    QPoint(38, 76), QPoint(54, 40), QPoint(70, 76),
    QPoint(62, 76), QPoint(62, 96), QPoint(46, 96), QPoint(46, 76)
])
painter.drawPolygon(up_poly)

# Neon arrow DOWN (Cyan)
painter.setBrush(QColor('#00E5FF'))
down_poly = QPolygon([
    QPoint(68, 56), QPoint(84, 92), QPoint(100, 56),
    QPoint(92, 56), QPoint(92, 36), QPoint(76, 36), QPoint(76, 56)
])
painter.drawPolygon(down_poly)

painter.end()

pixmap.save('app_icon.png', 'PNG')
print('PNG saved!')

try:
    from PIL import Image
    img = Image.open('app_icon.png')
    img.save('app_icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)])
    print('ICO saved via PIL!')
except Exception as e:
    pixmap.save('app_icon.ico', 'ICO')
    print(f'ICO saved via Qt: {e}')
