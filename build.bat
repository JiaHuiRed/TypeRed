@echo off
chcp 65001 >nul
echo [1/3] Generating icon...
py -3.14 make_icon.py
if errorlevel 1 (
    echo Failed to generate icon.
    pause
    exit /b 1
)

echo [2/3] Generating version info...
py -3.14 make_version.py
if errorlevel 1 (
    echo Failed to generate version info.
    pause
    exit /b 1
)

echo [3/3] Building exe...
py -3.14 -m PyInstaller --distpath dist --workpath build --noconfirm --clean TypeRed.spec
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

rem PyInstaller can pick up an incompatible ICU DLL from the build machine's PATH.
rem PySide6 uses the Windows ICU on this target, so remove only those accidental copies.
if exist "dist\TypeRed\_internal\icuuc.dll" del /q "dist\TypeRed\_internal\icuuc.dll"
if exist "dist\TypeRed\_internal\icudt78.dll" del /q "dist\TypeRed\_internal\icudt78.dll"

echo.
echo Done! Output: dist\TypeRed\TypeRed.exe
pause
