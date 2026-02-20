# PacketBuddy Architecture

This document provides a comprehensive overview of PacketBuddy's system architecture, component design, data flow, and technology stack.

## System Overview

PacketBuddy implements a **three-layer architecture** designed for minimal resource footprint while maintaining robust data collection and multi-device synchronization capabilities.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Web Dashboard  │  │   CLI Interface  │  │   REST API       │  │
│  │   (Chart.js)     │  │   (Click)        │  │   (FastAPI)      │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Local Storage   │  │    NeonSync      │  │  Storage Manager │  │
│  │  (SQLite)        │  │  (NeonDB Sync)   │  │  (Cleanup/Stats) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MONITOR LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  NetworkMonitor  │  │  Battery-Aware   │  │  Catch-Up Logic  │  │
│  │  (psutil)        │  │  Polling         │  │  (Restart Recovery)│  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Privacy-First** | Local-first storage, no PII collection, no browsing history tracked |
| **Lightweight** | <40MB RAM, <0.3% CPU, minimal disk I/O |
| **Zero Configuration** | Works out-of-the-box, optional cloud sync via environment variable |
| **Resilient** | Auto-restart on crash, battery-aware polling, counter reset handling |

---

## Component Architecture

### 1. NetworkMonitor (`src/core/monitor.py`)

The heartbeat of PacketBuddy - responsible for capturing network I/O data.

**Key Responsibilities:**
- Network interface detection via gateway routing tables
- Real-time bandwidth monitoring using `psutil.net_io_counters()`
- Delta calculation with anomaly filtering (>1GB/s spikes filtered)
- Battery-aware polling intervals (1s on AC, 2s on battery)
- Catch-up logic for usage recorded while the application was closed

**Core Logic:**

```python
# Primary interface detection (platform-specific)
Windows: Get-NetRoute -DestinationPrefix 0.0.0.0/0
macOS:   route -n get default
Linux:   ip route show default

# Counter handling
- Filters virtual/internal interfaces (lo, utun, awdl, docker, veth, etc.)
- Detects counter resets (negative deltas) from system sleep/resume
- Tracks absolute counters in system_state for crash recovery
```

**Polling Configuration:**

| Mode | Poll Interval | Batch Write Interval |
|------|---------------|---------------------|
| AC Power | 1 second | 30 seconds |
| Battery | 2 seconds | 180 seconds |

---

### 2. Storage (`src/core/storage.py`)

The memory layer - manages local SQLite database with atomic writes.

**Key Responsibilities:**
- Local data persistence with SQLite
- Daily/monthly aggregate computation
- Peak speed tracking and persistence
- Sync state management
- Database cleanup and VACUUM operations

**Connection Management:**
- Context manager pattern for safe connection handling
- Automatic commit/rollback on success/failure
- Row factory for dict-like row access

**Storage Methods:**

| Method | Purpose |
|--------|---------|
| `insert_usage()` | Insert usage log + update aggregates |
| `get_today_usage()` | Today's sent/received/peak |
| `get_month_usage()` | Daily breakdown for month |
| `get_lifetime_usage()` | Total all-time usage |
| `cleanup_synced_logs()` | Delete old synced logs |
| `vacuum_database()` | Reclaim SQLite space |

---

### 3. NeonSync (`src/core/sync.py`)

The bridge layer - handles cloud synchronization to NeonDB (serverless PostgreSQL).

**Key Responsibilities:**
- Async connection pooling to NeonDB
- Batch synchronization (O(1) updates via aggregates)
- Multi-device data aggregation
- Storage optimization with VACUUM ANALYZE
- Crisis mode cleanup when storage >80%

**Sync Strategy:**

```
Local SQLite ──────┐
                   │  60s interval
                   ▼
            ┌──────────────┐
            │   NeonSync   │
            │  (asyncpg)   │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │   NeonDB     │
            │ (PostgreSQL) │
            └──────────────┘
```

**Storage Retention Policies:**

| Layer | Logs Retention | Aggregates Retention |
|-------|----------------|---------------------|
| Local SQLite | 30 days (synced) | 12 months |
| NeonDB | 7 days | 3 months |
| Crisis Mode | 3 days | 1-2 months |

**Crisis Mode:** Triggered when NeonDB storage exceeds 80% of 512MB free tier limit. Reduces retention aggressively and runs VACUUM ANALYZE.

