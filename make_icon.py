# 生成 TypeRed.ico，与程序内图标一致
# v0.3.2-fix — 经典 BMP 格式 ICO，兼容 PyInstaller
import sys
import struct
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (QPainter, QPixmap, QColor, QFont,
                            QPainterPath, QLinearGradient, QImage)
from PySide6.QtCore import Qt, QPointF, QRectF
from PIL import Image

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
    r = size * 54 / 256
    path.addRoundedRect(QRectF(size*10/256, size*10/256,
                                size*236/256, size*236/256), r, r)
    p.fillPath(path, grad)
    font = QFont('Segoe UI', int(size * 100 / 256), QFont.Bold)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 230))
    p.drawText(pix.rect(), Qt.AlignCenter, 'TR')
    p.end()
    return pix.toImage()


def _align4(n: int) -> int:
    """向上对齐到 4 字节边界。"""
    return (n + 3) & ~3


def pil_to_bmp_ico_bytes(pil_img: Image.Image) -> bytes:
    """将 PIL RGBA 图像转为 ICO 经典 BMP 格式的图像数据。"""
    w, h = pil_img.size

    # PIL 像素数据 (RGBA, top-to-bottom)
    rgba = pil_img.tobytes()
    pixel_stride = w * 4                     # 32bpp 无需字节对齐
    and_row_stride = _align4((w + 7) // 8)   # 1bpp AND 掩码行对齐

    # XOR 掩码: BGRA, bottom-to-top
    xor_data = b''
    for y in range(h - 1, -1, -1):
        row_start = y * pixel_stride
        for x in range(w):
            i = row_start + x * 4
            r, g, b, a = rgba[i], rgba[i+1], rgba[i+2], rgba[i+3]
            xor_data += bytes([b, g, r, a])

    # AND 掩码: 1bpp, 0=显示像素, 1=透明, bottom-to-top
    and_data = b''
    for y in range(h - 1, -1, -1):
        row_start = y * pixel_stride
        row_bytes = bytearray(and_row_stride)
        for x in range(w):
            alpha = rgba[row_start + x * 4 + 3]
            if alpha < 128:
                byte_idx = x // 8
                bit_idx = 7 - (x % 8)
                row_bytes[byte_idx] |= (1 << bit_idx)
        and_data += bytes(row_bytes)

    # BITMAPINFOHEADER (40 bytes)
    biSize = 40
    biWidth = w
    biHeight = h * 2                       # XOR + AND 掩码高度
    biPlanes = 1
    biBitCount = 32
    biCompression = 0
    biSizeImage = pixel_stride * h + and_row_stride * h
    biXPelsPerMeter = 0
    biYPelsPerMeter = 0
    biClrUsed = 0
    biClrImportant = 0

    header = struct.pack('<IiiHHIIiiII',
                         biSize, biWidth, biHeight,
                         biPlanes, biBitCount, biCompression,
                         biSizeImage, biXPelsPerMeter,
                         biYPelsPerMeter, biClrUsed, biClrImportant)

    return header + xor_data + and_data


def make_ico(sizes, pil_images) -> bytes:
    """手动构建经典 BMP 格式的 ICO 文件。"""
    num = len(sizes)
    data_list = [pil_to_bmp_ico_bytes(img) for img in pil_images]

    header = struct.pack('<HHH', 0, 1, num)

    offset = 6 + num * 16
    entries = b''
    chunks = b''

    for i, s in enumerate(sizes):
        data = data_list[i]
        w_byte = 0 if s >= 256 else s
        h_byte = 0 if s >= 256 else s
        entry = struct.pack('<BBBBHHII',
                            w_byte, h_byte,
                            0, 0, 1, 32,
                            len(data), offset)
        entries += entry
        chunks += data
        offset += len(data)

    return header + entries + chunks


sizes = [16, 32, 48, 64, 128, 256]
images = []
for s in sizes:
    img = draw_icon(s)
    buf = img.bits().tobytes()
    pil = Image.frombytes('RGBA', (s, s), buf, 'raw', 'BGRA')
    images.append(pil)

ico_bytes = make_ico(sizes, images)

with open('TypeRed.ico', 'wb') as f:
    f.write(ico_bytes)

# 验证（先读完所有目录项，再读数据区，避免 seek 干扰）
with open('TypeRed.ico', 'rb') as f:
    hd = f.read(6)
    _, _, count = struct.unpack('<HHH', hd)
    dirs = [f.read(16) for _ in range(count)]
    print(f'TypeRed.ico 生成完毕 — {len(ico_bytes)} 字节, {count} 个尺寸:')
    for i, e in enumerate(dirs):
        w, h, _, _, _, _, sz, off = struct.unpack('<BBBBHHII', e)
        w = 256 if w == 0 else w
        h = 256 if h == 0 else h
        f.seek(off)
        bi_size = struct.unpack('<I', f.read(4))[0]
        is_classic = (bi_size == 40)
        print(f'  [{i}] {w}x{h}  {sz/1024:.1f}KB  BMP={is_classic}')
