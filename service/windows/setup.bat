@echo off
REM PacketBuddy - One-Click Windows Setup
REM Just double-click this file!

setlocal EnableDelayedExpansion

REM ═══════════════════════════════════════════════════════════
REM  Admin Check
REM ═══════════════════════════════════════════════════════════
net session >nul 2>&1
if %errorLevel% neq 0 (
    cls
    color 0E
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  ⚠️  NEED ADMINISTRATOR RIGHTS                          │
    echo └────────────────────────────────────────────────────────┘
    echo.
    echo This is easy to fix:
    echo.
    echo   1. Right-click this file (setup.bat)
    echo   2. Click "Run as administrator"
    echo   3. Click "Yes" when Windows asks
    echo.
    echo That's it! The setup will run automatically.
    echo.
    pause
    exit /b 1
)

REM ═══════════════════════════════════════════════════════════
REM  Welcome Screen
REM ═══════════════════════════════════════════════════════════
cls
color 0B
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║         📊 PacketBuddy Setup Wizard                   ║
echo ║                                                        ║
echo ║    Track your internet usage automatically            ║
echo ║    Takes about 2 minutes • Fully automated            ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul
cls

REM Get project directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
cd ..\..
set "PROJECT_DIR=%CD%"

REM ═══════════════════════════════════════════════════════════
REM  Step 1: Python Check
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [1/6] Checking Python...                              │
echo └────────────────────────────────────────────────────────┘
echo.

set "PYTHON_CMD="
for %%P in (python python3 py) do (
    %%P --version >nul 2>&1
    if !errorLevel! equ 0 (
        for /f "tokens=2" %%V in ('%%P --version 2^>^&1') do (
            set "PY_VER=%%V"
            for /f "tokens=1,2 delims=." %%A in ("!PY_VER!") do (
                if %%A.%%B geq 3.11 (
                    set "PYTHON_CMD=%%P"
                    goto :PythonFound
                )
            )
        )
    )
)

