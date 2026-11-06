@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.11+ required.
  pause
  exit /b 1
)
py -3 -m venv .venv-build
if errorlevel 1 goto fail
call .venv-build\Scripts\activate.bat
python -m pip install pyinstaller
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --clean --onefile --console --name PrismLayerStudioBrowser --add-data "app;app" server.py
if errorlevel 1 goto fail
echo Done: dist\PrismLayerStudioBrowser.exe
pause
exit /b 0
:fail
echo Build failed.
pause
exit /b 1
