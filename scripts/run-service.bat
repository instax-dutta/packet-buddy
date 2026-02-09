@echo off
REM PacketBuddy Service Launcher
REM This script is used by Windows Task Scheduler to run PacketBuddy service
REM It properly sets up the environment before starting the server

REM Get the directory where this script is located (scripts folder)
set "SCRIPT_DIR=%~dp0"

REM Get project root (parent of scripts folder)
cd /d "%SCRIPT_DIR%.."
set "PROJECT_DIR=%CD%"

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Set PYTHONPATH so Python can find the src module
set "PYTHONPATH=%PROJECT_DIR%"

REM Use pythonw.exe for silent background operation
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\pythonw.exe"

REM Redirect output to log files for debugging
set "LOG_DIR=%USERPROFILE%\.packetbuddy"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Run the server module silently with output logging
"%PYTHON_EXE%" -m src.api.server > "%LOG_DIR%\stdout.log" 2> "%LOG_DIR%\stderr.log"
