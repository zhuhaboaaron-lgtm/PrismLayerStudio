@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if exist ".venv-build\Scripts\python.exe" (
  set "PRISM_TEST_PYTHON=%~dp0.venv-build\Scripts\python.exe"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3.11+ is required on the development computer to run tests.
    exit /b 1
  )
  set "PRISM_TEST_PYTHON=python"
)
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 20+ is required on the development computer for numerical tests.
  exit /b 1
)
node --test tests\core.test.cjs
if errorlevel 1 exit /b 1
"%PRISM_TEST_PYTHON%" -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 exit /b 1
if /I "%~1"=="--packaged" (
  "%PRISM_TEST_PYTHON%" tests\run_packaged_smoke.py
  if errorlevel 1 exit /b 1
)
echo Tests passed. Use test.bat --packaged to test release\PrismLayerStudio.exe at 100/125/150/200 percent renderer scaling.
exit /b 0
