# PacketBuddy CLI Reference

## Introduction

PacketBuddy provides a command-line interface (CLI) accessed via the `pb` command. This ultra-lightweight network usage tracker monitors your bandwidth in real-time and provides historical usage statistics.

**Installation Requirement:** The `pb` command is available after installing PacketBuddy and adding it to your system PATH.

---

## Main Commands

### `pb live`

Show current real-time upload and download speed.

**Usage:**
```bash
pb live
```

**Output:**
- Upload Speed
- Download Speed
- Total Speed

**Example:**
```
┌────────────────┬──────────────┐
│ Metric         │ Value        │
├────────────────┼──────────────┤
│ Upload Speed   │ 125.3 KB/s   │
│ Download Speed │ 2.4 MB/s     │
│ Total Speed    │ 2.5 MB/s     │
└────────────────┴──────────────┘
```

---

### `pb today`

Display today's network usage statistics.

**Usage:**
```bash
pb today
```

**Output:**
- Uploaded bytes
- Downloaded bytes
- Total usage

**Example:**
```
📊 Today's Usage

┌────────────┬────────────┐
│ Type       │ Amount     │
├────────────┼────────────┤
│ Uploaded   │ 1.2 GB     │
│ Downloaded │ 8.5 GB     │
│ Total      │ 9.7 GB     │
└────────────┴────────────┘
```

---

### `pb month [YYYY-MM]`

Show a daily breakdown of network usage for a specific month.

**Usage:**
```bash
pb month           # Current month
pb month 2024-01   # Specific month
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `month`  | No       | Month in `YYYY-MM` format. Defaults to current month. |

**Output:**
- Daily usage table (date, uploaded, downloaded, total)
- Month summary with totals

**Example:**
```
📅 Usage for 2024-01

┌────────────┬───────────┬─────────────┬───────────┐
│ Date       │ Uploaded  │ Downloaded  │ Total     │
├────────────┼───────────┼─────────────┼───────────┤
│ 2024-01-01 │ 1.2 GB    │ 8.5 GB      │ 9.7 GB    │
│ 2024-01-02 │ 0.8 GB    │ 6.2 GB      │ 7.0 GB    │
│ ...        │ ...       │ ...         │ ...       │
└────────────┴───────────┴─────────────┴───────────┘

📈 Month Summary:
   Total Uploaded: 35.2 GB
   Total Downloaded: 245.8 GB
   Total: 281.0 GB
```

---

### `pb summary`

Display lifetime usage statistics since PacketBuddy started tracking.

**Usage:**
```bash
pb summary
```

**Output:**
- Total uploaded bytes (lifetime)
- Total downloaded bytes (lifetime)
- Grand total

**Example:**
```
🌐 Lifetime Usage Summary

┌──────────────────┬────────────┐
│ Metric           │ Amount     │
├──────────────────┼────────────┤
│ Total Uploaded   │ 156.2 GB   │
│ Total Downloaded │ 1.2 TB     │
│ Grand Total      │ 1.35 TB    │
└──────────────────┴────────────┘
```

---

### `pb export`

Export all usage data to JSON or CSV format.

**Usage:**
```bash
pb export                          # Export as JSON (default)
pb export --format csv             # Export as CSV
pb export --format json --output my_data.json
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | choice | `json` | Export format: `json` or `csv` |
| `--output` | path | `packetbuddy_export.{format}` | Output file path |

**Example:**
```bash
$ pb export --format csv --output usage_2024.csv
✅ Exported 1523 records to usage_2024.csv
```

---

### `pb serve`

Start the API server and web dashboard.

**Usage:**
```bash
pb serve
```

**Description:**
Launches the local web server providing:
- REST API endpoints
- Web-based dashboard for viewing usage statistics

**Note:** The server runs until manually stopped (Ctrl+C).

---

### `pb update`

Check for and apply updates from GitHub.