---

### 4. FastAPI Server (`src/api/server.py`, `src/api/routes.py`)

The interface layer - provides REST API and serves the dashboard.

**Key Responsibilities:**
- HTTP API on port 7373 (configurable)
- Static file serving for dashboard
- CORS middleware for cross-origin requests
- Background task orchestration

**Server Lifecycle:**

```
Startup:
  1. Initialize FastAPI app with CORS
  2. Mount dashboard static files
  3. Start NetworkMonitor background task
  4. Start NeonSync background task (if enabled)
  5. Start periodic cleanup task
  6. Start auto-update checker

Shutdown:
  1. Stop NetworkMonitor (flush pending writes)
  2. Stop NeonSync (final sync attempt)
  3. Cancel all background tasks
```

**Key Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Service health + storage stats |
| `GET /api/live` | Current upload/download speed |
| `GET /api/today` | Today's usage with cost breakdown |
| `GET /api/month` | Monthly breakdown by day |
| `GET /api/summary` | Lifetime usage statistics |
| `GET /api/export` | Export data (JSON/CSV/HTML/TOON) |
| `GET /api/storage` | Storage usage for local + NeonDB |
| `POST /api/storage/cleanup` | Trigger manual cleanup |

---

### 5. CLI Interface (`src/cli/main.py`)

Command-line interface using Click framework.

**Available Commands:**

| Command | Description |
|---------|-------------|
| `pb live` | Show current speeds |
| `pb today` | Today's usage summary |
| `pb month [YYYY-MM]` | Monthly breakdown |
| `pb summary` | Lifetime usage |
| `pb export --format json` | Export all data |
| `pb serve` | Start API server |
| `pb update` | Check/apply updates |
| `pb storage stats` | Database statistics |
| `pb storage cleanup` | Clean old data |
| `pb storage neon` | NeonDB storage info |
| `pb service start/stop/restart` | Manage background service |

---

## Data Flow Diagrams

### Real-Time Monitoring Flow

```
┌─────────────────┐
│  Network I/O    │
│  (OS Kernel)    │
└────────┬────────┘
         │ psutil.net_io_counters()
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Primary         │────▶│ Filter Virtual  │
│ Interface Detect│     │ Interfaces      │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Calculate Delta │
                        │ (current - last)│
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │ Anomaly   │ │ Counter   │ │ Speed     │
             │ Filter    │ │ Reset     │ │ Calc      │
             │ (>1GB/s)  │ │ Detect    │ │ (B/s)     │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                        ┌─────────────────┐
                        │ Pending Writes  │
                        │ Buffer          │
                        └────────┬────────┘
                                 │ 30s batch
                                 ▼
                        ┌─────────────────┐
                        │ SQLite Storage  │
                        │ + Aggregates    │
                        └─────────────────┘
```

### Sync Flow

```
┌─────────────────┐
│  SQLite         │
│  usage_logs     │
│  (synced=0)     │
└────────┬────────┘
         │ get_unsynced_logs(limit=1000)
         ▼
┌─────────────────┐
│  Batch Aggregate│
│  - Daily stats  │
│  - Monthly stats│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  NeonDB         │
│  INSERT/UPSERT  │
│  (Transaction)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Mark Synced    │
│  (SQLite)       │
└─────────────────┘
```

### Export Flow

```
┌─────────────────────────────────────────────────────────┐
│                    /api/export?format=X                  │
└────────────────────────┬────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
┌────────┐         ┌────────┐         ┌────────────┐
│  JSON  │         │  CSV   │         │ HTML/TOON  │
│ Full   │         │ Daily  │         │ Year Wrap  │
│ Export │         │ Aggs   │         │ Report     │
└────────┘         └────────┘         └────────────┘
```

---

## Technology Stack

### Core Dependencies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.11+ | Cross-platform, async support |
| **Network Monitoring** | psutil | System network I/O counters |
| **Local Storage** | SQLite | Zero-config, serverless, atomic writes |
| **Cloud Sync** | asyncpg + NeonDB | Serverless PostgreSQL, connection pooling |
| **REST API** | FastAPI + Uvicorn | High-performance async, auto docs |
| **CLI** | Click + tabulate | Rich command-line interface |
| **Dashboard** | Chart.js | Client-side chart rendering |
| **Configuration** | TOML | Human-readable config files |

