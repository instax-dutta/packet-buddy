# PacketBuddy Troubleshooting Guide

This guide covers common issues, diagnostic procedures, and solutions for PacketBuddy.

## Table of Contents

- [Common Issues and Solutions](#common-issues-and-solutions)
- [Log Files and Debugging](#log-files-and-debugging)
- [Service Management Commands](#service-management-commands)
- [Database Issues](#database-issues)
- [Network Issues](#network-issues)
- [NeonDB/Cloud Sync Issues](#neondbcloud-sync-issues)
- [Recovery Procedures](#recovery-procedures)
- [Getting Help](#getting-help)

---

## Common Issues and Solutions

### Service Won't Start

**Symptoms:**
- Dashboard won't load at http://127.0.0.1:7373/dashboard
- API connection refused errors
- `pb today` command hangs or fails

**Diagnostic Steps:**

1. **Check if the service is running:**
   ```bash
   # Windows
   tasklist | findstr pythonw
   
   # macOS/Linux
   ps aux | grep packetbuddy
   ```

2. **Check service status:**
   ```bash
   # Windows
   schtasks /query /tn PacketBuddy
   
   # macOS
   launchctl list | grep packetbuddy
   
   # Linux
   systemctl --user status packetbuddy.service
   ```

3. **Check log files** (see [Log Files section](#log-files-and-debugging))

**Solutions:**

- **Run setup as Administrator:**
  ```bash
  # Windows
  setup.bat  # Right-click -> Run as Administrator
  
  # macOS/Linux
  ./setup.sh
  ```

- **Manually start the service:**
  ```bash
  pb service start
  ```

- **Check for port conflicts** (see [Port in Use](#port-in-use))

---

### Dashboard Not Accessible

**Symptoms:**
- Browser shows "Connection refused" or "Unable to connect"
- Dashboard loads but shows no data

**Diagnostic Steps:**

1. **Verify the API is responding:**
   ```bash
   curl http://127.0.0.1:7373/api/health
   ```

2. **Check the configured port:**
   ```bash
   # View current config
   cat ~/.packetbuddy/config.toml  # macOS/Linux
   type %USERPROFILE%\.packetbuddy\config.toml  # Windows
   ```

**Solutions:**

- **Restart the service:**
  ```bash
  pb service restart
  ```

- **Check firewall settings:**
  - Ensure port 7373 (or your configured port) allows local connections
  - PacketBuddy only binds to 127.0.0.1 by default

---

### No Data Being Recorded

**Symptoms:**
- Dashboard shows 0 bytes for all time periods
- `pb today` returns zeros
- No historical data available

**Diagnostic Steps:**

1. **Check if monitor is running:**
   ```bash
   curl http://127.0.0.1:7373/api/live
   ```
   Should return current upload/download speeds.

2. **Check database stats:**
   ```bash
   pb stats
   ```

3. **Verify network interfaces:**
   - Check logs for "Monitoring primary interface:" message
   - If no interface detected, all non-virtual interfaces are summed

**Solutions:**

- **First run after reboot shows zero:** This is expected behavior. PacketBuddy records usage from when it started, not before. v1.4.2+ includes catch-up logic for usage during the same boot session.

- **Restart the service:**
  ```bash
  pb service restart
  ```

- **Check for interface detection issues:**
  - Virtual interfaces (VPN, Docker, etc.) are automatically filtered
  - Check `~/.packetbuddy/stdout.log` for interface detection messages

---

### High CPU/Memory Usage

**Symptoms:**
- PacketBuddy consuming excessive resources
- System slowdown when service running

**Diagnostic Steps:**

1. **Monitor resource usage:**
   ```bash
   # Windows - Task Manager or:
   wmic process where "name='pythonw.exe'" get ProcessId,PageFileUsage,WorkingSetSize
   
   # macOS/Linux
   top -p $(pgrep -f packetbuddy)
   ```

2. **Check database size:**
   ```bash
   pb stats
   ```

**Solutions:**

- **Reduce poll interval:**
  Edit `~/.packetbuddy/config.toml`:
  ```toml
  [monitoring]
  poll_interval = 2  # Increase from default 1 second
  batch_write_interval = 60  # Increase batch interval
  ```

- **Run cleanup to reduce database size:**
  ```bash
  pb storage cleanup
  ```

- **Battery-aware mode:**
  PacketBuddy automatically reduces polling frequency when on battery power (2x poll interval, 6x batch interval).

---

### Sync Not Working

**Symptoms:**
- "Sync disabled" message in logs
- Multi-device stats not aggregating
- NeonDB connection errors

**Diagnostic Steps:**

1. **Check sync status:**
   ```bash
   curl http://127.0.0.1:7373/api/health | grep sync_enabled
   ```

2. **Verify NeonDB configuration:**
   ```bash
   # Check if NEON_DB_URL is set
   echo $NEON_DB_URL  # macOS/Linux
   echo %NEON_DB_URL%  # Windows
   ```

3. **Check unsynced log count:**
   ```bash
   pb stats
   ```

**Solutions:**

- **Set NeonDB URL:**
  ```bash
  # macOS/Linux - add to ~/.bashrc or ~/.zshrc
  export NEON_DB_URL="postgresql://user:pass@host/db?sslmode=require"
  
  # Windows - set in System Environment Variables
  setx NEON_DB_URL "postgresql://user:pass@host/db?sslmode=require"
  ```

- **Or add to config.toml:**
  ```toml
  [database]
  neon_url = "postgresql://user:pass@host/db?sslmode=require"
  
  [sync]
  enabled = true
  interval = 300  # 5 minutes (optimized for NeonDB cold starts)
  ```

- **Restart service after configuration change:**
  ```bash
  pb service restart
  ```

---

### Database Errors

**Symptoms:**
- "Database locked" errors
- SQLite errors in logs
- Data not persisting

**Diagnostic Steps:**

1. **Check database file:**
   ```bash
   ls -la ~/.packetbuddy/packetbuddy.db
   ```

2. **Check database integrity:**
   ```bash
   pb stats
   ```

**Solutions:**

- **Database locked:** Wait a few seconds and retry. This usually resolves itself as SQLite handles concurrent access.

- **Permission issues:** Ensure the `.packetbuddy` directory is writable:
  ```bash
  chmod 755 ~/.packetbuddy
  chmod 644 ~/.packetbuddy/packetbuddy.db
  ```

---

### Permission Issues

**Symptoms:**
- "Permission denied" errors in logs
- Service fails to start
- Cannot write to database

**Solutions:**

- **Fix directory permissions:**
  ```bash
  # macOS/Linux
  chmod -R 755 ~/.packetbuddy
  
  # Windows - run as Administrator or fix folder permissions
  icacls "%USERPROFILE%\.packetbuddy" /grant:r "%USERNAME%:(OI)(CI)F"
  ```

- **Run setup with elevated privileges:**
  ```bash
  # Windows
  # Right-click setup.bat -> Run as Administrator
  
  # macOS/Linux
  sudo ./setup.sh  # Only if needed for service registration
  ```

---

### Port in Use

**Symptoms:**
- Error: `[Errno 10048] Only one usage of each socket address`
- `Address already in use` error

**Solutions:**

1. **Change the port in config:**
   Edit `~/.packetbuddy/config.toml`:
   ```toml
   [api]
   host = "127.0.0.1"
   port = 7374  # Change to available port
   ```

2. **Restart service:**
   ```bash
   pb service restart
   ```

3. **Find what's using the port:**
   ```bash
   # Windows
   netstat -ano | findstr :7373
   
   # macOS/Linux
   lsof -i :7373
   ```

---

## Log Files and Debugging

### Log File Locations

| Platform | Location |
|----------|----------|
| Windows | `%USERPROFILE%\.packetbuddy\stdout.log` and `stderr.log` |
| macOS/Linux | `~/.packetbuddy/stdout.log` and `~/.packetbuddy/stderr.log` |

### Viewing Logs

```bash
# View recent logs
cat ~/.packetbuddy/stdout.log
cat ~/.packetbuddy/stderr.log

# Follow logs in real-time (macOS/Linux)
tail -f ~/.packetbuddy/stdout.log

# Windows PowerShell
Get-Content $env:USERPROFILE\.packetbuddy\stdout.log -Tail 50 -Wait
```

### Common Log Messages

| Message | Meaning |
|---------|---------|
| `Monitoring primary interface: eth0` | Successfully detected network interface |
| `No primary interface detected` | Using all non-virtual interfaces |
| `Sync disabled (no NEON_DB_URL configured)` | Cloud sync not configured |
| `Synced N logs to NeonDB` | Successful sync to cloud |
| `Catching up on missed usage` | Recovering usage from same boot session |
| `Battery check` | Battery-aware mode active |

### Debug Mode

For verbose output, run the server directly:

```bash
cd /path/to/packet-buddy
python -m src.api.server
```

---

## Service Management Commands

### CLI Commands

```bash
# Start the background service
pb service start

# Stop the background service
pb service stop

# Restart the background service
pb service restart
```

### Platform-Specific Commands

**Windows (Task Scheduler):**
```bash
# Query task status
schtasks /query /tn PacketBuddy

# Run task manually
schtasks /run /tn PacketBuddy

# End task
schtasks /end /tn PacketBuddy

# Create task (usually done by setup.bat)
# See setup.bat for full command
```

**macOS (launchd):**
```bash
# List service
launchctl list | grep packetbuddy

# Start service
launchctl kickstart -p gui/$(id -u)/com.packetbuddy.daemon

# Stop service
launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon

# Load service
launchctl load ~/Library/LaunchAgents/com.packetbuddy.daemon.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.packetbuddy.daemon.plist
```

**Linux (systemd):**
```bash
# Check status
systemctl --user status packetbuddy.service

# Start service
systemctl --user start packetbuddy.service

# Stop service
systemctl --user stop packetbuddy.service

# Enable at login
systemctl --user enable packetbuddy.service

# Disable at login
systemctl --user disable packetbuddy.service

# View logs
journalctl --user -u packetbuddy.service
```

---

## Database Issues

### Database Locked

**Cause:** SQLite handles concurrent access automatically, but occasional lock contention can occur.

**Solutions:**
1. Wait a few seconds and retry
2. Restart the service:
   ```bash
   pb service restart
   ```
3. If persistent, check for zombie processes:
   ```bash
   # macOS/Linux
   lsof ~/.packetbuddy/packetbuddy.db
   
   # Windows
   # Use Resource Monitor to find processes with open handles
   ```

### Database Too Large

**Symptoms:**
- `pb stats` shows high storage usage percentage
- Slow queries
- Disk space concerns

**Diagnostic:**
```bash
pb stats
```

Check the `Storage usage` percentage. If >= 80%, cleanup is recommended.

**Solutions:**

1. **Run standard cleanup:**
   ```bash
   pb storage cleanup
   ```
   
   This removes synced logs older than the configured retention period (default: 30 days).

2. **Check what would be deleted (dry run):**
   ```bash
   pb storage cleanup --dry-run
   ```

3. **Custom retention period:**
   ```bash
   pb storage cleanup --days 7
   ```

4. **Manual VACUUM:**
   ```bash
   # Via API
   curl -X POST "http://127.0.0.1:7373/api/storage/cleanup?vacuum=true"
   ```

### Cleanup Procedures

**Standard Cleanup:**
```bash
# Local database cleanup
pb storage cleanup

# With custom retention
pb storage cleanup --days 14

# Without VACUUM (faster)
pb storage cleanup --no-vacuum
```

**Database Statistics:**
```bash
pb stats
pb storage stats  # Same command
```

**API-based Cleanup:**
```bash
# Standard cleanup with vacuum
curl -X POST "http://127.0.0.1:7373/api/storage/cleanup?vacuum=true"

# Aggressive cleanup (for storage crisis)
curl -X POST "http://127.0.0.1:7373/api/storage/cleanup?aggressive=true&vacuum=true"
```

---

## Network Issues

### Incorrect Speed Readings

**Symptoms:**
- Speeds seem too high or too low
- Negative speed values
- Spikes in usage

**Causes and Solutions:**

1. **Counter reset (negative values):**
   - Occurs after system sleep/hibernate
   - PacketBuddy automatically detects and skips these samples
   - No action needed

2. **Unreasonably large deltas:**
   - Default threshold: 1 GB/s
   - Samples above this are automatically skipped
   - Adjust in config if needed:
     ```toml
     [monitoring]
     max_delta_bytes = 2000000000  # 2 GB/s
     ```

3. **VPN/Virtual interfaces included:**
   - PacketBuddy filters common virtual interfaces
   - Filtered prefixes: `lo`, `utun`, `awdl`, `llw`, `anpi`, `gif`, `stf`, `bridge`, `ap`, `vboxnet`, `vmnet`, `docker`, `veth`

### Missing Interface Data

**Symptoms:**
- No usage recorded despite active network
- "No primary interface detected" in logs

**Diagnostic:**

Check which interfaces are being monitored:
```bash
# Look for interface detection in logs
grep "interface" ~/.packetbuddy/stdout.log
```

**Solutions:**

1. **All non-virtual interfaces are summed:**
   - If no primary interface is detected, PacketBuddy sums all physical interfaces
   - This is normal and expected behavior

2. **Primary interface detection:**
   - Windows: Uses `Get-NetRoute` to find interface with default gateway
   - macOS: Uses `route -n get default`
   - Linux: Uses `ip route show default`

3. **Manual verification:**
   ```bash
   # Windows
   powershell -Command "Get-NetRoute -DestinationPrefix 0.0.0.0/0 | Select-Object InterfaceAlias"
   
   # macOS
   route -n get default | grep interface
   
   # Linux
   ip route show default
   ```

---

## NeonDB/Cloud Sync Issues

### Connection Failures

**Symptoms:**
- "Failed to connect to NeonDB" errors
- Sync timeout errors
- "Sync service error" in logs

**Diagnostic:**

1. **Verify NeonDB URL format:**
   ```bash
   echo $NEON_DB_URL
   ```
   Should be: `postgresql://user:password@host/database?sslmode=require`

2. **Test connection manually:**
   ```bash
   # Using psql
   psql "$NEON_DB_URL" -c "SELECT 1"
   ```

3. **Check sync status:**
   ```bash
   pb storage neon
   ```

**Solutions:**

1. **Verify credentials:**
   - Check NeonDB dashboard for connection string
   - Ensure password is URL-encoded if it contains special characters

2. **Check network connectivity:**
   - NeonDB requires internet access
   - Verify firewall allows outbound connections

3. **Retry settings:**
   ```toml
   [sync]
   retry_delay = 5  # Seconds between retries
   max_retries = 3  # Number of retry attempts
   ```

### Storage Quota Exceeded

**Symptoms:**
- NeonDB writes failing
- "Storage quota exceeded" errors
- Dashboard shows old data

**Diagnostic:**
```bash
pb storage neon
```

Check the `Usage` percentage. NeonDB free tier limit is 512 MB.

**Solutions:**

1. **Standard NeonDB cleanup:**
   ```bash
   pb storage cleanup --neon
   ```

2. **Aggressive cleanup (for storage crisis):**
   ```bash
   pb storage cleanup --neon --aggressive
   
   # Or the shortcut:
   pb neon-cleanup
   ```
   
   Aggressive cleanup reduces retention to:
   - Logs: 3 days
   - Daily aggregates: 1 month
   - Monthly aggregates: 2 months

3. **Automatic cleanup:**
   - PacketBuddy automatically runs aggressive cleanup when NeonDB storage exceeds 80%
   - This happens during the periodic cleanup task (every 24 hours)

### Aggressive Cleanup

When NeonDB storage is critically high (>80%):

```bash
# Quick command
pb neon-cleanup

# Or with full options
pb storage cleanup --neon --aggressive
```

**What aggressive cleanup does:**
1. Deletes logs older than 3 days
2. Deletes daily aggregates older than 1 month
3. Deletes monthly aggregates older than 2 months
4. Runs `VACUUM ANALYZE` on all tables

**Retention Settings:**

Configure in `~/.packetbuddy/config.toml`:
```toml
[storage.neon]
log_retention_days = 7           # Default: 7 days
aggregate_retention_months = 3   # Default: 3 months
max_storage_mb = 450             # Warning threshold in MB
warning_threshold_percent = 80   # Percentage for warning
cleanup_on_sync = true           # Auto-cleanup during sync
```

---

## Recovery Procedures

### Complete Service Reset

If PacketBuddy is completely broken:

1. **Stop the service:**
   ```bash
   pb service stop
   ```

2. **Backup data (optional):**
   ```bash
   cp ~/.packetbuddy/packetbuddy.db ~/packetbuddy_backup.db
   ```

3. **Re-run setup:**
   ```bash
   ./setup.bat   # Windows
   ./setup.sh    # macOS/Linux
   ```

4. **Start service:**
   ```bash
   pb service start
   ```

### Database Recovery

If the database is corrupted:

1. **Stop service:**
   ```bash
   pb service stop
   ```

2. **Check database integrity:**
   ```bash
   sqlite3 ~/.packetbuddy/packetbuddy.db "PRAGMA integrity_check;"
   ```

3. **If corrupted, recreate:**
   ```bash
   # Backup first
   mv ~/.packetbuddy/packetbuddy.db ~/.packetbuddy/packetbuddy.db.broken
   
   # Service will create a new database on start
   pb service start
   ```

### Version Mismatch

If dashboard shows old version but code is newer:

**Cause:** Python module caching or stale VERSION file

**Solution:**
```bash
# Restart service (v1.4.2+ uses dynamic versioning)
pb service restart

# Or force update
pb update --force
```

---

## Getting Help

### Before Reporting

1. **Collect diagnostic information:**
   ```bash
   # Service status
   pb service --help
   
   # Database stats
   pb stats
   
   # Health check
   curl http://127.0.0.1:7373/api/health
   ```

2. **Check logs:**
   ```bash
   cat ~/.packetbuddy/stderr.log
   cat ~/.packetbuddy/stdout.log
   ```

3. **Note your configuration:**
   - OS version
   - PacketBuddy version (`pb --version` or check VERSION file)
   - Any custom config.toml settings

### GitHub Issues

Report issues at: https://github.com/instax-dutta/packet-buddy/issues

**Include in your report:**
- Description of the problem
- Steps to reproduce
- Relevant log snippets
- Output of `pb stats`
- Your OS and PacketBuddy version
- Any error messages

### Useful Debug Commands

```bash
# Full system check
curl -s http://127.0.0.1:7373/api/health | python -m json.tool

# Storage status (both local and NeonDB)
curl -s http://127.0.0.1:7373/api/storage | python -m json.tool

# Current speed
curl -s http://127.0.0.1:7373/api/live

# Today's usage
curl -s http://127.0.0.1:7373/api/today

# Check for updates
pb update --check-only

# View config
cat ~/.packetbuddy/config.toml
```

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Service won't start | `pb service restart` or run `setup.bat/sh` as admin |
| Dashboard not loading | Check `curl http://127.0.0.1:7373/api/health` |
| No data recorded | Restart service, check logs for interface detection |
| High CPU/memory | Reduce `poll_interval` in config, run cleanup |
| Sync not working | Set `NEON_DB_URL` env var or in config.toml |
| Database locked | Wait and retry, or restart service |
| NeonDB storage full | `pb neon-cleanup` or `pb storage cleanup --neon --aggressive` |
| Port in use | Change `port` in `~/.packetbuddy/config.toml` |
| Old version showing | `pb service restart` or `pb update --force` |
