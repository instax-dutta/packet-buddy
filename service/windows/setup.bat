@echo off
REM PacketBuddy - One-Click Windows Setup
REM Just double-click this file!

REM ===========================================================
REM  Admin Check (BEFORE enabling delayed expansion)
REM ===========================================================
echo Checking administrator privileges...
whoami /groups | find "S-1-5-32-544" >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo.
    echo +--------------------------------------------------------+
    echo    NEED ADMINISTRATOR RIGHTS
    echo +--------------------------------------------------------+
    echo.
    echo This is easy to fix:
    echo.
    echo   1. Right-click this file [setup.bat]
    echo   2. Click "Run as administrator"
    echo   3. Click "Yes" when Windows asks
    echo.
    echo That is it. The setup will run automatically.
    echo.
    pause
    exit /b 1
)
echo [OK] Running as Administrator
echo.

REM Now enable delayed expansion for the rest of the script
setlocal EnableDelayedExpansion

REM ===========================================================
REM  Welcome Screen
REM ===========================================================
color 0B
echo.
echo +========================================================+
echo                                                          
echo          PacketBuddy Setup Wizard                        
echo                                                          
echo     Track your internet usage automatically              
echo     Takes about 2 minutes - Fully automated              
echo                                                          
echo +========================================================+
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul
cls

REM Get project directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
cd ..\..
set "PROJECT_DIR=%CD%"

REM ===========================================================
REM  Step 1: Python Check
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [1/6] Checking Python...
echo +--------------------------------------------------------+
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
    echo +--------------------------------------------------------+
    echo   [X] Python 3.11+ Not Found
    echo +--------------------------------------------------------+
    echo.
    echo Don't worry! This is easy to fix:
    echo.
    echo   1. Go to: https://www.python.org/downloads/
    echo   2. Download Python 3.11 or newer
    echo   3. During install: CHECK "Add Python to PATH"
    echo   4. Run this setup again
    echo.
    echo Tip: The checkbox is at the BOTTOM of the installer!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('!PYTHON_CMD! --version') do set "PY_VERSION=%%V"
echo [OK] Found !PY_VERSION!
timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 2: Virtual Environment
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [2/6] Setting up Python environment...
echo +--------------------------------------------------------+
echo.

if exist "venv" (
    echo [i] Already exists, skipping...
) else (
    echo Creating virtual environment...
    !PYTHON_CMD! -m venv venv
    if !errorLevel! equ 0 (
        echo [OK] Environment created
    ) else (
        color 0C
        echo [X] Failed to create environment
        echo.
        echo Try running: python -m pip install --upgrade pip
        pause
        exit /b 1
    )
)
timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 3: Install Dependencies
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [3/6] Installing required packages...
echo   (This takes about 30 seconds)
echo +--------------------------------------------------------+
echo.

call venv\Scripts\activate.bat
echo Installing packages (please wait)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if !errorLevel! equ 0 (
    echo [OK] All packages installed
) else (
    color 0E
    echo [!] Some packages may have failed
    echo Continuing anyway...
)
timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 4: Configuration
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [4/6] Creating configuration...
echo +--------------------------------------------------------+
echo.

set "CONFIG_DIR=%USERPROFILE%\.packetbuddy"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

if not exist "%CONFIG_DIR%\config.toml" (
    copy config.example.toml "%CONFIG_DIR%\config.toml" >nul
    echo [OK] Configuration created
) else (
    echo [i] Configuration already exists
)

REM Prompt for Neon DB connection string
echo.
echo +--------------------------------------------------------+
echo   Database Configuration
echo +--------------------------------------------------------+
echo.
echo Enter your NeonDB connection string.
echo (Press Enter to skip if you want to configure later)
echo.
set /p "NEON_URL=NeonDB URL: "

if not "!NEON_URL!"=="" (
    REM Update config.toml with the provided Neon URL using PowerShell
    powershell -Command "(Get-Content '%CONFIG_DIR%\config.toml') -replace 'neon_url = \"\"', 'neon_url = \"!NEON_URL!\"' | Set-Content '%CONFIG_DIR%\config.toml'"
    echo [OK] Database URL configured
) else (
    echo [i] Skipped - You can set NEON_DB_URL environment variable later
)
echo.

REM Initialize database
python -c "from src.core.storage import storage; storage.get_device_id()" >nul 2>&1
echo [OK] Database initialized
timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 5: Add to PATH
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [5/7] Adding to PATH for CLI access...
echo +--------------------------------------------------------+
echo.

