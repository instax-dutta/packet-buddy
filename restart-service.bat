@echo off
echo ========================================
echo PacketBuddy Service Restart
echo ========================================
echo.

echo [1/5] Stopping scheduled task...
schtasks /end /tn PacketBuddy >nul 2>&1

echo [2/5] Killing Python processes...
taskkill /F /IM pythonw.exe >nul 2>&1

echo [3/5] Waiting for cleanup...
timeout /t 3 /nobreak >nul

echo [4/5] Starting service...
schtasks /run /tn PacketBuddy >nul 2>&1

echo [5/5] Waiting for service to start...
timeout /t 6 /nobreak >nul

echo.
echo ========================================
echo Checking version...
echo ========================================
curl.exe -s http://127.0.0.1:7373/api/health 2>nul | findstr version

echo.
echo ========================================
echo Done! Open http://127.0.0.1:7373/dashboard
echo ========================================
echo.
pause