**Usage:**
```bash
pb update                    # Check and apply update if available
pb update --check-only       # Only check, don't apply
pb update --force            # Force update even if already up to date
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `--check-only` | flag | Only check for updates without applying them |
| `--force` | flag | Force update even if already on latest version |

**Behavior:**
- PacketBuddy automatically updates in the background
- This command is for manual/forced updates
- Prompts for confirmation before applying updates
- Offers to restart the service after update

**Example:**
```bash
$ pb update --check-only

🔍 Checking for updates...
ℹ PacketBuddy automatically updates in the background
   This command is for manual/force updates

✅ You're already on the latest version (a1b2c3d)

💡 Tip: Updates are applied automatically when available
```

---

### `pb stats`

Show database storage statistics.

**Usage:**
```bash
pb stats
```

**Output:**
- Usage logs count
- Daily aggregates count
- Monthly aggregates count
- Synced vs unsynced logs
- Oldest/newest log timestamps
- Database size and storage usage percentage

**Example:**
```
Database Statistics

┌────────────────────┬───────────┐
│ Table              │ Count     │
├────────────────────┼───────────┤
│ Usage Logs         │ 45,230    │
│ Daily Aggregates   │ 365       │
│ Monthly Aggregates │ 12        │
│ Synced Logs        │ 45,200    │
│ Unsynced Logs      │ 30        │
└────────────────────┴───────────┘

Timestamps
   Oldest log: 2023-01-15 08:23:45
   Newest log: 2024-01-15 14:32:10

Storage
   Database size: 12.5 MB
   Storage usage: 25%
```

---

### `pb cleanup`

Clean up old synced log entries to free storage space.

**Usage:**
```bash
pb cleanup                        # Use config defaults
pb cleanup --days 30              # Keep last 30 days
pb cleanup --dry-run              # Preview without changes
pb cleanup --vacuum               # Force VACUUM after cleanup
pb cleanup --no-vacuum            # Skip VACUUM
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days` | int | config value | Days to keep synced logs |
| `--vacuum` | flag | config value | Run VACUUM after cleanup |
| `--no-vacuum` | flag | - | Skip VACUUM after cleanup |
| `--dry-run` | flag | false | Show what would be deleted without deleting |

**Example:**
```bash
$ pb cleanup --days 30 --dry-run

Storage Cleanup
   Retention: 30 days
   Cutoff date: 2023-12-15 14:30
   Mode: dry run (no changes)

   Synced logs that would be deleted: 1,250
   VACUUM would run after cleanup

Dry run complete. No changes made.
```

---

## Storage Commands

The `pb storage` command group provides database storage management functionality.

### `pb storage stats`

Show database storage statistics (same as `pb stats`).

**Usage:**
```bash
pb storage stats
```

---

### `pb storage cleanup`

Clean up old synced log entries with extended options including NeonDB support.

**Usage:**
```bash
pb storage cleanup                        # Local cleanup with defaults
pb storage cleanup --days 30              # Keep last 30 days
pb storage cleanup --dry-run              # Preview without changes
pb storage cleanup --neon                 # Cleanup NeonDB remote storage
pb storage cleanup --neon --aggressive    # Aggressive NeonDB cleanup
```

**Options:**
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--days` | int | config value | Days to keep synced logs |
| `--vacuum` | flag | config value | Run VACUUM after cleanup |
| `--no-vacuum` | flag | - | Skip VACUUM after cleanup |
| `--dry-run` | flag | false | Show what would be deleted without deleting |
| `--neon` | flag | false | Cleanup NeonDB remote storage |
| `--aggressive` | flag | false | Aggressive cleanup for storage crisis (requires `--neon`) |

**Aggressive Cleanup Retention:**
When using `--neon --aggressive`:
- Logs: 3 days
- Daily aggregates: 1 month
- Monthly aggregates: 2 months

**Example (NeonDB Aggressive):**
```bash
$ pb storage cleanup --neon --aggressive

NeonDB Aggressive Cleanup
   This will reduce retention to minimal levels
   Logs: 3 days | Daily aggregates: 1 month | Monthly aggregates: 2 months

   ✓ Deleted 5,420 log entries
   ✓ Deleted 45 daily aggregates
   ✓ Deleted 6 monthly aggregates
   ✓ VACUUM ANALYZE completed

Storage freed: 15.32 MB
   Before: 485.20 MB | After: 469.88 MB
```

