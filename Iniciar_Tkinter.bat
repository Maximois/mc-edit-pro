@echo off
setlocal
cd /d "%~dp0"
py -3.11 "%~dp0launch_interface.py" audio_editor_full
if errorlevel 1 pause
