# PacketBuddy One-Time Automated Setup for Windows
# Run this as Administrator: Right-click PowerShell > Run as Administrator

param(
    [string]$NeonDbUrl = ""
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor Yellow
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "  3. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Fancy header
Clear-Host
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "           📊 PacketBuddy Setup Wizard" -ForegroundColor Magenta
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Magenta
Write-Host ""
Write-Host "Ultra-lightweight network usage tracker" -ForegroundColor Cyan
Write-Host "This will take about 2 minutes..." -ForegroundColor Cyan
Write-Host ""

$ProjectDir = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
Write-Host "📁 Project directory: $ProjectDir" -ForegroundColor Blue
Write-Host ""

# Step 1: Check Python
Write-Host "[1/7] Checking Python installation..." -ForegroundColor Yellow

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.([0-9]+)") {
            if ([int]$matches[1] -ge 11) {
                $pythonCmd = $cmd
                break
            }
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "✗ Python 3.11+ not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.11+ from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

$pythonVersion = & $pythonCmd --version
Write-Host "✓ $pythonVersion found" -ForegroundColor Green
Write-Host ""

# Step 2: Create virtual environment
Write-Host "[2/7] Setting up Python virtual environment..." -ForegroundColor Yellow
Set-Location $ProjectDir

if (Test-Path "venv") {
    Write-Host "→ Virtual environment already exists, skipping" -ForegroundColor Yellow
} else {
    & $pythonCmd -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Step 3: Install dependencies
Write-Host "[3/7] Installing dependencies..." -ForegroundColor Yellow
& "$ProjectDir\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$ProjectDir\venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
Write-Host "✓ All dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 4: Create config directory
Write-Host "[4/7] Creating configuration directory..." -ForegroundColor Yellow
$ConfigDir = "$env:USERPROFILE\.packetbuddy"
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

if (-not (Test-Path "$ConfigDir\config.toml")) {
    Copy-Item "config.example.toml" "$ConfigDir\config.toml"
    Write-Host "✓ Configuration file created" -ForegroundColor Green
} else {
    Write-Host "→ Configuration file already exists" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Optional NeonDB setup
Write-Host "[5/7] Cloud sync configuration..." -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Multi-Device Cloud Sync (Optional)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

if ([string]::IsNullOrEmpty($NeonDbUrl)) {
    Write-Host "Do you want to enable cloud sync with NeonDB?" -ForegroundColor White
    Write-Host "This allows you to track multiple devices (Mac + PC) in one database." -ForegroundColor White
    Write-Host ""
    Write-Host "Benefits:" -ForegroundColor Green
    Write-Host "  • Track all your devices in one place"
    Write-Host "  • Free tier supports 10GB (enough for years)"
    Write-Host "  • Automatic cloud backup"
    Write-Host ""
    Write-Host "Note: If skipped, PacketBuddy works perfectly with local-only tracking." -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Enable cloud sync? (y/n) [n]"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host ""
        Write-Host "📝 Please enter your NeonDB connection string:" -ForegroundColor Blue
        Write-Host "(Format: postgresql://user:pass@host.neon.tech/db?sslmode=require)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Don't have one? Get it free at: https://neon.tech" -ForegroundColor White
        Write-Host ""
        $NeonDbUrl = Read-Host "NeonDB URL"
    }
}

if (-not [string]::IsNullOrEmpty($NeonDbUrl)) {
    # Set as environment variable (user-level, permanent)
    [System.Environment]::SetEnvironmentVariable("NEON_DB_URL", $NeonDbUrl, [System.EnvironmentVariableTarget]::User)
    $env:NEON_DB_URL = $NeonDbUrl
    Write-Host "✓ NeonDB configured" -ForegroundColor Green
} else {
    Write-Host "→ Skipping cloud sync (local-only mode)" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Initialize database
Write-Host "[6/7] Initializing database..." -ForegroundColor Yellow
& "$ProjectDir\venv\Scripts\python.exe" -c "from src.core.storage import storage; storage.get_device_id()" 2>&1 | Out-Null
Write-Host "✓ Database initialized" -ForegroundColor Green
Write-Host ""

# Step 7: Create scheduled task
Write-Host "[7/7] Setting up auto-start service..." -ForegroundColor Yellow

$TaskName = "PacketBuddy"
$pythonw = "$ProjectDir\venv\Scripts\pythonw.exe"
if (Test-Path $pythonw) {
    $PythonExe = $pythonw
} else {
    $PythonExe = "$ProjectDir\venv\Scripts\python.exe"
}
$WorkingDir = $ProjectDir

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "→ Removed existing scheduled task" -ForegroundColor Yellow
}

# Create action with internal PYTHONPATH setting
$TaskCmd = "cmd /c cd /d `"$WorkingDir`" && set PYTHONPATH=$WorkingDir&& `"$PythonExe`" -m src.api.server"
$Action = New-ScheduledTaskAction -Execute "cmd.exe" `
    -Argument "/c $TaskCmd"

# Create trigger (at logon)
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -Priority 7 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Register task
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "PacketBuddy Network Usage Tracker" `
    -User $env:USERNAME `
    -RunLevel Highest | Out-Null

Write-Host "✓ Scheduled task created" -ForegroundColor Green

# Start the task
Start-ScheduledTask -TaskName $TaskName
Write-Host "✓ Service started" -ForegroundColor Green
Write-Host ""

# Step 8: Test the service
Write-Host "Testing service..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Waiting for service to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

$success = $false
for ($i = 1; $i -le 6; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:7373/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $success = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
}
Write-Host ""

if ($success) {
    Write-Host "✓ Service is running!" -ForegroundColor Green
} else {
    Write-Host "⚠ Service may need a moment to start" -ForegroundColor Red
    Write-Host "Check Task Scheduler for status" -ForegroundColor Yellow
}
Write-Host ""

# Final success message
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "           ✓ PacketBuddy Setup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Your network usage is now being tracked 24/7!" -ForegroundColor Magenta
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Dashboard:" -ForegroundColor Green
Write-Host "   start http://127.0.0.1:7373/dashboard"
Write-Host ""
Write-Host "📱 CLI Commands (from project directory):" -ForegroundColor Green
Write-Host "   .\venv\Scripts\python.exe -m src.cli.main today"
Write-Host "   .\venv\Scripts\python.exe -m src.cli.main summary"
Write-Host "   .\venv\Scripts\python.exe -m src.cli.main month"
Write-Host ""
Write-Host "📁 Data Location:" -ForegroundColor Green
Write-Host "   Database: $ConfigDir\packetbuddy.db"
Write-Host "   Config:   $ConfigDir\config.toml"
Write-Host ""
Write-Host "🔧 Service Control:" -ForegroundColor Green
Write-Host "   Start:   Start-ScheduledTask -TaskName 'PacketBuddy'"
Write-Host "   Stop:    Stop-ScheduledTask -TaskName 'PacketBuddy'"
Write-Host "   Status:  Get-ScheduledTask -TaskName 'PacketBuddy'"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tip: The service will automatically start on every login!" -ForegroundColor Yellow
Write-Host "💡 Tip: Add to PATH for easier CLI access" -ForegroundColor Yellow
Write-Host ""
Write-Host "Happy tracking! 🚀" -ForegroundColor Magenta
Write-Host ""