### Technology Rationale

| Choice | Reason |
|--------|--------|
| **Python 3.11+** | Cross-platform, rich library ecosystem, native async |
| **SQLite** | Zero-config, serverless, atomic writes, perfect for local-first |
| **NeonDB** | Serverless PostgreSQL with generous free tier (512MB), auto-sleep |
| **FastAPI** | Native async, OpenAPI docs, <50ms endpoint latency |
| **Chart.js** | Client-side rendering, no build step, CDN-delivered |

---

## Background Services and Tasks

### Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                    (Main Process)                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ NetworkMonitor   │  │ NeonSync         │             │
│  │ (async task)     │  │ (async task)     │             │
│  │                  │  │                  │             │
│  │ - Monitor loop   │  │ - Sync loop      │             │
│  │ - Batch write    │  │ - 60s interval   │             │
│  │ - Battery check  │  │                  │             │
│  └──────────────────┘  └──────────────────┘             │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ Periodic Cleanup │  │ Auto-Update      │             │
│  │ (24h interval)   │  │ Checker (6h)     │             │
│  │                  │  │                  │             │
│  │ - Local cleanup  │  │ - Git fetch      │             │
│  │ - NeonDB cleanup │  │ - Auto-apply     │             │
│  │ - VACUUM         │  │ - Service restart│             │
│  └──────────────────┘  └──────────────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Task Intervals

| Task | Interval | Purpose |
|------|----------|---------|
| Network Polling | 1-2s | Capture I/O deltas |
| Batch Write | 30-180s | Reduce disk I/O |
| NeonDB Sync | 60s | Cloud replication |
| Battery Check | 30s | Adjust polling rate |
| Periodic Cleanup | 24h | Remove old data |
| Auto-Update Check | 6h | Check for new versions |
| Storage State Update | ~10 samples | Persist absolute counters |

### Crash Recovery

**Watchdog Pattern (Windows):**
- Task Scheduler with hourly repetition trigger
- Service auto-restarts if process terminates unexpectedly

**Catch-Up Logic:**
1. Track `boot_time` from `psutil.boot_time()`
2. Store absolute counters (`last_abs_sent`, `last_abs_received`)
3. On restart, compare current counters vs saved
4. Record gap as usage entry (if >1KB)

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     devices     │       │   usage_logs    │
├─────────────────┤       ├─────────────────┤
│ device_id (PK)  │───┐   │ id (PK)         │
│ os_type         │   │   │ device_id (FK)  │◄──┐
│ hostname        │   │   │ timestamp       │   │
│ created_at      │   │   │ bytes_sent      │   │
└─────────────────┘   │   │ bytes_received  │   │
                      │   │ synced          │   │
                      │   └─────────────────┘   │
                      │                         │
                      │   ┌─────────────────┐   │
                      │   │daily_aggregates │   │
                      │   ├─────────────────┤   │
                      ├───│ device_id (FK)  │◄──┘
                      │   │ date (PK)       │
                      │   │ bytes_sent      │
                      │   │ bytes_received  │
                      │   │ peak_speed      │
                      │   └─────────────────┘
                      │
                      │   ┌─────────────────┐
                      │   │monthly_aggregates│
                      │   ├─────────────────┤
                      ├───│ device_id (FK)  │
                      │   │ month (PK)      │
                      │   │ bytes_sent      │
                      │   │ bytes_received  │
                      │   └─────────────────┘
                      │
┌─────────────────┐   │
│  system_state   │   │
├─────────────────┤   │
│ key (PK)        │   │
│ value_text      │   │
│ value_int       │   │
│ updated_at      │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │
│  sync_cursor    │   │
├─────────────────┤   │
│ key (PK)        │   │
│ value           │   │
└─────────────────┘   │
                      │
         All FKs ─────┘
```

### Table Definitions

#### `devices`

| Column | Type | Description |
|--------|------|-------------|
| `device_id` | TEXT (PK) | Unique device identifier (UUID-based) |
| `os_type` | TEXT | Operating system (Windows/macOS/Linux) |
| `hostname` | TEXT | Device hostname |
| `created_at` | TIMESTAMP | Device registration time |

#### `usage_logs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-increment ID |
| `device_id` | TEXT (FK) | Device identifier |
| `timestamp` | TIMESTAMP | Log entry timestamp |
| `bytes_sent` | INTEGER | Bytes uploaded |
| `bytes_received` | INTEGER | Bytes downloaded |
| `synced` | BOOLEAN | Sync status (0=pending, 1=synced) |

