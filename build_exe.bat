@echo off
title Build Standalone EXE
color 0A
echo.
echo  ============================================
echo    Building Standalone EXE with PyInstaller
echo    Redundant File Remover  v3.1
echo  ============================================
echo.

pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo [ERROR] Could not install PyInstaller.
    pause & exit /b 1
)

:: Use the .spec file so all feature sub-packages + assets are bundled correctly
python -m PyInstaller --clean RedundantFileRemover.spec

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
