@echo off
chcp 65001 >nul
echo [1/3] Generating icon...
python make_icon.py
if errorlevel 1 (
    echo Failed to generate icon.
    pause
    exit /b 1
)

echo [2/3] Generating splash...
python make_splash.py
if errorlevel 1 (
    echo Failed to generate splash.
    pause
    exit /b 1
)

echo [3/3] Building exe...
pyinstaller --onefile --windowed --name TypeRed --icon TypeRed.ico --add-data "frontend/style.css;frontend" --add-data "frontend/mona-loading.gif;frontend" --splash splash.png --noupx --clean main.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Done! Output: dist\TypeRed.exe
pause
