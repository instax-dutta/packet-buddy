# PacketBuddy Auto-Start Setup Script
# Run this as Administrator to enable auto-start on login/reboot

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "║     PacketBuddy Auto-Start Setup                      ║" -ForegroundColor Cyan
Write-Host "║                                                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator`n" -ForegroundColor Red
    Write-Host "To fix this:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "  3. Run this script again`n" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Running as Administrator`n" -ForegroundColor Green

# Get paths
$projectDir = "c:\Users\jatin\packet-buddy"
$pythonExe = "$projectDir\venv\Scripts\pythonw.exe"
$launcherScript = "$projectDir\service\windows\launcher.py"

# Verify files exist
if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ ERROR: Python executable not found at: $pythonExe`n" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path $launcherScript)) {
    Write-Host "❌ ERROR: Launcher script not found at: $launcherScript`n" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Creating Windows Task Scheduler task..." -ForegroundColor Cyan

try {
    # Create scheduled task action
    $action = New-ScheduledTaskAction -Execute $pythonExe -Argument $launcherScript
    
    # Create trigger (at logon)
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Create principal (current user, highest privileges)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Register the task
    Register-ScheduledTask -TaskName "PacketBuddy" -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
    
    Write-Host "✅ Task Scheduler task created successfully`n" -ForegroundColor Green
    
    # Verify task was created
    $task = Get-ScheduledTask -TaskName "PacketBuddy" -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "║         ✅ Auto-Start Configured Successfully!        ║" -ForegroundColor Green
        Write-Host "║                                                        ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
        
        Write-Host "PacketBuddy will now:" -ForegroundColor Cyan
        Write-Host "  ✅ Start automatically when you log in" -ForegroundColor White
        Write-Host "  ✅ Start automatically after system reboot" -ForegroundColor White
        Write-Host "  ✅ Run silently in the background" -ForegroundColor White
        Write-Host "  ✅ Auto-update itself when new versions are available`n" -ForegroundColor White
        
        Write-Host "Dashboard: http://127.0.0.1:7373/dashboard" -ForegroundColor Yellow
        Write-Host "`nTask Details:" -ForegroundColor Cyan
        Write-Host "  Task Name: PacketBuddy" -ForegroundColor White
        Write-Host "  Trigger: At logon" -ForegroundColor White
        Write-Host "  User: $env:USERNAME" -ForegroundColor White
        Write-Host "  Privilege Level: Highest`n" -ForegroundColor White
        
        # Ask if user wants to start the task now
        $start = Read-Host "Do you want to start PacketBuddy now? (Y/N)"
        if ($start -eq "Y" -or $start -eq "y") {
            Start-ScheduledTask -TaskName "PacketBuddy"
            Write-Host "`n✅ PacketBuddy started!`n" -ForegroundColor Green
            Start-Sleep -Seconds 3
            Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
            Start-Process "http://127.0.0.1:7373/dashboard"
        }
    } else {
        Write-Host "⚠️  Task created but verification failed`n" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ ERROR: Failed to create task`n" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    pause
    exit 1
}

Write-Host "`nSetup complete! You can close this window.`n" -ForegroundColor Green
pause
