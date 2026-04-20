@echo off
title Redundant File Remover — Installer
color 0B
echo.
echo  ============================================
echo    REDUNDANT FILE REMOVER  v3.1  Installer
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found!
    echo  Please install Python 3.10+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  [OK] Python found.
echo.

:: Install dependencies
echo  Installing dependencies (PyQt6 is ~100 MB, this may take a few minutes)...
echo  You should see download progress below:
echo.
pip install -r requirements.txt --progress-bar on
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to install dependencies.
    echo  Try running this as Administrator, or run manually:
    echo    pip install PyQt6 send2trash
    pause
    exit /b 1
)

echo.
echo  [OK] Dependencies installed.
echo.

:: Create Desktop shortcut pointing to main.py
echo  Creating Desktop shortcut...
powershell -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$sc = $ws.CreateShortcut([System.IO.Path]::Combine($desktop, 'Redundant File Remover.lnk')); " ^
  "$sc.TargetPath = 'pythonw'; " ^
  "$sc.Arguments = '\"%~dp0main.py\"'; " ^
  "$sc.WorkingDirectory = '%~dp0'; " ^
  "$sc.Description = 'Find and remove duplicate files safely'; " ^
  "$sc.IconLocation = '%~dp0assets\logo.ico'; " ^
  "$sc.Save()"

echo  [OK] Desktop shortcut created!
echo.
echo  ============================================
echo    Installation complete!
echo    Double-click the shortcut on your Desktop
echo    to launch the app anytime.
echo  ============================================
echo.
pause
