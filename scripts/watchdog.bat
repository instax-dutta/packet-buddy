@echo off
REM PacketBuddy Watchdog - Monitors and auto-restarts the service if it crashes
REM This script will keep checking if PacketBuddy is running and restart it if needed

:LOOP
REM Check if service is responding
curl -s http://127.0.0.1:7373/api/health >nul 2>&1

if %errorLevel% neq 0 (
    echo [%date% %time%] Service not responding, restarting...
    schtasks /run /tn "PacketBuddy" >nul 2>&1
    timeout /t 10 /nobreak >nul
)

REM Wait 30 seconds before next check
timeout /t 30 /nobreak >nul
goto LOOP
