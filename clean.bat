@echo off
chcp 65001 >nul
echo Cleaning TypeRed build artifacts...
echo.

if exist build\ (
    rmdir /s /q build
    echo   Deleted build/
)
if exist dist\ (
    rmdir /s /q dist
    echo   Deleted dist/
)
if exist __pycache__\ (
    rmdir /s /q __pycache__
    echo   Deleted __pycache__/
)
if exist splash.png (
    del /q splash.png 2>nul
    echo   Deleted splash.png
)

echo.
echo Done! Cleaned up build artifacts.
