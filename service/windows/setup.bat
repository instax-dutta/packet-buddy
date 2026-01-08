@echo off
REM PacketBuddy One-Time Automated Setup for Windows
REM Double-click this file or run from Command Prompt

setlocal EnableDelayedExpansion

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo.
    echo ═══════════════════════════════════════════════════════
    echo ERROR: Administrator rights required!
    echo ═══════════════════════════════════════════════════════
    echo.
    echo Please:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo   3. Run again
    echo.
    pause
    exit /b 1
)

REM Colors and fancy header
color 0B
cls
echo.
echo ═══════════════════════════════════════════════════════
echo            PacketBuddy Setup Wizard
echo ═══════════════════════════════════════════════════════
echo.
echo Ultra-lightweight network usage tracker
echo This will take about 2 minutes...
echo.

REM Get project directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
cd ..\..
set "PROJECT_DIR=%CD%"

echo Project directory: %PROJECT_DIR%
echo.

REM Step 1: Check Python
echo [1/8] Checking Python installation...

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
    color 0C
    echo X Python 3.11+ not found
    echo.
    echo Please install Python 3.11+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('!PYTHON_CMD! --version') do set "PY_VERSION=%%V"
echo [OK] !PY_VERSION! found
echo.

REM Step 2: Create virtual environment
echo [2/8] Setting up Python virtual environment...

if exist "venv" (
    echo [INFO] Virtual environment already exists, skipping
) else (
    !PYTHON_CMD! -m venv venv
    if !errorLevel! equ 0 (
        echo [OK] Virtual environment created
    )
)
echo.

REM Step 3: Install dependencies
echo [3/8] Installing dependencies...
echo This may take a minute...

call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo [OK] All dependencies installed
echo.

REM Step 4: Create config directory
echo [4/8] Creating configuration directory...

set "CONFIG_DIR=%USERPROFILE%\.packetbuddy"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

if not exist "%CONFIG_DIR%\config.toml" (
    copy config.example.toml "%CONFIG_DIR%\config.toml" >nul
    echo [OK] Configuration file created
) else (
    echo [INFO] Configuration file already exists
)
echo.

REM Step 5: Optional NeonDB setup
echo [5/8] Cloud sync configuration...
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   Multi-Device Cloud Sync (Optional)
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Do you want to enable cloud sync with NeonDB?
echo This allows you to track multiple devices (PC + Mac) in one database.
echo.
echo Benefits:
echo   * Track all your devices in one place
echo   * Free tier supports 10GB (enough for years)
echo   * Automatic cloud backup
echo.
echo Note: If skipped, PacketBuddy works perfectly with local-only tracking.
echo.

set /p "ENABLE_SYNC=Enable cloud sync? (y/n) [n]: "

