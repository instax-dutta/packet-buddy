@echo off
REM PacketBuddy - Root Setup Redirector
REM This script makes it easy to install from the root folder.

setlocal

REM Change to the directory where this script is located
cd /d "%~dp0"

echo ===========================================================
echo   PacketBuddy - Easy Installation
echo ===========================================================
echo.

REM Just call the Windows setup script - it handles admin check itself
if exist "service\windows\setup.bat" (
    echo Launching Windows setup...
    echo.
    call "service\windows\setup.bat"
) else (
    echo [ERROR] Setup script not found at service\windows\setup.bat
    echo Current directory: %CD%
    pause
    exit /b 1
)

endlocal
