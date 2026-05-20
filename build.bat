@echo off
chcp 65001 >/dev/null
echo [1/2] Generating icon...
python make_icon.py
if errorlevel 1 (
    echo Failed to generate icon.
    pause
    exit /b 1
)

echo [2/2] Building exe...
pyinstaller --onefile --windowed --name TypeRed --icon TypeRed.ico --add-data "frontend/style.css;frontend" --noupx --clean main.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Done! Output: dist\TypeRed.exe
pause
