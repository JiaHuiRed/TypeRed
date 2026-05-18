# 生成 TypeRed.ico，与程序内图标一致
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (QPainter, QPixmap, QColor, QFont,
                            QPainterPath, QLinearGradient, QImage)
from PySide6.QtCore import Qt, QPointF, QRectF

app = QApplication(sys.argv)

def draw_icon(size):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    grad.setColorAt(0.0, QColor('#5b7cf7'))
    grad.setColorAt(1.0, QColor('#8b5cf6'))
    path = QPainterPath()
    r = size * 54 / 256  # 圆角比例
    path.addRoundedRect(QRectF(size*10/256, size*10/256,
                                size*236/256, size*236/256), r, r)
    p.fillPath(path, grad)
    font = QFont('Segoe UI', int(size * 100 / 256), QFont.Bold)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 230))
    p.drawText(pix.rect(), Qt.AlignCenter, 'TR')
    p.end()
    return pix.toImage()

from PIL import Image
import io

sizes = [16, 32, 48, 64, 128, 256]
images = []
for s in sizes:
    img = draw_icon(s)
    buf = img.bits().tobytes()
    pil = Image.frombytes('RGBA', (s, s), buf, 'raw', 'BGRA')
    images.append(pil)

images[0].save('TypeRed.ico', format='ICO',
               sizes=[(s, s) for s in sizes],
               append_images=images[1:])
print('TypeRed.ico 生成完毕')
