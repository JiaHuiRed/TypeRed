# author Red
# 生成 TypeRed.ico，与程序内图标一致

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPainterPath, QLinearGradient
from PySide6.QtCore import Qt, QPointF, QRectF
from PIL import Image

app = QApplication(sys.argv)
SIZES = [16, 32, 48, 64, 128, 256]


def draw_icon(size: int) -> Image.Image:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    grad.setColorAt(0.0, QColor('#5b7cf7'))
    grad.setColorAt(1.0, QColor('#8b5cf6'))
    path = QPainterPath()
    r = size * 54 / 256
    path.addRoundedRect(QRectF(size*10/256, size*10/256,
                                size*236/256, size*236/256), r, r)
    p.fillPath(path, grad)
    font = QFont('Segoe UI', int(size * 100 / 256), QFont.Bold)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 230))
    p.drawText(pix.rect(), Qt.AlignCenter, 'TR')
    p.end()
    img = pix.toImage().convertToFormat(pix.toImage().Format.Format_RGBA8888)
    return Image.frombytes('RGBA', (size, size), img.bits().tobytes())


images = [draw_icon(s) for s in SIZES]

# 用最大尺寸图保存，Pillow 自动嵌入所有尺寸
images[-1].save(
    'TypeRed.ico',
    format='ICO',
    sizes=[(s, s) for s in SIZES],
    append_images=images[:-1],
)
print(f'TypeRed.ico 生成完毕 — {len(SIZES)} 个尺寸: {SIZES}')
