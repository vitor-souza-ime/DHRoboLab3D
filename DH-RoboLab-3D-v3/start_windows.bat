@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente ausente. Execute instalar_windows.bat primeiro.
  pause
  exit /b 1
)
echo ===========================================
echo DH RoboLab 3D
 echo Acesse http://127.0.0.1:5000 no navegador
 echo Pressione Ctrl+C para encerrar.
echo ===========================================
.venv\Scripts\python.exe app.py
if errorlevel 1 pause
