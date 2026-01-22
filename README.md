# PacketBuddy - Network Usage & Bandwidth Tracker

**A lightweight, cross-platform network usage monitor that runs silently in the background and provides beautiful real-time analytics.**

[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue?style=flat-square)](https://github.com/instax-dutta/packet-buddy)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Version](https://img.shields.io/badge/version-1.4.0-brightgreen?style=flat-square)](https://github.com/instax-dutta/packet-buddy/releases)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## 🎉 What's New in v1.4.0

### Export System Overhaul
- **🎉 Year Wrap-Up Export**: Beautiful HTML reports perfect for sharing your internet usage year-end summary
- **🤖 TOON Format**: New token-optimized export format (~60% fewer tokens) for LLM analysis
- **📊 Enhanced Exports**: All formats now include peak speeds and comprehensive statistics
- **📥 Multiple Formats**: CSV, JSON, HTML, and TOON - choose what works best for you

### Bug Fixes & Improvements
- **⚡ Peak Speed Persistence**: Fixed dashboard peak speed resetting on page refresh
- **📈 Better Analytics**: Added 5 new storage methods for detailed statistics
- **🎨 Dashboard Update**: New "Year Wrap-Up" button for one-click export

[See full changelog](RELEASE_NOTES_v1.4.0.md)

---

## 📋 Table of Contents

- [What is PacketBuddy?](#what-is-packetbuddy)
- [Key Features](#key-features)
- [Quick Start Guide](#quick-start-guide)
  - [Windows Installation](#windows-installation)
  - [macOS Installation](#macos-installation)
  - [Linux Installation](#linux-installation)
- [How It Works](#how-it-works)
- [Dashboard Overview](#dashboard-overview)
- [Multi-Device Setup](#multi-device-setup)
- [Configuration](#configuration)
- [CLI Commands](#cli-commands)
- [Troubleshooting](#troubleshooting)
- [Automatic Crash Recovery (Windows)](#automatic-crash-recovery-windows)
- [FAQ](#faq)

---

## What is PacketBuddy?

PacketBuddy is an **ultra-lightweight network monitoring tool** that tracks your internet data usage in real-time. It runs silently in the background and provides a beautiful web dashboard to visualize your network activity.

### Perfect For

- 📊 **Tracking data usage** on capped internet connections
- 💰 **Monitoring costs** with built-in ₹ (INR) cost calculator
- 🌐 **Multi-device tracking** across Windows, macOS, and Linux
- 📱 **Verifying ISP bills** with accurate bandwidth measurements
- 🎓 **Network troubleshooting** and identifying data-heavy applications
- 🎉 **Year-end wrap-ups** with beautiful HTML reports and LLM-optimized exports

### Why PacketBuddy?

- ✅ **Minimal resource usage**: <40MB RAM, <0.5% CPU
- ✅ **Privacy-focused**: All data stored locally (cloud sync optional)
- ✅ **Zero configuration**: One-command installation
- ✅ **Auto-starts on boot**: Runs silently in background
- ✅ **Beautiful dashboard**: Real-time charts and analytics
- ✅ **Cross-platform**: Works on Windows, macOS, and Linux

---

## Key Features

### 🎨 Beautiful Web Dashboard

- Real-time upload/download speed monitoring
- Daily, monthly, and lifetime statistics
- **Persistent peak speed tracking** (no more resets on refresh!)
- Indian Rupee (₹) cost tracking (@ ₹7.50/GB)
- Interactive charts with Chart.js
- Dark theme optimized for readability
- **One-click year wrap-up export** 🎉

### ⚙️ Smart Monitoring

- **Automatic interface detection**: Locks to your primary network interface
- **Zero data inflation**: Filters out system overhead (AirDrop, Sidecar, etc.)
- **Battery-aware**: Optimizes polling when on battery power
- **Timezone-accurate**: Data resets at midnight in your local timezone
- **Crash recovery**: Auto-restarts and handles network interruptions gracefully

### 🌐 Multi-Device Support (Optional)

- Track unlimited devices with a single NeonDB database
- Device identification and aggregate reporting
- Free tier supports 10GB storage (enough for years of data)

### 🔧 Zero Configuration

- One-command installation on all platforms
- Auto-starts on system boot
- Background daemon mode
- Automatic updates with `pb update`

---

## Quick Start Guide

### Prerequisites

**All Platforms:**

- Python 3.11 or higher ([Download here](https://www.python.org/downloads/))
- Git (optional, for cloning)

**Windows Only:**

- Administrator privileges (for Task Scheduler setup)

**Optional:**

- NeonDB account for multi-device sync ([Free tier](https://neon.tech))

---

### Windows Installation

#### Step 1: Download PacketBuddy

```batch
# Option A: Clone with Git
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy

# Option B: Download ZIP from GitHub and extract
```

#### Step 2: Run Setup as Administrator

```batch
# Right-click on setup.bat and select "Run as administrator"
# OR run from Command Prompt (as Administrator):
cd path\to\packet-buddy
service\windows\setup.bat
```

**What the setup does:**

1. ✅ Checks Python 3.11+ installation
2. ✅ Creates virtual environment
3. ✅ Installs dependencies
4. ✅ Creates configuration directory (`%USERPROFILE%\.packetbuddy`)
5. ✅ Optionally configures NeonDB cloud sync
6. ✅ Initializes local database
7. ✅ Creates Windows Task Scheduler task (auto-starts on login)
8. ✅ Adds `pb` command to PATH (optional)

#### Step 3: Access Dashboard

The service is now running in the background! Open your browser and go to:

```
http://127.0.0.1:7373/dashboard
```

**That's it!** PacketBuddy will now track your network usage 24/7 and auto-start on every login.

#### Windows Service Control

```batch
# Start service manually
start.bat

# Stop service
stop.bat

# Check service status
schtasks /query /tn "PacketBuddy"

# View service in Task Scheduler
taskschd.msc
```

#### Windows: Automatic Crash Recovery (Watchdog)

PacketBuddy includes a lightweight watchdog that monitors the service and automatically restarts it if it crashes (e.g., during high-load exports).

**To enable the watchdog:**

Run this in **PowerShell as Administrator**:

```powershell
$action = New-ScheduledTaskAction -Execute "c:\Users\$env:USERNAME\packet-buddy\watchdog.bat"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 0)
Register-ScheduledTask -TaskName "PacketBuddyWatchdog" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
Start-ScheduledTask -TaskName "PacketBuddyWatchdog"
```

**Verification:**

- **Check status**: `Get-ScheduledTask -TaskName "PacketBuddyWatchdog"`
- **How it works**: Polls `http://127.0.0.1:7373/api/health` every 30s; restarts `PacketBuddy` task if unresponsive.

---

### macOS Installation

#### Step 1: Clone Repository

```bash
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy
```

#### Step 2: Run Setup Script

```bash
chmod +x service/macos/setup.sh
./service/macos/setup.sh
```

**What the setup does:**

1. ✅ Verifies Python 3.11+ installation
2. ✅ Creates virtual environment
3. ✅ Installs dependencies
4. ✅ Creates configuration directory (`~/.packetbuddy`)
5. ✅ Optionally configures NeonDB
6. ✅ Initializes database
7. ✅ Creates LaunchAgent (auto-starts on login)
8. ✅ Adds `pb` command to PATH

#### Step 3: Access Dashboard

```bash
open http://127.0.0.1:7373/dashboard
```

#### macOS Service Control

```bash
# Start service
pb service start

# Stop service
pb service stop

# Restart service
pb service restart

# Check service status
launchctl list | grep packetbuddy
```

---

### Linux Installation

#### Step 1: Clone Repository

```bash
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy
```

#### Step 2: Run Setup Script

```bash
bash service/linux/setup.sh
```

**What the setup does:**

1. ✅ Checks Python 3.11+ installation
2. ✅ Creates virtual environment
3. ✅ Installs dependencies
4. ✅ Creates configuration directory (`~/.packetbuddy`)
5. ✅ Optionally configures NeonDB
6. ✅ Initializes database
7. ✅ Creates systemd user service (auto-starts on login)
8. ✅ Adds `pb` command to PATH

#### Step 3: Access Dashboard

```bash
xdg-open http://127.0.0.1:7373/dashboard
# Or open in browser: http://127.0.0.1:7373/dashboard
```

#### Linux Service Control

```bash
# Start service
systemctl --user start packetbuddy.service

# Stop service
systemctl --user stop packetbuddy.service

# Restart service
systemctl --user restart packetbuddy.service

# Check service status
systemctl --user status packetbuddy.service

# View logs
journalctl --user -u packetbuddy.service -f
```

---

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PacketBuddy                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   Monitor    │─────▶│   Storage    │               │
│  │  (psutil)    │      │  (SQLite)    │               │
│  └──────────────┘      └──────────────┘               │
│         │                      │                       │
│         │                      │                       │
│         ▼                      ▼                       │
│  ┌──────────────┐      ┌──────────────┐               │
│  │  FastAPI     │◀─────│    Sync      │               │
│  │   Server     │      │  (NeonDB)    │               │
│  └──────────────┘      └──────────────┘               │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐                                     │
│  │  Dashboard   │                                     │
│  │  (HTML/JS)   │                                     │
│  └──────────────┘                                     │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **Monitor** (`src/core/monitor.py`)
   - Uses `psutil` to read network interface statistics
   - Polls every 1 second (configurable)
   - Detects and handles counter resets (sleep/resume)
   - Filters anomalies (>1GB/s spikes)

2. **Storage** (`src/core/storage.py`)
   - Local SQLite database (`~/.packetbuddy/packetbuddy.db`)
   - Batch writes every 30 seconds to reduce disk I/O
   - Transaction-safe with automatic rollback

3. **Sync** (`src/core/sync.py`)
   - Optional cloud sync to NeonDB (PostgreSQL)
   - Syncs every 60 seconds
   - Automatic retry with exponential backoff
   - Works offline (buffers locally)

4. **API Server** (`src/api/server.py`)
   - FastAPI server on `http://127.0.0.1:7373`
   - Serves dashboard and REST API
   - CORS enabled for development

5. **Dashboard** (`dashboard/`)
   - Static HTML/CSS/JavaScript
   - Chart.js for visualizations
   - Auto-refreshes every 2-60 seconds

---

## Dashboard Overview

### Live Speed Monitor

Real-time upload/download speeds with animated progress bars.

### Today's Usage

- Total uploaded/downloaded today
- Cost in ₹ (Indian Rupees)
- Upload/Download distribution pie chart

### Lifetime Statistics

- Total data usage since installation
- Cumulative cost tracking
- Average daily usage

### Monthly Breakdown

- Interactive bar chart showing daily usage
- Navigate between months
- Hover for detailed stats

### Quick Stats

- Peak speed recorded
- Active devices (if using NeonDB)
- Data points collected
- Last update timestamp

---

## Multi-Device Setup

Track multiple devices (Windows PC, MacBook, Linux server) with a single database!

### Step 1: Create NeonDB Account

1. Go to [neon.tech](https://neon.tech)
2. Sign up for free account
3. Create a new database
4. Copy your connection string (format: `postgresql://user:pass@host.neon.tech/db?sslmode=require`)

### Step 2: Configure Each Device

**During setup, when prompted:**

```
Enable cloud sync? (y/n) [n]: y
NeonDB URL: postgresql://user:pass@host.neon.tech/db?sslmode=require
```

**Or set environment variable before setup:**

```bash
# macOS/Linux
export NEON_DB_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require"

# Windows PowerShell
$env:NEON_DB_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require"

# Windows Command Prompt
setx NEON_DB_URL "postgresql://user:pass@host.neon.tech/db?sslmode=require"
```

### Step 3: Run Setup on Each Device

Follow the platform-specific installation steps above. Each device will:

- Get a unique device ID
- Sync to the same NeonDB database
- Show combined stats in the dashboard

### Free Tier Limits

NeonDB free tier includes:

- ✅ 10 GB storage (enough for 10+ years of data)
- ✅ Unlimited devices
- ✅ Always-on database

PacketBuddy uses ~1MB per month per device.

---

## Configuration

Configuration file location: `~/.packetbuddy/config.toml` (or `%USERPROFILE%\.packetbuddy\config.toml` on Windows)

### Example Configuration

```toml
[api]
host = "127.0.0.1"
port = 7373
cors_enabled = true

[monitoring]
poll_interval = 1  # Seconds between network checks
batch_write_interval = 30  # Seconds between database writes
interface = "auto"  # Network interface (auto-detect or specify like "en0")

[sync]
enabled = false  # Set to true if using NeonDB
interval = 60  # Seconds between cloud syncs

[cost]
rate_per_gb = 7.50  # Cost per GB in ₹ (INR)
currency = "INR"
```

### Common Customizations

**Change API Port:**

```toml
[api]
port = 8080
```

**Reduce Resource Usage:**

```toml
[monitoring]
poll_interval = 2  # Poll every 2 seconds instead of 1
batch_write_interval = 60  # Write to DB every 60 seconds
```

**Specify Network Interface:**

```toml
[monitoring]
interface = "en0"  # macOS Wi-Fi
# interface = "eth0"  # Linux Ethernet
# interface = "Wi-Fi"  # Windows
```

**Adjust Cost Rate:**

```toml
[cost]
rate_per_gb = 10.00  # ₹10 per GB
```

**Control Automatic Updates:**

```toml
[auto_update]
enabled = true          # Enable automatic updates (recommended)
check_on_startup = true # Check for updates when service starts
auto_apply = true       # Automatically apply updates
auto_restart = true     # Automatically restart after update
```

**Disable Automatic Updates** (not recommended):

```toml
[auto_update]
enabled = false  # Disable all automatic updates
```

---

## Automatic Updates

**PacketBuddy automatically updates itself!** 🎉

### How It Works

1. **Automatic Check**: Service checks for updates 10 seconds after startup
2. **Automatic Download**: If update is available, it's downloaded automatically
3. **Automatic Apply**: Update is applied in the background
4. **Automatic Restart**: Service restarts to apply changes (seamless)

### Manual Updates

You can also force an update manually:

```bash
# Check for updates
pb update --check-only

# Force update immediately
pb update

# Force update even if already up to date
pb update --force
```

### Configuration

Control automatic update behavior in `~/.packetbuddy/config.toml`:

```toml
[auto_update]
enabled = true          # Master switch for auto-updates
check_on_startup = true # Check when service starts
auto_apply = true       # Automatically download and apply
auto_restart = true     # Restart service after update
```

### Disabling Auto-Updates

Not recommended, but you can disable if needed:

```toml
[auto_update]
enabled = false
```

Then update manually with `pb update` when you want.

---

## CLI Commands

After installation, use the `pb` command from anywhere:

### Usage Statistics

```bash
# Today's usage
pb today

# Lifetime summary
pb summary

# Monthly breakdown
pb month

# Custom date range
pb range --from 2026-01-01 --to 2026-01-31
```

### Service Management

```bash
# Start background service
pb service start

# Stop service
pb service stop

# Restart service
pb service restart

# Check service status
pb service status
```

### Data Export

```bash
# Export to CSV (with peak speeds)
pb export --format csv --output data.csv

# Export to JSON (comprehensive statistics)
pb export --format json --output data.json

# Export beautiful HTML year wrap-up
pb export --format html --output wrap_up.html

# Export TOON format (Token Optimized - ~60% fewer tokens for LLMs)
pb export --llm
```

**New in v1.4.0:** All exports now include peak speed data and comprehensive statistics!

#### Export Formats Comparison

| Format | Best For | Features |
|--------|----------|----------|
| **CSV** | Spreadsheet analysis | Daily data with peak speeds |
| **JSON** | Programmatic use | Complete statistics, human-readable values |
| **HTML** | Sharing & presentation | Beautiful year wrap-up, Spotify-style |
| **TOON** | LLM analysis | Token-optimized format, ~60% fewer tokens |

#### TOON Format (New!)

PacketBuddy now exports data in **TOON (Token Optimized Object Notation)** format for LLM analysis:

```toml
[totals]
bytes_sent = 48547545088
bytes_received = 132923842560
total_bytes = 181471387648
human = {sent="45.2 GB", received="123.8 GB", total="169.0 GB"}

[year_2026]
bytes_sent = 12345678
bytes_received = 98765432
total_bytes = 111111110
days = 22

[records]
peak_speed_bps = 13107200
peak_speed_human = "12.5 MB/s"
```

**Benefits:**
- 🚀 ~60% fewer tokens than markdown
- 📊 All data preserved in compact format
- 🤖 Optimized for ChatGPT, Claude, and other LLMs
- 📝 Human-readable values included

### Updates

```bash
# Check for updates
pb update --check-only

# Update to latest version
pb update
```

### Example Output

```
📊 Today's Usage

╒════════════╤═══════════╕
│ Type       │ Amount    │
╞════════════╪═══════════╡
│ Uploaded   │ 118.31 MB │
├────────────┼───────────┤
│ Downloaded │ 93.80 MB  │
├────────────┼───────────┤
│ Total      │ 212.11 MB │
├────────────┼───────────┤
│ Cost       │ ₹1.59     │
╘════════════╧═══════════╛
```

---

## Troubleshooting

### Windows: Service Not Starting from Task Scheduler

**Symptoms:**

- Works from Command Prompt
- Fails when run via Task Scheduler

**Solution:**
Re-run the setup script as Administrator:

```batch
service\windows\setup.bat
```

**Details:** See [Windows Task Scheduler Fix Guide](docs/WINDOWS_TASK_SCHEDULER_FIX.md)

---

### Dashboard Not Loading

**Check if service is running:**

```bash
# Test API health endpoint
curl http://127.0.0.1:7373/api/health

# Should return: {"status":"ok","hostname":"..."}
```

**If service is not running:**

```bash
# Windows
schtasks /run /tn "PacketBuddy"

# macOS
launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon

# Linux
systemctl --user start packetbuddy.service
```

**Check logs:**

```bash
# Windows
type %USERPROFILE%\.packetbuddy\stderr.log

# macOS/Linux
tail -f ~/.packetbuddy/stderr.log
```

---

### Port Already in Use

**Error:** `Address already in use: 127.0.0.1:7373`

**Solution:** Change port in config:

```toml
[api]
port = 8080  # Or any other available port
```

Then restart service.

---

### NeonDB Sync Failing

**Verify connection string:**

```bash
# macOS/Linux
echo $NEON_DB_URL

# Windows
echo %NEON_DB_URL%
```

**Test connection:**

```bash
psql "$NEON_DB_URL"
```

**Check sync logs:**

```bash
tail -f ~/.packetbuddy/stderr.log | grep sync
```

---

### High Resource Usage

**Reduce polling frequency:**

```toml
[monitoring]
poll_interval = 2  # Poll every 2 seconds
batch_write_interval = 60  # Write every 60 seconds
```

**Disable cloud sync:**

```toml
[sync]
enabled = false
```

---

### Python Not Found (Windows)

**Error:** `Python 3.11+ not found`

**Solution:**

1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Restart Command Prompt
4. Verify: `python --version`

---

## FAQ

### Q: Does PacketBuddy slow down my internet?

**A:** No. PacketBuddy only reads network statistics from your OS. It doesn't intercept or modify network traffic. Resource usage is <40MB RAM and <0.5% CPU.

---

### Q: What data does PacketBuddy collect?

**A:** Only bytes sent/received and timestamps. No websites, apps, IP addresses, or personal data. See [Privacy & Security](#privacy--security).

---

### Q: Can I track multiple devices?

**A:** Yes! Use NeonDB cloud sync (free tier) to track unlimited devices in one database. See [Multi-Device Setup](#multi-device-setup).

---

### Q: Does it work on mobile hotspot/tethering?

**A:** Yes. PacketBuddy automatically detects your active network interface, whether it's Wi-Fi, Ethernet, or mobile hotspot.

---

### Q: How accurate is the tracking?

**A:** Very accurate. PacketBuddy reads kernel-level network statistics directly from your OS. It includes smart filtering to avoid data inflation from system overhead.

---

### Q: Can I export my data?

**A:** Yes. Use `pb export --format csv` or access `/api/export?format=csv` in your browser.

---

### Q: Does it work offline?

**A:** Yes. Local tracking works 100% offline. Cloud sync (optional) requires internet but buffers data locally when offline.

---

### Q: How do I uninstall?

**Windows:**

```batch
schtasks /delete /tn "PacketBuddy" /f
rmdir /s /q %USERPROFILE%\.packetbuddy
```

**macOS:**

```bash
launchctl unload ~/Library/LaunchAgents/com.packetbuddy.plist
rm ~/Library/LaunchAgents/com.packetbuddy.plist
rm -rf ~/.packetbuddy
```

**Linux:**

```bash
systemctl --user stop packetbuddy.service
systemctl --user disable packetbuddy.service
rm ~/.config/systemd/user/packetbuddy.service
rm -rf ~/.packetbuddy
```

---

## Privacy & Security

### Local-First Architecture

- ✅ All data written to local SQLite first
- ✅ Cloud sync is completely optional
- ✅ No telemetry or analytics
- ✅ No third-party tracking

### What Data is Collected?

```json
{
  "timestamp": "2026-01-08T10:30:00Z",
  "bytes_sent": 1048576,
  "bytes_received": 2097152,
  "device_id": "uuid-here"
}
```

**That's it!** No:

- ❌ Websites visited
- ❌ App identification
- ❌ Personal information
- ❌ IP addresses
- ❌ DNS queries

### Security

- 🔒 API binds to `127.0.0.1` only (no external access)
- 🔒 NeonDB uses TLS encryption
- 🔒 No secrets in code
- 🔒 Environment variables for credentials

---

## Performance

PacketBuddy is designed to be invisible:

| Metric | Value |
|--------|-------|
| CPU Usage | 0.2% - 0.5% |
| RAM Usage | 28MB - 40MB |
| Disk I/O | ~5KB/s |
| Network Overhead | ~1KB/30s (sync) |
| Battery Impact | Minimal |

**Comparison:**

- 🟢 PacketBuddy: 30MB RAM, 0.3% CPU
- 🔴 Chrome Tab: 200MB+ RAM, 2-5% CPU
- 🔴 Spotify: 150MB+ RAM, 1-3% CPU

---

## API Reference

Base URL: `http://127.0.0.1:7373/api`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service status & device info |
| `/live` | GET | Current upload/download speed |
| `/today` | GET | Today's total usage |
| `/month?month=YYYY-MM` | GET | Monthly breakdown |
| `/range?from=DATE&to=DATE` | GET | Custom date range |
| `/summary` | GET | Lifetime totals |
| `/export?format=json\|csv` | GET | Export all data |

### Example Response

```json
{
  "bytes_sent": 125829120,
  "bytes_received": 524288000,
  "total_bytes": 650117120,
  "human_readable": {
    "sent": "120.00 MB",
    "received": "500.00 MB",
    "total": "620.00 MB"
  },
  "cost": {
    "total": {
      "cost": 4.88,
      "cost_formatted": "₹4.88"
    }
  }
}
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Credits

Built with:

- [Python](https://python.org) - Core language
- [FastAPI](https://fastapi.tiangolo.com/) - HTTP server
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [NeonDB](https://neon.tech/) - PostgreSQL database

---

## Support

- 📫 **Issues**: [GitHub Issues](https://github.com/instax-dutta/packet-buddy/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/instax-dutta/packet-buddy/discussions)
- ⭐ **Star us**: [GitHub](https://github.com/instax-dutta/packet-buddy)
- 🔄 **Auto-Update**: Run `pb update` to get latest features

---

## Keywords

`network monitor`, `bandwidth tracker`, `internet usage monitor`, `data usage tracker`, `network traffic analysis`, `ISP bill calculator`, `multi-device tracking`, `cross-platform network tool`, `Python network utility`, `real-time bandwidth monitor`, `network usage dashboard`, `data consumption tracker`, `open source network monitor`, `lightweight bandwidth tool`, `macOS network monitor`, `Windows bandwidth tracker`, `Linux network utility`

---

<div align="center">

**Made with ❤️ for the internet community**

[⬆ Back to Top](#packetbuddy---network-usage--bandwidth-tracker)

</div>
