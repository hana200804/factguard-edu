@echo off
setlocal
cd /d "%~dp0"
echo FactGuard EDU - setup Python environment
py -3 -c "import sys; assert sys.version_info[:2] >= (3,11)" >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11 or newer with the Python launcher, then retry.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Setup failed. Check network access and retry.
  pause
  exit /b 1
)
echo Setup completed. Double-click run.bat to start.
pause
