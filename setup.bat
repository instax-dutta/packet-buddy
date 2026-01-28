@echo off
REM PacketBuddy - Root Setup Redirector
REM This script makes it easy to install from the root folder.

setlocal

echo ═══════════════════════════════════════════════════════════
echo   📊 PacketBuddy - Easy Installation
echo ═══════════════════════════════════════════════════════════
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Please:
    echo 1. Right-click this file (setup.bat)
    echo 2. Click "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Determine OS and run appropriate setup
if exist "service\windows\setup.bat" (
    echo Detected Windows. Launching setup...
    call "service\windows\setup.bat"
) else (
    echo [ERROR] Setup script not found at service\windows\setup.bat
    pause
    exit /b 1
)

endlocal
