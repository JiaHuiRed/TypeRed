@echo off
chcp 65001 >nul
echo [1/4] Generating icon...
python make_icon.py
if errorlevel 1 (
    echo Failed to generate icon.
    pause
    exit /b 1
)

echo [2/4] Generating splash...
python make_splash.py
if errorlevel 1 (
    echo Failed to generate splash.
    pause
    exit /b 1
)

echo [3/4] Generating version info...
python make_version.py
if errorlevel 1 (
    echo Failed to generate version info.
    pause
    exit /b 1
)

echo [4/4] Building exe...
pyinstaller --onedir --windowed --noconfirm --name TypeRed --icon TypeRed.ico --version-file version.txt --add-data "frontend/style.css;frontend" --add-data "frontend/script.js;frontend" --add-data "frontend/welcome.md;frontend" --add-data "frontend/mona-loading.gif;frontend" --splash splash.png --noupx --clean main.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Done! Output: dist\TypeRed.exe
pause
