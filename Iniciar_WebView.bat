@echo off
setlocal
cd /d "%~dp0"
py -3.11 "%~dp0launch_interface.py" app_desktop_lite
if errorlevel 1 pause