---

### `pb storage neon`

Show NeonDB storage statistics and usage (requires NeonDB sync enabled).

**Usage:**
```bash
pb storage neon
```

**Requirements:**
- NeonDB sync must be enabled via `NEON_DB_URL` environment variable

**Output:**
- Total storage used (MB)
- Free tier limit (512 MB)
- Usage percentage
- Table sizes
- Device and log counts
- Retention settings

**Example:**
```bash
$ pb storage neon

NeonDB Storage

┌─────────────────────┬────────────────┐
│ Metric              │ Value          │
├─────────────────────┼────────────────┤
│ Total Used          │ 245.5 MB       │
│ Free Tier Limit     │ 512 MB (0.5 GB)│
│ Usage               │ 48%            │
│ Warning Threshold   │ 80%            │
└─────────────────────┴────────────────┘

Table Sizes
┌─────────────────────┬────────────┐
│ Table               │ Size       │
├─────────────────────┼────────────┤
│ usage_logs          │ 180.2 MB   │
│ daily_aggregates    │ 45.3 MB    │
│ monthly_aggregates  │ 20.0 MB    │
└─────────────────────┴────────────┘

Statistics
   Devices: 3
   Total logs: 125,430

Retention Settings
   Logs: 7 days
   Aggregates: 3 months
```

---

## Service Commands

The `pb service` command group manages the background monitoring service.

### `pb service start`

Start the PacketBuddy background service.

**Usage:**
```bash
pb service start
```

**Description:**
Starts the daemon/service that continuously monitors network traffic in the background.

---

### `pb service stop`

Stop the PacketBuddy background service.

**Usage:**
```bash
pb service stop
```

**Description:**
Stops the background monitoring service. Network traffic will no longer be tracked until restarted.

---

### `pb service restart`

Restart the PacketBuddy background service.

**Usage:**
```bash
pb service restart
```

**Description:**
Stops and starts the background service. Useful after configuration changes or updates.

---

## Additional Commands

### `pb neon-cleanup`

Shortcut command for aggressive NeonDB cleanup when storage is critically high.

**Usage:**
```bash
pb neon-cleanup
```

**Description:**
Equivalent to `pb storage cleanup --neon --aggressive`. Use this when NeonDB storage is critically full (>90%).

**Requirements:**
- NeonDB sync must be enabled via `NEON_DB_URL` environment variable

---

## Global Options

These options apply to all commands:

```bash
pb --help     # Show help for the CLI
pb --version  # Show PacketBuddy version
```

---

## Command Summary

| Command | Description |
|---------|-------------|
| `pb live` | Show current upload/download speed |
| `pb today` | Show today's usage |
| `pb month [YYYY-MM]` | Show monthly usage breakdown |
| `pb summary` | Show lifetime usage summary |
| `pb export` | Export data to JSON/CSV |
| `pb serve` | Start API server and dashboard |
| `pb update` | Check for and apply updates |
| `pb stats` | Show database statistics |
| `pb cleanup` | Clean up old synced logs |
| `pb storage stats` | Show storage statistics |
| `pb storage cleanup` | Advanced cleanup with NeonDB support |
| `pb storage neon` | Show NeonDB storage info |
| `pb service start` | Start background service |
| `pb service stop` | Stop background service |
| `pb service restart` | Restart background service |
| `pb neon-cleanup` | Aggressive NeonDB cleanup |

---

## Getting Help

For command-specific help, use the `--help` flag:

```bash
pb --help
pb storage --help
pb storage cleanup --help
pb service --help
```

---

## Platform Notes

- **Windows:** Output uses ASCII-compatible formatting (grid tables)
- **macOS/Linux:** Output includes emoji and fancy formatting (fancy_grid tables)
- **Service Management:**
  - macOS: Uses launchctl
  - Windows: Uses Task Scheduler
  - Linux: Uses systemd user services
