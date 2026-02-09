# PacketBuddy - Network Usage & Bandwidth Tracker

**A lightweight, cross-platform network usage monitor that runs silently in the background and provides beautiful real-time analytics.**

![PacketBuddy Dashboard Showcase](assets/image.png)

[![Version](https://img.shields.io/badge/version-1.4.1-brightgreen?style=flat-square)](https://github.com/instax-dutta/packet-buddy)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## 🚀 Quick Start (Windows)

1. **Clone** the repository.
2. **Right-click `setup.bat`** (in this folder) and select **"Run as Administrator"**.
3. **Done!** Open your browser to: [http://127.0.0.1:7373/dashboard](http://127.0.0.1:7373/dashboard)

*For macOS/Linux, run `./setup.sh`.*

---

## 📦 Installation & Updates

PacketBuddy can be installed or updated directly via `pip` or the built-in CLI:

### First Time Installation
```bash
pip install packetbuddy
```

### Update to Latest Version
```bash
pip install --upgrade packetbuddy
```

### Force Update (via CLI)
```bash
pb update --force
```

---

## 🎉 What's New in v1.4.1

- **🌊 Liquid / Fluid UI**: Complete dashboard redesign with organic glassmorphism, morphing transitions, and a "Year Wrap-Up" experience.
- **🛡️ SSOT Versioning**: Dynamic runtime versioning that bypasses Python caching—making updates seamless.
- **🚀 Optimized Sync**: Refactored NeonDB synchronization with batch aggregation to reduce API calls and costs.
- **📊 Enhanced Export**: Improved CSV, JSON, and TOON export efficiency for both humans and AI agents.

---

## 📖 Documentation & AI Guide

We use **TOON (Token Optimized Object Notation)** for documentation, which is ~60% more efficient for AI agents to process.

If you are a developer or an **AI Assistant**, start here:
- [**Documentation Index (.docs/index.toon)**](.docs/index.toon) — Entry point for understanding the codebase.
- [**Codebase Overview**](.docs/codebase.toon) — Deep dive into the project structure.
- [**Quick Reference**](.docs/quick-reference.toon) — Commands, API endpoints, and troubleshooting.

---

## 🔧 CLI Commands

After installation, use the `pb` command:
- `pb live` — Real-time upload/download dashboard in terminal.
- `pb today` — Summary of today's usage and costs.
- `pb month` — Breakdown of the current month's daily usage.
- `pb export --format html` — Generate your Year Wrap-Up report.
- `pb update` — Check and apply latest updates from GitHub.

---

## 🛡️ Privacy & Security

- ✅ **Local-First**: All data is stored on your machine.
- ✅ **No PII**: No websites, apps, or personal data collected.
- ✅ **Local Access Only**: API binds to `127.0.0.1` only.

---

**Made with ❤️ for the internet community**  
[Full Wiki](https://github.com/instax-dutta/packet-buddy/wiki) | [Bug Reports](https://github.com/instax-dutta/packet-buddy/issues)
