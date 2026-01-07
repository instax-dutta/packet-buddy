# 🏗️ Technical Architecture & Data Flow

This document details the internal lifecycle of metrics within PacketBuddy. Use this to maintain data integrity across future scaling efforts.

## 1. The Metric Pipeline

1. **Ingestion (`src/core/monitor.py`)**:
    - Polls `psutil.net_io_counters(pernic=True)` every `poll_interval` (default 1s).
    - Performs **Inclusive Summing**: Sums activity across all physical-looking interfaces while filtering out system noise (loopback, AirDrop, internal tunnels).
    - Standardizes on **Decimal (1000-base)** Gigabytes for ISP and ISP-metering accuracy.
    - Calculates the delta between the current and last sample.
2. **Buffering**:
    - Deltas are stored in a memory list (`self.pending_writes`).
    - This minimizes SQLite write lock contention.
3. **Persistence (`src/core/storage.py`)**:
    - Every `batch_write_interval` (default 5s), the buffer is flushed to the `usage_logs` table.
    - Updates `daily_aggregates` and `monthly_aggregates` in the same transaction.
4. **Cloud Integration (`src/core/sync.py`)**:
    - Periodically replicates local logs to NeonDB.
    - Retrieves Network-wide global aggregates for the "Stitched" dashboard view.
5. **Consumption (`src/api/routes.py`)**:
    - FastAPI endpoints query both local and global aggregates to provide a unified network view.

## 2. Cross-Platform Runtime

The application is designed to run as a "headless" daemon.

- **macOS**: `launchd` service path in `~/Library/LaunchAgents`.
- **Windows**: `schtasks` running `pythonw.exe` (headless) with "Highest Privileges".
- **Linux**: `systemd --user` unit managing the background process.
- **CLI Abstraction**: All platforms use the unified `pb service` command group for control.

## 3. Storage Schema (SQLite)

- `usage_logs`: Raw per-flush data (Timestamp, Sent, Received).
- `daily_aggregates`: Primary source for "Today" and "Monthly" charts. Indexed by `(device_id, date)`.
- `devices`: Metadata for multi-device sync mapping.

## 4. Dashboard Communication

The dashboard (`/dashboard`) is a single-page application using:

- **`app.js`**: Periodic fetch loops.
- **`Chart.js`**: Renders the usage history.
- **REST API**: All data communication happens over JSON via the `127.0.0.1:7373/api/*` endpoints.

## 5. Security Protocols

- **Loopback Binding**: The API server MUST only bind to `127.0.0.1` to prevent exposure to the local network.
- **CORS**: Restricted by default, but configurable for remote dashboard access.
