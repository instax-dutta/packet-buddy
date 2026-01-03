# PacketBuddy Windows Service Installation Script
# Run as Administrator

param(
    [string]$NeonDbUrl = ""
)

Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  PacketBuddy - Windows Service Installer" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent (Split-Path -Parent $scriptPath)

Write-Host "Project Path: $projectPath" -ForegroundColor Yellow

# Check if Python is installed
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path

if (-not $pythonPath) {
    Write-Host "❌ Python not found. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

# Use pythonw (windowless) if it exists in the same directory
$pythonBaseDir = Split-Path -Parent $pythonPath
$pythonwPath = Join-Path $pythonBaseDir "pythonw.exe"

if (Test-Path $pythonwPath) {
    $execPath = $pythonwPath
    Write-Host "✓ Using headless Python: $execPath" -ForegroundColor Green
} else {
    $execPath = $pythonPath
    Write-Host "✓ Using standard Python: $execPath" -ForegroundColor Green
}

# Create scheduled task to run PacketBuddy on startup
$taskName = "PacketBuddy"
$taskDescription = "PacketBuddy network usage tracking service"

# Remove existing task if present
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action
$action = New-ScheduledTaskAction `
    -Execute $execPath `
    -Argument "-m src.api.server" `
    -WorkingDirectory $projectPath

# Create trigger (at startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Create principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Register task
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Description $taskDescription `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force
    
    Write-Host "✓ Scheduled task created successfully" -ForegroundColor Green
    
    # Set environment variable if provided
    if ($NeonDbUrl) {
        [System.Environment]::SetEnvironmentVariable("NEON_DB_URL", $NeonDbUrl, [System.EnvironmentVariableTarget]::User)
        Write-Host "✓ NEON_DB_URL environment variable set" -ForegroundColor Green
    }
    
    # Start the task
    Write-Host ""
    Write-Host "Starting PacketBuddy service..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    
    Start-Sleep -Seconds 2
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  ✓ PacketBuddy installed successfully!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dashboard: http://127.0.0.1:7373/dashboard" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To uninstall:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName 'PacketBuddy' -Confirm:`$false" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host "❌ Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}
