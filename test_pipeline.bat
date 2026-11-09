@echo off
setlocal
cd /d "%~dp0"

py -3.11 "%~dp0launch_interface.py" --prepare
if errorlevel 1 (
    pause
    exit /b 1
)

echo Asegurate de tener en ejecucion el lanzador de la interfaz que quieres probar.
".venv311\Scripts\python.exe" "%~dp0test_pipeline.py"
pause
