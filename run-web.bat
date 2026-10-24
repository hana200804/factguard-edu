@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the Python environment and install requirements-web.txt first.
  pause
  exit /b 1
)
echo FactGuard EDU Web: http://127.0.0.1:8765
echo Keep this window open while using the service.
".venv\Scripts\python.exe" scripts\serve_web.py --port 8765
if errorlevel 1 pause
