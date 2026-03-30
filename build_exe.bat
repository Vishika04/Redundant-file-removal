@echo off
title Build Standalone EXE
color 0A
echo.
echo  ============================================
echo    Building Standalone EXE with PyInstaller
echo  ============================================
echo.

pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo [ERROR] Could not install PyInstaller.
    pause & exit /b 1
)

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "RedundantFileRemover" ^
    --icon "assets\logo.ico" ^
    --add-data "README.md;." ^
    --add-data "assets\*;assets" ^
    "%~dp0redundant_file_remover.py"

if %errorlevel% equ 0 (
    echo.
    echo  [OK] Build successful!
    echo  Find your EXE in: %~dp0dist\RedundantFileRemover.exe
    echo  Share that single file — no Python needed on target machine.
) else (
    echo.
    echo  [ERROR] Build failed. Check output above.
)
echo.
pause