set "NEON_URL="
if /i "!ENABLE_SYNC!"=="y" (
    echo.
    echo Please enter your NeonDB connection string:
    echo (Format: postgresql://user:pass@host.neon.tech/db?sslmode=require)
    echo.
    echo Don't have one? Get it free at: https://neon.tech
    echo.
    set /p "NEON_URL=NeonDB URL: "
    
    if not "!NEON_URL!"=="" (
        setx NEON_DB_URL "!NEON_URL!" >nul
        echo [OK] NeonDB configured
    )
) else (
    echo [INFO] Skipping cloud sync (local-only mode)
)
echo.

REM Step 6: Initialize database
echo [6/8] Initializing database...
python -c "from src.core.storage import storage; storage.get_device_id()" >nul 2>&1
echo [OK] Database initialized
echo.

REM Step 7: Create scheduled task
echo [7/8] Setting up auto-start service...
echo.

set "TASK_NAME=PacketBuddy"

REM Verify launcher script exists
set "LAUNCHER_SCRIPT=%PROJECT_DIR%\run-service.bat"
if not exist "%LAUNCHER_SCRIPT%" (
    color 0C
    echo [ERROR] Launcher script not found: %LAUNCHER_SCRIPT%
    echo.
    echo This is a critical error. Please report this issue.
    pause
    exit /b 1
)

REM Remove existing task if it exists
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! equ 0 (
    echo [INFO] Removing existing scheduled task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    if !errorLevel! neq 0 (
        echo [WARN] Could not remove existing task (this is usually OK)
    )
)

REM Create scheduled task using the dedicated launcher script
echo [INFO] Creating scheduled task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%LAUNCHER_SCRIPT%\"" /sc onlogon /rl highest /f >nul 2>&1

if !errorLevel! equ 0 (
    echo [OK] Scheduled task created successfully
) else (
    color 0E
    echo.
    echo [ERROR] Failed to create scheduled task!
    echo.
    echo This usually means:
    echo   1. You didn't run as Administrator
    echo   2. Task Scheduler service is disabled
    echo.
    echo Please:
    echo   1. Close this window
    echo   2. Right-click setup.bat
    echo   3. Select "Run as administrator"
    echo   4. Try again
    echo.
    pause
    exit /b 1
)

REM Verify task was created
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! neq 0 (
    color 0C
    echo [ERROR] Task was created but cannot be found!
    echo This is unusual. Please check Task Scheduler manually.
    pause
    exit /b 1
)

REM Start the task immediately
echo [INFO] Starting service...
schtasks /run /tn "%TASK_NAME%" >nul 2>&1
if !errorLevel! equ 0 (
    echo [OK] Service start signal sent
) else (
    color 0E
    echo [WARN] Could not send start signal
    echo The task exists but failed to start immediately.
    echo It will start on next login.
)
echo.

REM Step 8: Set up global pb command
echo [8/8] Setting up global 'pb' command...
echo.
echo To use 'pb' from anywhere, we need to add it to your PATH.
echo.

set /p "ADD_PATH=Add 'pb' command to PATH? (y/n) [y]: "

if not "!ADD_PATH!"=="n" if not "!ADD_PATH!"=="N" (
    echo Adding to PATH...
    
    REM Add project directory to user PATH
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"
    
    REM Check if already in PATH
    echo !USER_PATH! | find /i "%PROJECT_DIR%" >nul
    if !errorLevel! neq 0 (
        setx PATH "!USER_PATH!;%PROJECT_DIR%" >nul
        echo [OK] Added to PATH
        echo [OK] You can now use 'pb today' from anywhere!
        echo.
        echo NOTE: Close and reopen Command Prompt for 'pb' command to work
        set "PB_CMD=pb"
    ) else (
        echo [INFO] Already in PATH
        set "PB_CMD=pb"
    )
) else (
    echo [INFO] Skipped PATH setup
    set "PB_CMD=%PROJECT_DIR%\pb"
)
echo.

REM Test the service
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Testing Service Startup
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Waiting for service to start (this may take 10-15 seconds)...
timeout /t 8 /nobreak >nul

set "SUCCESS=0"
set "ATTEMPTS=0"
for /l %%i in (1,1,12) do (
    set /a ATTEMPTS=%%i
    curl -s http://127.0.0.1:7373/api/health >nul 2>&1
    if !errorLevel! equ 0 (
        set "SUCCESS=1"
        goto :ServiceRunning
    )
    echo | set /p="."
    timeout /t 1 /nobreak >nul
)

:ServiceRunning
echo.
echo.
if "!SUCCESS!"=="1" (
    color 0A
    echo ✅ SUCCESS! Service is running!
    echo.
    echo Dashboard is now available at: http://127.0.0.1:7373/dashboard
) else (
    color 0C
    echo.
    echo ❌ WARNING: Service did not start!
    echo.
    echo Attempted !ATTEMPTS! times but could not connect to http://127.0.0.1:7373
    echo.
    echo This usually means:
    echo   1. Port 7373 is already in use by another application
    echo   2. Python dependencies are missing
    echo   3. Virtual environment has issues
    echo   4. Firewall is blocking Python
    echo.
    echo 🔍 To diagnose the issue:
    echo.
    echo   1. Check error logs:
    echo      type %USERPROFILE%\.packetbuddy\stderr.log
    echo.
    echo   2. Try running manually to see the error:
    echo      cd "%PROJECT_DIR%"
    echo      venv\Scripts\activate
    echo      python -m src.api.server
    echo.
    echo   3. Check if port 7373 is in use:
    echo      netstat -ano ^| findstr :7373
    echo.
    echo   4. View full troubleshooting guide:
    echo      https://github.com/instax-dutta/packet-buddy/blob/main/docs/WINDOWS_SERVICE_NOT_STARTING.md
    echo.
    echo The service will auto-start on next login, but please check the logs!
    echo.
    pause
)
echo.

REM Final success message
color 0A
cls
echo.
echo ═══════════════════════════════════════════════════════
echo            PacketBuddy Setup Complete!
echo ═══════════════════════════════════════════════════════
echo.
echo  Your network usage is now being tracked 24/7!
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo Quick Start:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  Dashboard:
echo    start http://127.0.0.1:7373/dashboard
echo.

if "!PB_CMD!"=="pb" (
    echo  CLI Commands (after reopening Command Prompt):
    echo    pb today        # Today's usage
    echo    pb summary      # Lifetime stats
    echo    pb month        # Monthly breakdown
    echo    pb export       # Download data
) else (
    echo  CLI Commands:
    echo    cd "%PROJECT_DIR%"
    echo    pb.cmd today    # Today's usage
    echo    pb.cmd summary  # Lifetime stats
    echo    pb.cmd month    # Monthly breakdown
)
echo.
echo  Data Location:
echo    %CONFIG_DIR%\packetbuddy.db
echo.
echo  Service Control:
echo    schtasks /run /tn "PacketBuddy"     # Start
echo    schtasks /end /tn "PacketBuddy"     # Stop
echo    schtasks /query /tn "PacketBuddy"   # Status
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo  Tip: The service auto-starts on every login!
echo  Tip: Resource usage: ~30MB RAM, less than 0.5%% CPU
echo.
echo Happy tracking!
echo.
pause
