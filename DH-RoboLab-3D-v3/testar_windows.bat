@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute instalar_windows.bat primeiro.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install pytest
.venv\Scripts\python.exe -m pytest -q
pause
