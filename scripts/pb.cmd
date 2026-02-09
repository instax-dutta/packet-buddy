@echo off
REM PacketBuddy CLI Shortcut for Windows
REM This allows you to use 'pb' from anywhere

REM Get the directory where this script is located (scripts folder)
set SCRIPT_DIR=%~dp0

REM Get project root (parent of scripts folder)
cd /d "%SCRIPT_DIR%.."
set PROJECT_DIR=%CD%

REM Activate venv and run CLI
cd /d "%PROJECT_DIR%"
call "%PROJECT_DIR%\venv\Scripts\activate.bat" >nul 2>&1
set PYTHONPATH=%PROJECT_DIR%;%PYTHONPATH%
python -m src.cli.main %*
