@echo off
REM PacketBuddy Service Stopper
REM This stops the background monitoring service

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if exist "pb.cmd" (
    call pb.cmd service stop
) else (
    echo Error: pb.cmd not found.
    pause
)
