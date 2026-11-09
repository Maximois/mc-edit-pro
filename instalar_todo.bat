@echo off
setlocal
cd /d "%~dp0"
title Preparar entorno Python 3.11 - MC Editor Pro

echo Preparando el entorno local de Python 3.11...
py -3.11 "%~dp0launch_interface.py" --prepare
if errorlevel 1 (
    echo.
    echo No se pudo preparar el entorno. Revisa el error anterior.
    pause
    exit /b 1
)

echo.
echo Entorno listo. Elige cualquiera de los lanzadores Iniciar_*.bat.
pause
