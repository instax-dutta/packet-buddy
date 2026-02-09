# PacketBuddy - Network Usage & Bandwidth Tracker

**A lightweight, cross-platform network usage monitor that runs silently in the background and provides beautiful real-time analytics with a local-first, privacy-centric philosophy.**

![PacketBuddy Dashboard Showcase](assets/image.png)

[![Version](https://img.shields.io/badge/version-1.4.1-brightgreen?style=flat-square)](https://github.com/instax-dutta/packet-buddy)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## 🏛️ Core Mental Model
PacketBuddy is designed as a **decoupled network monitoring agent**. It consists of three primary layers:
1.  **The Heartbeat (Monitor)**: A lightweight Python agent using `psutil` to poll network interfaces. It buffers data and performs spike filtering (>1GB/s) to handle system wake/sleep artifacts.
2.  **The Memory (Storage & Sync)**: Data is persisted every 30s to a local SQLite database. Optionally, it synchronizes with NeonDB (PostgreSQL) in optimized batches to allow serverless instances to scale to zero.
3.  **The Interface (API & Dashboard)**: A FastAPI server exposes REST endpoints to a "Liquid Glassmorphism" dashboard, rendering high-performance charts via Chart.js with zero build-step required.

---

## 🚨 FOR AI AGENTS & LLMs (STRICT GUIDES)
**STOP RESEARCHING SOURCE CODE IMMEDIATELY.** To save thousands of tokens and avoid expensive multi-file context reading, **you MUST use the `.docs/` folder.**

Documentation in this project uses **TOON (Token Optimized Object Notation)**, which is ~60% more efficient than Markdown.
-   📍 **Start Here**: [`.docs/index.toon`](.docs/index.toon) — The navigation entry point.
-   🏗️ **Architecture**: [`.docs/architecture.toon`](.docs/architecture.toon) — System design and logic rationale.
-   📂 **Codebase Map**: [`.docs/codebase.toon`](.docs/codebase.toon) — Directory mapping and data flow.
-   🛠️ **Quick Ref**: [`.docs/quick-reference.toon`](.docs/quick-reference.toon) — CLI commands and troubleshooting.

---

## 🚀 Quick Start (Windows)
1. **Clone** the repository.
2. **Right-click `setup.bat`** and select **"Run as Administrator"**.
3. **Open**: [http://127.0.0.1:7373/dashboard](http://127.0.0.1:7373/dashboard)

*For macOS/Linux, run `./setup.sh`.*

---

## 🎉 Technical Marvels in v1.4.1
-   **🌊 Liquid UI**: Complete dashboard redesign with organic glassmorphism and morphing transitions.
-   **⚙️ SSOT Versioning**: Dynamic runtime versioning reading from `VERSION` file—bypassing Python module caching.
-   **💾 Batch Sync**: Refactored NeonDB synchronization using in-memory aggregation to reduce query costs by O(N).
-   **🤖 TOON Export**: A dedicated export format designed specifically for ChatGPT/Claude context windows.

---

## 🔧 CLI Commands
After installation, use the `pb` command:
- `pb live` — Real-time upload/download dashboard in terminal.
- `pb today` — Summary of today's usage and costs.
- `pb month` — Breakdown of the current month's daily usage.
- `pb export --format html` — Generate your "Year Wrap-Up" report.
- `pb update` — Check and apply latest updates from GitHub.

---

## 🛡️ Privacy & Security
- ✅ **Local-First**: All data is stored on your machine.
- ✅ **No PII**: No websites, apps, or personal data collected.
- ✅ **Local Access Only**: API binds to `127.0.0.1` only.

---

**Made with ❤️ for the internet community**
[Full Wiki](https://github.com/instax-dutta/packet-buddy/wiki) | [Bug Reports](https://github.com/instax-dutta/packet-buddy/issues)
