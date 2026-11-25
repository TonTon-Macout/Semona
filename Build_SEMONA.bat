@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "SOURCE_FILE=Semona.py"
set "APP_NAME=SEMONA"
set "APP_VERSION=1.0"
set "ICON_FILE=icons\icon.ico"
set "EXE_NAME=%APP_NAME%_v%APP_VERSION%"

echo.
echo ==================== SEMONA build ====================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

if not exist "%SOURCE_FILE%" (
    echo ERROR: Source file "%SOURCE_FILE%" was not found.
    pause
    exit /b 1
)
if not exist "icons\" (
    echo ERROR: Folder "icons" was not found.
    pause
    exit /b 1
)
if not exist "%ICON_FILE%" (
    echo ERROR: Application icon "%ICON_FILE%" was not found.
    pause
    exit /b 1
)
if not exist "icons\update.png" (
    echo ERROR: "icons\update.png" was not found.
    pause
    exit /b 1
)

echo Checking Python packages...
python -c "import PyInstaller, PyQt6, serial, requests" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages are missing.
    echo Run: python -m pip install --upgrade pyinstaller PyQt6 pyserial requests
    pause
    exit /b 1
)

echo.
echo Building %EXE_NAME%.exe ...
echo All image and icon files from the icons folder will be embedded.
echo No images will be copied beside the EXE.
echo.

python -m PyInstaller --noconfirm --clean --onefile --windowed --name "%EXE_NAME%" --icon "%ICON_FILE%" --add-data "icons;icons" --hidden-import serial.tools.list_ports --log-level WARN "%SOURCE_FILE%"

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

if not exist "dist\%EXE_NAME%.exe" (
    echo ERROR: Expected EXE was not created.
    pause
    exit /b 1
)

move /Y "dist\%EXE_NAME%.exe" "." >nul
if errorlevel 1 (
    echo ERROR: Could not move the EXE to this folder.
    pause
    exit /b 1
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "%APP_NAME%.spec" 2>nul
del /q "%EXE_NAME%.spec" 2>nul
rmdir /s /q __pycache__ 2>nul

echo.
echo Build completed: %EXE_NAME%.exe
echo All files from icons are embedded inside the EXE.
echo Only settings.json, themes.json and devices.json are stored beside the EXE as user data.
echo.
pause
