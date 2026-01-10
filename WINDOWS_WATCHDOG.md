# PacketBuddy Watchdog - Automatic Crash Recovery for Windows

## Overview

The PacketBuddy Watchdog is an automatic crash recovery system for Windows that monitors the PacketBuddy service and automatically restarts it if it crashes or becomes unresponsive.

## Why This Is Needed

PacketBuddy is a long-running background service that monitors network usage. In some rare cases, the service may crash due to:

- **Export functionality bugs** - Current version has a known issue where clicking export buttons in the dashboard can cause a crash
- **Network interface changes** - Switching between Wi-Fi and Ethernet
- **System sleep/resume** - Unexpected behavior after system wakes from sleep
- **Resource exhaustion** - In extreme cases of high network activity

The watchdog ensures **zero downtime** by automatically detecting these crashes and restarting the service within seconds.

## Features

✅ **Automatic Detection** - Checks service health every 30 seconds  
✅ **Automatic Restart** - Restarts PacketBuddy immediately if it's down  
✅ **Silent Operation** - Runs in background with no user interaction needed  
✅ **Auto-Start** - Enabled via Windows Task Scheduler to start on login  
✅ **No Data Loss** - Ensures continuous network monitoring  
✅ **Lightweight** - Minimal CPU/memory usage  

## Installation

### Automatic Setup (Recommended)

Run this command in **PowerShell as Administrator**:

```powershell
$action = New-ScheduledTaskAction -Execute "c:\Users\$env:USERNAME\packet-buddy\watchdog.bat"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 0)
Register-ScheduledTask -TaskName "PacketBuddyWatchdog" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
Start-ScheduledTask -TaskName "PacketBuddyWatchdog"
Write-Host "✅ Watchdog enabled and started!" -ForegroundColor Green
```

### Manual Setup

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Task**
3. **General Tab:**
   - Name: `PacketBuddyWatchdog`
   - Run whether user is logged on or not: ❌ (unchecked)
   - Run with highest privileges: ❌ (unchecked)
4. **Triggers Tab:**
   - New → Begin the task: `At log on`
   - Specific user: Your username
5. **Actions Tab:**
   - New → Action: `Start a program`
   - Program/script: `c:\Users\[YourUsername]\packet-buddy\watchdog.bat`
6. **Settings Tab:**
   - ✅ Allow task to be run on demand
   - ✅ Run task as soon as possible after a scheduled start is missed
   - ✅ If the task fails, restart every: `1 minute`
   - ❌ Stop the task if it runs longer than: (unchecked)
   - ✅ If the running task does not end when requested, force it to stop
7. Click **OK**

## How It Works

### Monitoring Loop

```batch
:LOOP
# Check if PacketBuddy API is responding
curl -s http://127.0.0.1:7373/api/health >nul 2>&1

if service_is_down:
    # Restart PacketBuddy via Task Scheduler
    schtasks /run /tn "PacketBuddy"
    # Wait 10 seconds for service to start
    wait 10 seconds

# Check again in 30 seconds
wait 30 seconds
goto LOOP
```

### Recovery Process

1. **Detection** (every 30 seconds):
   - Watchdog sends HTTP request to `http://127.0.0.1:7373/api/health`
   - If request fails → service is down

2. **Restart** (immediate):
   - Executes: `schtasks /run /tn "PacketBuddy"`
   - Waits 10 seconds for service to initialize

3. **Verification** (next cycle):
   - Checks if service is responding
   - If still down → repeats restart process

### Files

- **watchdog.bat** - The monitoring script
- **Task: PacketBuddyWatchdog** - Windows Task Scheduler task that runs the watchdog

## Verification

Check if watchdog is running:

```powershell
# Check Task Scheduler status
Get-ScheduledTask -TaskName "PacketBuddyWatchdog"

# Check if watchdog process is running
Get-Process | Where-Object {$_.ProcessName -eq "cmd" -and $_.CommandLine -like "*watchdog*"}

# View recent watchdog activity (if logging enabled)
Get-EventLog -LogName Application -Source "PacketBuddy" -Newest 10
```

## Testing

To test the watchdog:

1. Manually stop PacketBuddy:
   ```powershell
   Stop-Process -Name "pythonw" -Force
   ```

2. Wait 30-40 seconds (watchdog check interval)

3. Verify service restarted:
   ```powershell
   curl http://127.0.0.1:7373/api/health
   ```

Expected result: Service should be back online automatically! ✅

## Troubleshooting

### Watchdog not running

**Check task status:**
```powershell
Get-ScheduledTask -TaskName "PacketBuddyWatchdog"
```

**Start manually:**
```powershell
Start-ScheduledTask -TaskName "PacketBuddyWatchdog"
```

### Service not restarting

1. **Verify PacketBuddy task exists:**
   ```powershell
   Get-ScheduledTask -TaskName "PacketBuddy"
   ```

2. **Test manual restart:**
   ```powershell
   schtasks /run /tn "PacketBuddy"
   ```

3. **Check watchdog.bat path:**
   - Ensure path in Task Scheduler matches actual file location
   - Default: `c:\Users\[YourUsername]\packet-buddy\watchdog.bat`

### Multiple instances running

If multiple watchdog instances are running:

```powershell
# Stop all watchdog tasks
Stop-ScheduledTask -TaskName "PacketBuddyWatchdog"

# Kill any orphaned cmd processes
Get-Process cmd | Where-Object {$_.CommandLine -like "*watchdog*"} | Stop-Process -Force

# Restart cleanly
Start-ScheduledTask -TaskName "PacketBuddyWatchdog"
```

## Uninstalling

To remove the watchdog:

```powershell
# Stop the watchdog
Stop-ScheduledTask -TaskName "PacketBuddyWatchdog"

# Delete the task
Unregister-ScheduledTask -TaskName "PacketBuddyWatchdog" -Confirm:$false

# Optional: Delete the watchdog.bat file
Remove-Item "c:\Users\$env:USERNAME\packet-buddy\watchdog.bat"
```

## Performance Impact

- **CPU Usage:** \<0.1% (only during health checks)
- **Memory:** ~2MB (cmd.exe process)
- **Network:** Minimal (local HTTP request every 30 seconds)
- **Disk I/O:** None (unless logging enabled)

## Known Limitations

1. **30-second downtime window** - Maximum downtime is 30 seconds (one check interval)
2. **Requires PacketBuddy task** - Assumes main PacketBuddy task is configured in Task Scheduler
3. **Local monitoring only** - Cannot detect issues if the entire system is frozen

## Future Enhancements

Potential improvements for future versions:

- [ ] Configurable check interval
- [ ] Email/SMS notifications on crash
- [ ] Detailed logging to file
- [ ] Crash counter and reporting
- [ ] Integration with Windows Event Log
- [ ] Health check retries before restart

## Related Documentation

- [Windows Service Setup](service/windows/README.md)
- [Auto-Start Configuration](WINDOWS_TASK_SCHEDULER_FIX.md)
- [Main README](README.md)

## Support

If you encounter issues with the watchdog:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review Task Scheduler logs: `eventvwr.msc` → Windows Logs → Application
3. Report issues at: https://github.com/instax-dutta/packet-buddy/issues

## License

Same license as PacketBuddy (MIT)
