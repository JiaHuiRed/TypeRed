#260526 Red 生成 PyInstaller 启动屏图片
from PIL import Image, ImageDraw, ImageFont

W, H = 480, 280
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

for y in range(H):
    r = int(91 + (139 - 91) * y / H)
    g = int(124 + (92 - 124) * y / H)
    b = int(247 + (246 - 247) * y / H)
    draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 52)
except Exception:
    font = ImageFont.load_default()
left, top, right, bottom = draw.textbbox((0, 0), "TypeRed", font=font)
tw, th = right - left, bottom - top
draw.text(((W - tw) // 2, (H - th) // 2 - 24), "TypeRed", fill=(255, 255, 255, 235), font=font)

try:
    font2 = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 17)
except Exception:
    font2 = ImageFont.load_default()
left2, top2, right2, bottom2 = draw.textbbox((0, 0), "加载中…", font=font2)
tw2, th2 = right2 - left2, bottom2 - top2
draw.text(((W - tw2) // 2, (H - th2) // 2 + 28), "加载中…", fill=(255, 255, 255, 160), font=font2)

img.save("splash.png")
print("splash.png 生成完毕")
