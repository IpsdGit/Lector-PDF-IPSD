@echo off
title Renombrador de PDFs V3.0 - IPSD/UNAH
color 0A
echo.
echo ====================================================================
echo  RENOMBRADOR DE PDFs V3.0
echo  Instituto de Pesca y Salud Digital (IPSD) - UNAH
echo ====================================================================
echo.
echo  [*] Iniciando aplicacion...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe .\Cuerpo\renombrador_pdfs_v3.py

if errorlevel 1 (
    echo.
    echo  [ERROR] La aplicacion termino con errores.
    echo  Revisa los logs para mas detalles.
    echo.
    pause
    exit /b 1
)

echo.
echo  [OK] Aplicacion cerrada correctamente.
echo.
pause
