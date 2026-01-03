# 🛠️ Operational Maintenance & Debugging

A guide for AI agents to diagnose and repair local PacketBuddy installations.

## 🔍 Log Diagnostics

Always check the local logs first:

- **macOS/Windows Paths**: `~/.packetbuddy/stdout.log` and `~/.packetbuddy/stderr.log`.
- **Common Issues**:
  - `ModuleNotFoundError`: Usually means the `pip` sync failed during `pb update`. Solution: rerun `venv` installation.
  - `0 B` usage: Primary interface detection failure. Check `monitor._get_primary_interface()` logs.

## 2. Cross-Platform Runtime

The application is designed to run as a "headless" daemon.

- **macOS**: Controlled via `launchd` using the custom `.plist` in `~/Library/LaunchAgents`.
- **Windows**: Controlled via **Task Scheduler** (`schtasks`). It is configured to run at startup with "Highest Privileges" to ensure it survives user logouts.
- **Linux**: Controlled via **Systemd** (`systemctl`). Installed as a user-level service (`--user`) for security and persistence.

## ♻️ Service Control Manual

### Unified CLI Management (Recommended)

You can manage the service on any platform using:

- **Start**: `pb service start`
- **Stop**: `pb service stop`
- **Restart**: `pb service restart`

### macOS (launchctl)

...

- **Status**: `launchctl list | grep packetbuddy`
- **Restart**: `launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon`
- **Manual Debug**: `source venv/bin/activate && python -m src.api.server`

### Windows (schtasks)

- **Status**: `schtasks /query /tn PacketBuddy`
- **Restart**: `schtasks /end /tn PacketBuddy` then `schtasks /run /tn PacketBuddy`
- **Manual Debug**: `.\venv\Scripts\python.exe -m src.api.server`

### Linux (systemd)

- **Status**: `systemctl --user status packetbuddy`
- **Restart**: `systemctl --user restart packetbuddy`
- **Manual Debug**: `source venv/bin/activate && python -m src.api.server`

## 📊 Database Management

- **Location**: `~/.packetbuddy/packetbuddy.db`
- **Vacuuming**: If the file grows too large (e.g., >500MB), perform an `SQLITE VACUUM`.
- **Integrity**: `PRAGMA integrity_check;` should be run if usage charts look corrupted.

## 📦 Update Management

The `pb update` command is a wrapper for `src/utils/updater.py`.

- If a pull results in a merge conflict, the updater will fail safely.
- **Manual sync**: `git stash && git pull origin main && pb update`.

## 🔋 Battery Logic

If users report "slow updates", verify if they are on battery.

- **On Battery**: Polls 2x slower, batches 6x more.
- **On AC**: Real-time (1s polls).
- Controlled in `monitor.py` via `_check_battery_status()`.
