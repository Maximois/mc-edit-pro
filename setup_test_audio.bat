@echo off
setlocal
cd /d "%~dp0"

py -3.11 "%~dp0launch_interface.py" --prepare
if errorlevel 1 (
    pause
    exit /b 1
)

".venv311\Scripts\python.exe" "%~dp0create_test_audio.py"
pause
