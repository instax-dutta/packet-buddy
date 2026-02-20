# PacketBuddy

**Free, privacy-focused network usage and bandwidth tracking**

![Version](https://img.shields.io/badge/version-1.4.3-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

---

## Introduction

PacketBuddy is a lightweight, privacy-focused application for monitoring your network usage and bandwidth in real-time. Track your internet consumption, visualize historical data, and sync across multiple devices—all without compromising your privacy.

---

## Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Real-time Monitoring** | Live bandwidth usage with instant updates and per-process tracking |
| 💾 **Long-term Storage** | SQLite-based storage with optional NeonDB cloud sync for historical analysis |
| 🔄 **Multi-device Sync** | Synchronize your data across multiple devices securely |
| 🔒 **Privacy-first** | All data stored locally by default. No telemetry, no tracking, no data collection |
| 🖥️ **Cross-platform** | Works seamlessly on Windows, macOS, and Linux |
| ⚡ **Zero Configuration** | Get started in seconds—no complex setup required |

---

## Screenshots

> **Dashboard Showcase Coming Soon**
> 
> The interactive Chart.js dashboard provides:
> - Real-time bandwidth graphs
> - Daily, weekly, and monthly usage statistics
> - Per-application network usage breakdown
> - Customizable date ranges and filters

*Placeholder for dashboard screenshots*

---

## Quick Start

### Windows

1. **Run the setup script as Administrator**
   ```powershell
   # Right-click setup.bat and select "Run as administrator"
   # OR run in elevated PowerShell:
   .\setup.bat
   ```

2. **Access the dashboard**
   
   Open your browser and navigate to: [http://127.0.0.1:7373/dashboard](http://127.0.0.1:7373/dashboard)

### macOS / Linux

1. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Access the dashboard**
   
   Open your browser and navigate to: [http://127.0.0.1:7373/dashboard](http://127.0.0.1:7373/dashboard)

---

## Requirements

- **Python**: 3.11 or higher
- **OS**: Windows 10+, macOS 10.15+, or modern Linux distribution

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | SQLite (local), NeonDB (optional cloud sync) |
| Frontend | Chart.js Dashboard |
| API | RESTful with real-time WebSocket support |

---

## Wiki Pages

- [Installation Guide](Installation.md)
- [Configuration](Configuration.md)
- [API Reference](API-Reference.md)
- [Troubleshooting](Troubleshooting.md)
- [Changelog](Changelog.md)
- [Contributing](Contributing.md)

---

## License

PacketBuddy is released under the [MIT License](../LICENSE).

```
MIT License - Free for personal and commercial use
```

---

## Support

- **Issues**: [GitHub Issues](https://github.com/packetbuddy/packetbuddy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/packetbuddy/packetbuddy/discussions)

---

*Made with ❤️ for privacy-conscious users*
