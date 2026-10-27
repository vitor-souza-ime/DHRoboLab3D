@echo off
setlocal
cd /d "%~dp0"
echo ==== DH-RoboLab 3D - Instalacao ====
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv .venv
) else (
  python -m venv .venv
)
if errorlevel 1 (
  echo ERRO: Python 3 nao encontrado. Instale Python 3.11+ 64 bits.
  pause
  exit /b 1
)
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERRO ao instalar bibliotecas. Verifique conexao de internet.
  pause
  exit /b 1
)
echo Instalacao concluida.
pause
