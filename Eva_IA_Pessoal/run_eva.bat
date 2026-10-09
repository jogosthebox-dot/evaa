@echo off
cd /d "%~dp0"

echo Iniciando Eva...
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: ambiente Python nao encontrado.
    pause
    exit /b
)

start "" ".venv\Scripts\python.exe" "Main.py"

exit