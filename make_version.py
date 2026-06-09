# -*- coding: utf-8 -*-
"""从 main.py 读出 VERSION，生成 PyInstaller 版本文件"""
import re

with open('main.py', encoding='utf-8') as f:
    src = f.read()

m = re.search(r'VERSION\s*=\s*[\"\'](\d+\.\d+\.\d+)', src)
version = m.group(1) if m else '0.0.0'
parts = [int(x) for x in version.split('.')]
while len(parts) < 4:
    parts.append(0)

vs = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({parts[0]}, {parts[1]}, {parts[2]}, {parts[3]}),
    prodvers=({parts[0]}, {parts[1]}, {parts[2]}, {parts[3]}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable('040904B0',
        [StringStruct('CompanyName', ''),
         StringStruct('FileDescription', 'TypeRed Markdown Editor'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'TypeRed'),
         StringStruct('LegalCopyright', ''),
         StringStruct('OriginalFilename', 'TypeRed.exe'),
         StringStruct('ProductName', 'TypeRed'),
         StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
'''

with open('version.txt', 'w', encoding='utf-8') as f:
    f.write(vs)

print(f'Generated version.txt — v{version}')
