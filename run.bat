@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first to install dependencies.
  pause
  exit /b 1
)
echo FactGuard EDU - open http://127.0.0.1:8501 in your browser
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
if errorlevel 1 pause