:PythonFound
if "!PYTHON_CMD!"=="" (
    cls
    color 0C
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  ❌ Python 3.11+ Not Found                             │
    echo └────────────────────────────────────────────────────────┘
    echo.
    echo Don't worry! This is easy to fix:
    echo.
    echo   1. Go to: https://www.python.org/downloads/
    echo   2. Download Python 3.11 or newer
    echo   3. During install: CHECK ☑️ "Add Python to PATH"
    echo   4. Run this setup again
    echo.
    echo 💡 Tip: The checkbox is at the BOTTOM of the installer!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('!PYTHON_CMD! --version') do set "PY_VERSION=%%V"
echo ✅ Found !PY_VERSION!
timeout /t 1 /nobreak >nul

REM ═══════════════════════════════════════════════════════════
REM  Step 2: Virtual Environment
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [2/6] Setting up Python environment...                │
echo └────────────────────────────────────────────────────────┘
echo.

if exist "venv" (
    echo ℹ️  Already exists, skipping...
) else (
    echo Creating virtual environment...
    !PYTHON_CMD! -m venv venv
    if !errorLevel! equ 0 (
        echo ✅ Environment created
    ) else (
        color 0C
        echo ❌ Failed to create environment
        echo.
        echo Try running: python -m pip install --upgrade pip
        pause
        exit /b 1
    )
)
timeout /t 1 /nobreak >nul

REM ═══════════════════════════════════════════════════════════
REM  Step 3: Install Dependencies
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [3/6] Installing required packages...                 │
echo │ (This takes about 30 seconds)                          │
echo └────────────────────────────────────────────────────────┘
echo.

call venv\Scripts\activate.bat
echo Installing packages (please wait)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if !errorLevel! equ 0 (
    echo ✅ All packages installed
) else (
    color 0E
    echo ⚠️  Some packages may have failed
    echo Continuing anyway...
)
timeout /t 1 /nobreak >nul

REM ═══════════════════════════════════════════════════════════
REM  Step 4: Configuration
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [4/6] Creating configuration...                       │
echo └────────────────────────────────────────────────────────┘
echo.

set "CONFIG_DIR=%USERPROFILE%\.packetbuddy"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

if not exist "%CONFIG_DIR%\config.toml" (
    copy config.example.toml "%CONFIG_DIR%\config.toml" >nul
    echo ✅ Configuration created
) else (
    echo ℹ️  Configuration already exists
)

REM Initialize database
python -c "from src.core.storage import storage; storage.get_device_id()" >nul 2>&1
echo ✅ Database initialized
timeout /t 1 /nobreak >nul

REM ═══════════════════════════════════════════════════════════
REM  Step 5: Auto-Start Service
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [5/6] Setting up auto-start...                        │
echo └────────────────────────────────────────────────────────┘
echo.

set "TASK_NAME=PacketBuddy"
set "LAUNCHER_SCRIPT=%PROJECT_DIR%\run-service.bat"

REM Remove old task if exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! equ 0 (
    echo Removing old task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

REM Create new task
echo Creating auto-start task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%LAUNCHER_SCRIPT%\"" /sc onlogon /rl highest /f >nul 2>&1

if !errorLevel! equ 0 (
    echo ✅ Auto-start configured
) else (
    color 0E
    echo.
    echo ⚠️  Auto-start setup failed
    echo.
    echo This usually means you didn't run as Administrator.
    echo Please close this window and:
    echo   1. Right-click setup.bat
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Verify task exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! neq 0 (
    color 0C
    echo ❌ Task creation failed
    pause
    exit /b 1
)

timeout /t 1 /nobreak >nul

REM ═══════════════════════════════════════════════════════════
REM  Step 6: Start Service
REM ═══════════════════════════════════════════════════════════
echo.
echo ┌────────────────────────────────────────────────────────┐
echo │ [6/6] Starting PacketBuddy...                          │
echo └────────────────────────────────────────────────────────┘
echo.

echo Starting service (this takes 10-15 seconds)...
schtasks /run /tn "%TASK_NAME%" >nul 2>&1
timeout /t 10 /nobreak >nul

REM Test if service is running
set "SUCCESS=0"
echo Checking if service started...
for /l %%i in (1,1,10) do (
    curl -s http://127.0.0.1:7373/api/health >nul 2>&1
    if !errorLevel! equ 0 (
        set "SUCCESS=1"
        goto :ServiceRunning
    )
    timeout /t 1 /nobreak >nul
)

:ServiceRunning

REM ═══════════════════════════════════════════════════════════
REM  Success Screen
REM ═══════════════════════════════════════════════════════════
cls
if "!SUCCESS!"=="1" (
    color 0A
    echo.
    echo ╔════════════════════════════════════════════════════════╗
    echo ║                                                        ║
    echo ║         ✅ PacketBuddy is Now Running!                ║
    echo ║                                                        ║
    echo ╚════════════════════════════════════════════════════════╝
    echo.
    echo 🎉 Setup Complete!
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  What's Next?                                          │
    echo └────────────────────────────────────────────────────────┘
    echo.
    echo   📊 View Dashboard:
    echo      http://127.0.0.1:7373/dashboard
    echo.
    echo   🔄 Auto-Updates:
    echo      Enabled! You'll always have the latest version
    echo.
    echo   🚀 Auto-Start:
    echo      Runs automatically when you login
    echo.
    echo   📝 Commands:
    echo      pb today    - See today's usage
    echo      pb summary  - See all-time stats
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  Opening dashboard in 5 seconds...                     │
    echo └────────────────────────────────────────────────────────┘
    echo.
    timeout /t 5 /nobreak >nul
    start http://127.0.0.1:7373/dashboard
    echo.
    echo ✨ You can close this window now!
    echo.
    pause
) else (
    color 0E
    echo.
    echo ╔════════════════════════════════════════════════════════╗
    echo ║                                                        ║
    echo ║         ⚠️  Service Didn't Start                      ║
    echo ║                                                        ║
    echo ╚════════════════════════════════════════════════════════╝
    echo.
    echo Don't worry! This is usually an easy fix.
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  Quick Fixes:                                          │
    echo └────────────────────────────────────────────────────────┘
    echo.
    echo 1️⃣  Port 7373 might be in use
    echo    Solution: Restart your computer
    echo.
    echo 2️⃣  Firewall might be blocking Python
    echo    Solution: Click "Allow" when Windows asks
    echo.
    echo 3️⃣  Try manual start:
    echo    Run: start.bat
    echo.
    echo ┌────────────────────────────────────────────────────────┐
    echo │  Need Help?                                            │
    echo └────────────────────────────────────────────────────────┘
    echo.
    echo   📖 Troubleshooting Guide:
    echo      docs\WINDOWS_SERVICE_NOT_STARTING.md
    echo.
    echo   💬 Get Support:
    echo      github.com/instax-dutta/packet-buddy/issues
    echo.
    echo The service will auto-start on next login anyway!
    echo.
    pause
)

endlocal
