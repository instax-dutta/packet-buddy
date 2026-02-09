@echo off
echo Forcing PacketBuddy restart to load v1.4.0...
echo.

echo Step 1: Stopping service...
schtasks /end /tn PacketBuddy >nul 2>&1

echo Step 2: Waiting for process to terminate...
timeout /t 5 /nobreak >nul

echo Step 3: Starting service with fresh code...
schtasks /run /tn PacketBuddy >nul 2>&1

echo Step 4: Waiting for service to start...
timeout /t 5 /nobreak >nul

echo Step 5: Checking version...
curl.exe -s http://127.0.0.1:7373/api/health 2>nul | findstr version

echo.
echo Done! Open http://127.0.0.1:7373/dashboard to verify.
echo.
pause
