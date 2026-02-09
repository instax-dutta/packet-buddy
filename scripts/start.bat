@echo off
REM PacketBuddy Service Starter
REM This starts the background monitor in headless mode

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Get project root (parent of scripts folder)
cd ..
set "PROJECT_DIR=%CD%"
cd /d "%SCRIPT_DIR%"

REM First try to start the scheduled task
schtasks /run /tn "PacketBuddy" >nul 2>&1

if %errorLevel% equ 0 (
    echo PacketBuddy service started successfully
    echo Dashboard available at: http://127.0.0.1:7373/dashboard
) else (
    REM Fallback: run directly using launcher script
    if exist "%SCRIPT_DIR%run-service.bat" (
        echo Starting PacketBuddy service directly...
        start "" "%SCRIPT_DIR%run-service.bat"
        timeout /t 3 /nobreak >nul
        echo Service started successfully
        echo Dashboard available at: http://127.0.0.1:7373/dashboard
    ) else (
        echo Error: PacketBuddy not properly installed.
        echo Please run service\windows\setup.bat first.
        pause
    )
)
