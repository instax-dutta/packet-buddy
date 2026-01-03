<div align="center">

# 📊 PacketBuddy — Open Source Network Usage & Bandwidth Tracker

### *The Lightweight, Real-Time Internet Data Monitor for macOS, Windows & Linux*

[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue?style=for-the-badge)](https://github.com/instax-dutta/packet-buddy)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

**PacketBuddy is an ultra-lightweight bandwidth monitor and network traffic tracker designed to help you manage internet data usage across all your devices with a beautiful dashboard and zero configuration.**

[Quick Start](#-quick-start-3-minutes) • [Features](#-features) • [Screenshots](#-dashboard-preview) • [Keywords](#-search-keywords) • [Setup](#%EF%B8%8F-installation)
</div>

---

## 🎯 What is PacketBuddy?

PacketBuddy is a **high-performance bandwidth tracker** and **network usage utility** that:

- 📈 **Real-time Traffic Monitoring**: Tracks every byte of your upload/download in real-time.
- 🌐 **Cross-Platform Sync**: Monitor your MacBook, Windows PC, and servers in one centralized location.
- 🎨 **Visual Analytics**: Beautiful, interactive charts to visualize your internet habits and daily data consumption.
- ⚡ **Minimalist Design**: Uses less than 0.5% CPU and 40MB RAM — essentially invisible.
- 🔒 **Privacy Focused**: All data stored locally in SQLite; cloud sync (NeonDB) is 100% optional.
- 🚀 **Effortless Setup**: One-command installation for background monitoring.

### **Perfect for:**

- 📊 **Capped Data Connections**: Stay under your ISP's monthly limit with precise tracking.
- 💰 **Billing Accuracy**: Verify your ISP's bandwidth reports and calculate costs in INR (₹).
- 📱 **Multi-Device Management**: See exactly how much data your phone, laptop, and PC are using.
- 🎓 **Network Troubleshooting**: Identify ghost-usage and data-heavy applications.

---

## ✨ Features

### 🎨 **Beautiful Dashboard**

- Real-time upload/download speed
- Daily, monthly, and lifetime stats  
- **Indian Rupee (₹) Cost Tracking** (@ ₹7.50/GB)
- Interactive charts with Chart.js
- Dark theme optimized

### ⚙️ **Smart Monitoring**

- **Smart Interface Detection**: Locks to primary gateway (e.g., Wi-Fi `en0`)
- **Zero Data Inflation**: Ignores Apple/System overhead (AirDrop, Sidecar, etc.)
- **Battery-Aware Logic**: Self-optimizes when unplugged to save power
- **Local Time Accuracy**: Data resets at 12:00 AM in *your* timezone
- **Automatic Failsafes**: Handles sleep, resume, and counter resets gracefully

### 🌐 **Multi-Device Support**

- Track unlimited devices
- Single NeonDB database  
- Device identification
- Aggregate reporting

### 🔧 **Zero Configuration**

- One-command installation
- Auto-starts on boot
- Background daemon
- **Automatic updates** with `pb update`

---

## 📸 Dashboard Preview

<div align="center">

![PacketBuddy Dashboard](docs/images/dashboard.png)

*Real-time network monitoring with gradient-accented stats and interactive charts*

</div>

### Dashboard Features

- **⚡ Live Speed Monitor** - Real-time upload/download rates with premium status bars
- **📅 Today's Usage** - Integrated **₹ Cost Tracking** with clean statistics
- **🌐 Lifetime Totals** - Global usage and cumulative financial tracking
- **📊 Monthly Chart** - Day-by-day interactive breakdown with Chart.js
- **🎯 Distribution Chart** - Real-time Upload vs Download pie distribution
- **📈 Smart Insights** - Average daily usage, peak speeds, and active devices

---

## 🚀 Quick Start (3 Minutes)

### macOS

```bash
# 1. Clone the repository
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy

# 2. Run the one-time setup script
chmod +x service/macos/setup.sh
./service/macos/setup.sh

# 3. Open the dashboard
open http://127.0.0.1:7373/dashboard
```

**That's it!** PacketBuddy is now tracking your network usage and will auto-start on every boot.

### Windows

```bat
# 1. Clone the repository (or download ZIP)
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy

# 2. Right-click setup.bat > Run as administrator  
cd service\windows
setup.bat

# 3. Open the dashboard
start http://127.0.0.1:7373/dashboard
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.11 or higher** ([Download here](https://www.python.org/downloads/))
- **Git** (optional, for cloning)
- **NeonDB Account** (optional, for multi-device sync - [Free tier available](https://neon.tech))

### Manual Installation

<details>
<summary><b>Click to expand step-by-step guide</b></summary>

#### Step 1: Get the Code

```bash
# Clone the repository
git clone https://github.com/instax-dutta/packet-buddy.git
cd packet-buddy

# Or download and extract ZIP from GitHub
```

#### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure (Optional)

```bash
# Copy example config
mkdir -p ~/.packetbuddy
cp config.example.toml ~/.packetbuddy/config.toml

# Edit if needed
nano ~/.packetbuddy/config.toml
```

#### Step 4: Set Up NeonDB (Optional)

If you want to track multiple devices:

1. Create a free account at [neon.tech](https://neon.tech)
2. Create a new database
3. Copy your connection string
4. Set environment variable:

```bash
# macOS/Linux
export NEON_DB_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require"

# Windows PowerShell
$env:NEON_DB_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require"
```

#### Step 5: Start PacketBuddy

```bash
# Start the server
python -m src.api.server
```

#### Step 6: Set Up Auto-Start

**macOS:**

```bash
# Use the provided script (recommended)
./service/macos/setup.sh

# Or manually:
cp service/macos/com.packetbuddy.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.packetbuddy.plist
```

**Windows:**

```powershell
# Run as Administrator
.\service\windows\install-service.ps1
```

</details>

---

## 📱 Using PacketBuddy

### Dashboard (Web Interface)

Visit **<http://127.0.0.1:7373/dashboard>** in any browser.

The dashboard auto-refreshes:

- Live speed: Every 2 seconds
- Today's stats: Every 30 seconds
- Lifetime stats: Every 60 seconds

### Command Line Interface

```bash
# Using the 'pb' command (after setup):
pb today      # Today's usage
pb summary    # Lifetime stats
pb month      # Monthly breakdown
pb update     # Check for updates
pb export     # Export data

# Or using Python directly:
python -m src.cli.main today
python -m src.cli.main summary
python -m src.cli.main update --check-only
```

### Example CLI Output

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
╘════════════╧═══════════╛
```

---

## 🌐 Multi-Device Setup

PacketBuddy supports tracking multiple devices with a single NeonDB database!

### How It Works

Each device gets a unique ID. Data is tagged with:

- Device hostname
- Operating system
- Unique device UUID

### Setup Process

1. **Set up NeonDB** (one time):
   - Create account at [neon.tech](https://neon.tech)
   - Create database
   - Note your connection string

2. **Configure each device**:

   ```bash
   # On MacBook
   export NEON_DB_URL="your-connection-string"
   ./service/macos/setup.sh
   
   # On Windows PC
   $env:NEON_DB_URL="your-connection-string"
   .\service\windows\setup.ps1
   ```

3. **View combined data**:
   - All devices sync to the same database
   - Dashboard shows device-specific and aggregate data
   - No configuration needed - just works!

### Free Tier Limits

NeonDB free tier includes:

- ✅ **10 GB storage** (enough for years of data)
- ✅ **Unlimited devices**
- ✅ **Always-on database**

PacketBuddy uses ~1MB per month per device, so you can track:

- 📱 **800+ devices** on free tier
- 📅 **10+ years** of data per device

---

## ⚡ Performance

PacketBuddy is designed to be **invisible** on your system:

| Metric | Value |
|--------|-------|
| CPU Usage | 0.2% - 0.5% |
| RAM Usage | 28MB - 40MB |
| Disk I/O | ~5KB/s |
| Network Overhead | Negligible (~1KB/30s sync) |
| Battery Impact | Minimal |

**Comparison:**

- 🟢 **PacketBuddy**: 30MB RAM, 0.3% CPU
- 🔴 **Chrome Tab**: 200MB+ RAM, 2-5% CPU
- 🔴 **Spotify**: 150MB+ RAM, 1-3% CPU

---

## 🔒 Privacy & Security

### Local-First Architecture

- ✅ All data written to local SQLite first
- ✅ Cloud sync is **completely optional**
- ✅ No telemetry or analytics
- ✅ No third-party tracking

### What Data is Collected?

```json
{
  "timestamp": "2026-01-03T09:30:00Z",
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

## 🛡️ Automatic Failsafes

PacketBuddy includes multiple layers of protection:

### Network Counter Resets

```python
if new_value < old_value:
    # Sleep/resume detected - skip and reset
    skip_sample()
```

### Anomaly Detection

```python
if delta > 1GB/second:
    # Likely a driver glitch - skip
    skip_sample()
```

### Crash Recovery

- Auto-restart on crash (LaunchAgent/Task Scheduler)
- Graceful shutdown with data flush
- Transaction-safe writes

### Network Interruptions

- Automatic retry with exponential backoff
- Local buffering during offline periods
- Never lose data

---

## 📊 API Reference

Base URL: `http://127.0.0.1:7373/api`

### Endpoints

| Endpoint | Method | Description | Response Time |
|----------|--------|-------------|---------------|
| `/health` | GET | Service status & device info | <10ms |
| `/live` | GET | Current upload/download speed | <10ms |
| `/today` | GET | Today's total usage | <50ms |
| `/month?month=YYYY-MM` | GET | Monthly breakdown | <100ms |
| `/range?from=DATE&to=DATE` | GET | Custom date range | <200ms |
| `/summary` | GET | Lifetime totals | <50ms |
| `/export?format=json\|csv` | GET | Export all data | Varies |

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
  }
}
```

---

## 🎨 Customization

### Change Port

Edit `~/.packetbuddy/config.toml`:

```toml
[api]
port = 8080  # Your preferred port
```

### Adjust Polling Rate

```toml
[monitoring]
poll_interval = 2  # Poll every 2 seconds instead of 1
```

### Disable Cloud Sync

```toml
[sync]
enabled = false
```

### Batch Write Interval

```toml
[monitoring]
batch_write_interval = 10  # Write to SQLite every 10 seconds
```

---

## 🧹 Maintenance

### View Logs

**macOS:**

```bash
tail -f ~/.packetbuddy/stdout.log
tail -f ~/.packetbuddy/stderr.log
```

**Windows:**

```powershell
Get-Content ~\.packetbuddy\stdout.log -Tail 50 -Wait
```

### Restart Service

**macOS:**

```bash
launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon
```

**Windows:**

```powershell
Restart-ScheduledTask -TaskName "PacketBuddy"
```

### Check Database Size

```bash
ls -lh ~/.packetbuddy/packetbuddy.db
```

### Backup Data

```bash
# Backup local database
cp ~/.packetbuddy/packetbuddy.db ~/packetbuddy-backup-$(date +%Y%m%d).db

# Export to CSV
python -m src.cli.main export --format csv --output backup.csv
```

---

## 🐛 Troubleshooting

<details>
<summary><b>Service won't start</b></summary>

1. Check if port 7373 is in use:

   ```bash
   lsof -i :7373  # macOS/Linux
   netstat -ano | findstr :7373  # Windows
   ```

2. View error logs:

   ```bash
   tail -f ~/.packetbuddy/stderr.log
   ```

3. Test manually:

   ```bash
   source venv/bin/activate
   python -m src.api.server
   ```

</details>

<details>
<summary><b>Dashboard not loading</b></summary>

1. Check if service is running:

   ```bash
   curl http://127.0.0.1:7373/api/health
   ```

2. Try a different browser
3. Clear browser cache
4. Check firewall settings

</details>

<details>
<summary><b>NeonDB sync failing</b></summary>

1. Verify connection string:

   ```bash
   echo $NEON_DB_URL
   ```

2. Test connection:

   ```bash
   psql "$NEON_DB_URL"
   ```

3. Check logs for specific errors
4. Verify network connectivity

</details>

<details>
<summary><b>High resource usage</b></summary>

Increase poll interval in config:

```toml
[monitoring]
poll_interval = 2  # or 5 for even lower usage
```

</details>

---

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Fast 3-minute setup
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [API Documentation](#-api-reference) - HTTP API reference
- [GitHub Repository](https://github.com/instax-dutta/packet-buddy) - Star us! ⭐

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

Built with:

- [Python](https://python.org) - Core language
- [FastAPI](https://fastapi.tiangolo.com/) - HTTP server
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
- [Chart.js](https://www.chartjs.org/) - Data visualization
- [NeonDB](https://neon.tech/) - PostgreSQL database

---

## 💬 Support

- 📫 **Issues**: [GitHub Issues](https://github.com/instax-dutta/packet-buddy/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/instax-dutta/packet-buddy/discussions)
- ⭐ **Star us**: [GitHub](https://github.com/instax-dutta/packet-buddy)
- 🔄 **Auto-Update**: Run `pb update` to get the latest features

---

## 🔍 Search Keywords

`network monitor`, `bandwidth tracker`, `internet usage monitor`, `macOS data tracker`, `Windows bandwidth tool`, `Linux network monitor`, `data usage alert`, `ISP bill calculator`, `network traffic analysis`, `Python network utility`, `open source data tracker`, `real-time bandwidth monitor`, `network usage dashboard`, `data consumption tracker`, `network utility macOS`, `systemd network service`.

---

<div align="center">

**Made with ❤️ for the internet community**

[⬆ Back to Top](#-packetbuddy--open-source-network-usage--bandwidth-tracker)

</div>