**Indexes:**
- `idx_usage_logs_timestamp` on `(device_id, timestamp)`
- `idx_usage_logs_synced` on `synced WHERE synced = 0`

#### `daily_aggregates`

| Column | Type | Description |
|--------|------|-------------|
| `device_id` | TEXT (FK, PK) | Device identifier |
| `date` | DATE (PK) | Aggregate date |
| `bytes_sent` | INTEGER | Total bytes sent |
| `bytes_received` | INTEGER | Total bytes received |
| `peak_speed` | INTEGER | Peak speed (B/s) for the day |

#### `monthly_aggregates`

| Column | Type | Description |
|--------|------|-------------|
| `device_id` | TEXT (FK, PK) | Device identifier |
| `month` | TEXT (PK) | Month in YYYY-MM format |
| `bytes_sent` | INTEGER | Total bytes sent |
| `bytes_received` | INTEGER | Total bytes received |

#### `sync_cursor`

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT (PK) | Cursor key |
| `value` | INTEGER | Last synced ID/timestamp |

#### `system_state`

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT (PK) | State key |
| `value_text` | TEXT | Text value |
| `value_int` | INTEGER | Integer value |
| `updated_at` | TIMESTAMP | Last update time |

**Common State Keys:**

| Key | Purpose |
|-----|---------|
| `boot_time` | System boot timestamp (for crash recovery) |
| `last_abs_sent` | Last absolute bytes sent counter |
| `last_abs_received` | Last absolute bytes received counter |

---

## Deployment Architecture

### Windows Service

```
┌─────────────────────────────────────────┐
│          Windows Task Scheduler         │
├─────────────────────────────────────────┤
│ Task: PacketBuddy                       │
│ Trigger: At logon + Hourly repetition   │
│ Action: python launcher.py              │
│ Privileges: Highest                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            launcher.py                  │
│  - Activates venv                       │
│  - Runs: python -m src.api.server       │
│  - Redirects output to stderr.log       │
└─────────────────────────────────────────┘
```

### Unix Service (macOS/Linux)

```
┌─────────────────────────────────────────┐
│     macOS: LaunchAgent                  │
│     Linux: systemd --user               │
├─────────────────────────────────────────┤
│ RunAtLoad: true                         │
│ KeepAlive: true                         │
│ StandardOut/Err: log files              │
└─────────────────────────────────────────┘
```

---

## Performance Characteristics

### Resource Targets

| Metric | Target | Typical |
|--------|--------|---------|
| RAM Usage | <40MB | 25-35MB |
| CPU Usage | <0.3% | 0.1-0.2% |
| Disk I/O | Minimal | 30s batch writes |
| API Latency | <50ms | 5-20ms |

### Optimization Strategies

1. **Batch Writes:** Aggregate 30s of data before database write
2. **Connection Pooling:** Reuse database connections
3. **Index Optimization:** Indexed queries for common patterns
4. **Client-Side Rendering:** Dashboard uses Chart.js (no server rendering)
5. **Efficient Polling:** Battery-aware intervals reduce unnecessary work

---

## Security Considerations

| Aspect | Implementation |
|--------|----------------|
| **Local Binding** | API bound to 127.0.0.1 (localhost only) |
| **No PII** | No browsing history, URLs, or personal data stored |
| **Local-First** | All data stored locally; cloud sync is optional |
| **Environment Variables** | Sensitive config via env vars, not files |
| **Privilege Separation** | Service runs with minimum required privileges |

---

## Version History

| Version | Architecture Changes |
|---------|---------------------|
| v1.4.3 | NeonDB storage optimization, VACUUM ANALYZE, crisis mode |
| v1.4.2 | Crash recovery, catch-up logic, primary interface detection |
| v1.4.1 | Peak speed persistence, TOON export format |
| v1.4.0 | Export formats (CSV, JSON, HTML, TOON) |
| v1.3.0 | NeonDB cloud sync integration |
| v1.0.0 | Initial release with local monitoring |
