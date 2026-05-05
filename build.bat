@echo off
chcp 65001 >nul
echo ===========================================
echo  Public Image Collector - Build Portable
echo ===========================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Limpiar builds anteriores
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Ejecutar PyInstaller
echo Empaquetando aplicacion...
pyinstaller ^
    --name "PublicImageCollector" ^
    --onefile ^
    --windowed ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --clean ^
    --noconfirm ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: El empaquetado fallo.
    pause
    exit /b 1
)

echo.
echo ===========================================
echo  Build completado exitosamente
echo ===========================================
echo.
echo Ejecutable generado en:
echo   dist\PublicImageCollector.exe
echo.
echo Para distribuir:
echo   Copia la carpeta 'dist\PublicImageCollector.exe' a cualquier PC Windows.
echo   No requiere instalar Python.
echo.
pause