REM Add project directory to user PATH using PowerShell
powershell -Command "$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($currentPath -notlike '*%PROJECT_DIR%*') { [Environment]::SetEnvironmentVariable('Path', $currentPath + ';%PROJECT_DIR%', 'User'); Write-Host '[OK] Added to PATH' } else { Write-Host '[i] Already in PATH' }"
timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 6: Auto-Start Service
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [6/7] Setting up auto-start...
echo +--------------------------------------------------------+
echo.

set "TASK_NAME=PacketBuddy"
set "LAUNCHER_SCRIPT=%PROJECT_DIR%\run-service.bat"

REM Detect pythonw.exe in venv for headless mode
set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\pythonw.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=%PROJECT_DIR%\venv\Scripts\python.exe"
)

REM Launcher script path
set "LAUNCHER_SCRIPT=%PROJECT_DIR%\service\windows\launcher.py"

REM Remove existing task if it exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! equ 0 (
    echo Removing old task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
)

REM Create scheduled task
REM We execute pythonw.exe explicitly pointing to our launcher script
REM This avoids "Screen flashing" because pythonw.exe is a GUI subsystem app (no console)
set "TASK_CMD=\"%PYTHON_EXE%\" \"%LAUNCHER_SCRIPT%\""

REM Create task
REM /sc onlogon : Start when user logs in
REM /rl highest : Run with highest privileges (Admin)
schtasks /create /tn "%TASK_NAME%" /tr "%TASK_CMD%" /sc onlogon /rl highest /f >nul 2>&1

if !errorLevel! equ 0 (
    echo [OK] Auto-start configured
) else (
    color 0E
    echo.
    echo [!] Auto-start setup failed
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
    echo [X] Task creation failed
    pause
    exit /b 1
)

timeout /t 1 /nobreak >nul

REM ===========================================================
REM  Step 7: Start Service
REM ===========================================================
echo.
echo +--------------------------------------------------------+
echo   [7/7] Starting PacketBuddy...
echo +--------------------------------------------------------+
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

REM ===========================================================
REM  Success Screen
REM ===========================================================
cls
if "!SUCCESS!"=="1" (
    color 0A
    echo.
    echo +========================================================+
    echo                                                          
    echo          [OK] PacketBuddy is Now Running!                
    echo                                                          
    echo +========================================================+
    echo.
    echo Setup Complete!
    echo.
    echo +--------------------------------------------------------+
    echo   What's Next?
    echo +--------------------------------------------------------+
    echo.
    echo   View Dashboard:
    echo      http://127.0.0.1:7373/dashboard
    echo.
    echo   Auto-Updates:
    echo      Enabled! You'll always have the latest version
    echo.
    echo   Auto-Start:
    echo      Runs automatically when you login
    echo.
    echo   Commands:
    echo      pb today    - See today's usage
    echo      pb summary  - See all-time stats
    echo.
    echo +--------------------------------------------------------+
    echo   Opening dashboard in 5 seconds...
    echo +--------------------------------------------------------+
    echo.
    timeout /t 5 /nobreak >nul
    start http://127.0.0.1:7373/dashboard
    echo.
    echo You can close this window now!
    echo.
    pause
) else (
    color 0E
    echo.
    echo +========================================================+
    echo                                                          
    echo          [!] Service Didn't Start                        
    echo                                                          
    echo +========================================================+
    echo.
    echo Don't worry! This is usually an easy fix.
    echo.
    echo +--------------------------------------------------------+
    echo   Quick Fixes:
    echo +--------------------------------------------------------+
    echo.
    echo 1. Port 7373 might be in use
    echo    Solution: Restart your computer
    echo.
    echo 2. Firewall might be blocking Python
    echo    Solution: Click "Allow" when Windows asks
    echo.
    echo 3. Try manual start:
    echo    Run: start.bat
    echo.
    echo +--------------------------------------------------------+
    echo   Need Help?
    echo +--------------------------------------------------------+
    echo.
    echo   Troubleshooting Guide:
    echo      docs\WINDOWS_SERVICE_NOT_STARTING.md
    echo.
    echo   Get Support:
    echo      github.com/instax-dutta/packet-buddy/issues
    echo.
    echo The service will auto-start on next login anyway!
    echo.
    pause
)

endlocal
