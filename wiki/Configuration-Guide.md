# PacketBuddy Configuration Guide

This guide covers all configuration options available in PacketBuddy. Configuration is managed via a TOML file that allows you to customize monitoring intervals, database connections, storage policies, and more.

## Configuration File Location

PacketBuddy looks for the configuration file in the following locations (in order of precedence):

1. `--config <path>` command-line argument
2. `PACKETBUDDY_CONFIG` environment variable
3. `./config.toml` (current working directory)
4. `~/.packetbuddy/config.toml` (user home directory)

To get started, copy the example configuration:

```bash
cp config.example.toml config.toml
```

---

## Configuration Sections

### [monitoring]

Controls the network monitoring behavior and performance tuning.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `poll_interval` | integer | `1` | Network polling interval in seconds. Lower values provide more granular data but increase CPU usage. |
| `batch_write_interval` | integer | `5` | SQLite batch write interval in seconds. Batching writes improves performance by reducing disk I/O. |
| `max_delta_bytes` | integer | `1000000000` | Maximum delta threshold (1GB/s) for anomaly detection. Triggers alerts when throughput exceeds this value. |

**Example:**

```toml
[monitoring]
poll_interval = 1              # High-frequency monitoring
batch_write_interval = 5       # Balance between responsiveness and performance
max_delta_bytes = 1000000000   # 1GB/s anomaly threshold
```

**Recommendations:**

- For **high-traffic networks**, keep `poll_interval` at `1` for accurate monitoring
- For **low-power systems**, increase `poll_interval` to `5` or higher to reduce CPU load
- Adjust `max_delta_bytes` based on your expected network capacity

---

### [sync]

Configures synchronization with NeonDB cloud storage.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable or disable NeonDB synchronization. Set to `false` for local-only mode. |
| `interval` | integer | `30` | Sync interval in seconds. Determines how often data is pushed to NeonDB. |
| `retry_delay` | integer | `5` | Delay in seconds before retrying a failed sync operation. |
| `max_retries` | integer | `3` | Maximum number of retry attempts before giving up on a sync operation. |

**Example:**

```toml
[sync]
enabled = true        # Enable cloud sync
interval = 30         # Sync every 30 seconds
retry_delay = 5       # Wait 5 seconds before retry
max_retries = 3       # Try up to 3 times
```

**Recommendations:**

- For **real-time dashboards**, use `interval = 10-30`
- For **infrequent sync**, use `interval = 300` (5 minutes) to reduce API calls
- Increase `max_retries` if you experience unreliable network connectivity

---

### [api]

Configures the local API server used by the dashboard and external integrations.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `"127.0.0.1"` | API server bind address. Use `0.0.0.0` to accept connections from all interfaces. |
| `port` | integer | `7373` | API server port number. |
| `cors_enabled` | boolean | `true` | Enable CORS headers for cross-origin requests from the web dashboard. |

**Example:**

```toml
[api]
host = "127.0.0.1"    # Localhost only (secure)
port = 7373           # Default port
cors_enabled = true   # Allow dashboard access
```

**Security Note:**

- Binding to `0.0.0.0` exposes the API to your local network
- Only disable CORS if you're hosting the dashboard on the same origin
- Consider using a reverse proxy with authentication for production deployments

---

### [database]

Configures the NeonDB cloud database connection.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `neon_url` | string | `""` | NeonDB PostgreSQL connection URL. Can also be set via `NEON_DB_URL` environment variable. |
| `pool_size` | integer | `5` | Connection pool size for NeonDB. Adjust based on expected concurrency. |

**Example:**

```toml
[database]
neon_url = "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/packetbuddy?sslmode=require"
pool_size = 5
```

**Recommendations:**

- Use the environment variable `NEON_DB_URL` instead of hardcoding credentials
- For NeonDB free tier, `pool_size = 5` is optimal
- Increase pool size for high-traffic deployments

---

### [auto_update]

Controls automatic update behavior for keeping PacketBuddy current.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable automatic update checking. Recommended for security and features. |
| `check_on_startup` | boolean | `true` | Check for updates when the service starts. |
| `check_interval_hours` | integer | `6` | How often to check for updates (in hours). |
| `auto_apply` | boolean | `true` | Automatically download and apply updates when found. |
| `auto_restart` | boolean | `true` | Automatically restart the service after an update is applied. |

**Example:**

```toml
[auto_update]
enabled = true              # Keep PacketBuddy updated
check_on_startup = true     # Check on launch
check_interval_hours = 6    # Check every 6 hours
auto_apply = true           # Apply updates automatically
auto_restart = true         # Restart after update
```

**Recommendations:**

- For **production servers**, enable all options to stay current with security patches
- For **development environments**, set `auto_apply = false` to control when updates are applied
- For **critical systems**, set `auto_restart = false` and restart manually during maintenance windows

---

### [storage]

Controls local data retention and storage management.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_retention_days` | integer | `30` | How long to keep local log data (in days). |
| `aggregate_retention_months` | integer | `12` | How long to keep aggregated statistics (in months). |
| `cleanup_interval_hours` | integer | `24` | How often to run the cleanup process (in hours). |
| `vacuum_after_cleanup` | boolean | `true` | Reclaim disk space after cleanup by running SQLite VACUUM. |
| `max_storage_mb` | integer | `400` | Warning threshold for local database size (in MB). |

**Example:**

```toml
[storage]
log_retention_days = 30           # Keep logs for 30 days
aggregate_retention_months = 12   # Keep aggregates for 1 year
cleanup_interval_hours = 24       # Daily cleanup
vacuum_after_cleanup = true       # Reclaim disk space
max_storage_mb = 400              # Warn at 400MB
```

**Recommendations:**

- For **long-term analysis**, increase `aggregate_retention_months`
- For **limited disk space**, reduce `log_retention_days` and enable `vacuum_after_cleanup`
- Set `max_storage_mb` slightly below your actual disk capacity

---

### [storage.neon]

NeonDB-specific settings optimized for the free tier (0.5 GB storage limit).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_retention_days` | integer | `7` | Aggressive log retention to save cloud storage (in days). |
| `aggregate_retention_months` | integer | `3` | Keep only 3 months of aggregated data in NeonDB. |
| `max_storage_mb` | integer | `450` | Warning threshold for NeonDB storage (under 512MB limit). |
| `warning_threshold_percent` | integer | `80` | Warn when storage usage reaches this percentage. |
| `cleanup_on_sync` | boolean | `true` | Run cleanup after each sync operation to manage storage. |

**Example:**

```toml
[storage.neon]
log_retention_days = 7            # Keep only 7 days of logs
aggregate_retention_months = 3    # Keep 3 months of aggregates
max_storage_mb = 450              # Stay under 512MB limit
warning_threshold_percent = 80    # Warn at 80% capacity
cleanup_on_sync = true            # Cleanup after each sync
```

**Free Tier Optimization:**

The NeonDB free tier has a 0.5 GB storage limit. These settings are optimized to stay within that limit while preserving useful data:

- Logs expire after 7 days (detailed data takes the most space)
- Aggregates are kept for 3 months (summarized data is much smaller)
- Cleanup runs automatically after each sync
- Warnings trigger at 80% to give you time to act

---

## Environment Variables

PacketBuddy supports the following environment variables:

| Variable | Description |
|----------|-------------|
| `NEON_DB_URL` | NeonDB PostgreSQL connection URL. Takes precedence over `database.neon_url` in config file. |
| `PACKETBUDDY_CONFIG` | Path to the configuration file. |

**Setting NEON_DB_URL:**

```bash
# Linux/macOS
export NEON_DB_URL="postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/packetbuddy?sslmode=require"

# Windows (Command Prompt)
set NEON_DB_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/packetbuddy?sslmode=require

# Windows (PowerShell)
$env:NEON_DB_URL="postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/packetbuddy?sslmode=require"
```

**Security Best Practice:**

Store sensitive credentials like database URLs in environment variables rather than the config file. This prevents accidental exposure if the config file is shared or committed to version control.

---

## Configuration Best Practices

### 1. Security

- Never commit `config.toml` with credentials to version control
- Use `NEON_DB_URL` environment variable for database credentials
- Bind API to `127.0.0.1` unless you need external access
- Add `config.toml` to your `.gitignore` file

### 2. Performance

- Match `poll_interval` to your monitoring needs (lower = more data, more CPU)
- Keep `batch_write_interval` between 5-10 seconds for optimal SQLite performance
- Increase `pool_size` only if you have concurrent dashboard users

### 3. Storage Management

- Enable `vacuum_after_cleanup` for long-running deployments
- Monitor `max_storage_mb` warnings to prevent disk issues
- Use shorter retention periods on NeonDB free tier

### 4. Reliability

- Keep `auto_update` enabled for security patches
- Set appropriate `max_retries` for sync operations
- Configure alerts based on `warning_threshold_percent`

---

## Example Configurations

### Development Setup

Minimal configuration for local development and testing:

```toml
[monitoring]
poll_interval = 5
batch_write_interval = 10
max_delta_bytes = 1000000000

[sync]
enabled = false          # No cloud sync in dev

[api]
host = "127.0.0.1"
port = 7373
cors_enabled = true

[database]
pool_size = 2

[auto_update]
enabled = false          # Manual updates in dev

[storage]
log_retention_days = 7
aggregate_retention_months = 1
cleanup_interval_hours = 24
vacuum_after_cleanup = true
max_storage_mb = 100
```

### Production Server

Full-featured configuration for production deployments:

```toml
[monitoring]
poll_interval = 1
batch_write_interval = 5
max_delta_bytes = 1000000000

[sync]
enabled = true
interval = 30
retry_delay = 5
max_retries = 5

[api]
host = "127.0.0.1"
port = 7373
cors_enabled = true

[database]
pool_size = 5

[auto_update]
enabled = true
check_on_startup = true
check_interval_hours = 6
auto_apply = true
auto_restart = true

[storage]
log_retention_days = 30
aggregate_retention_months = 12
cleanup_interval_hours = 24
vacuum_after_cleanup = true
max_storage_mb = 400

[storage.neon]
log_retention_days = 7
aggregate_retention_months = 3
max_storage_mb = 450
warning_threshold_percent = 80
cleanup_on_sync = true
```

### Low-Resource System

Optimized for minimal resource usage:

```toml
[monitoring]
poll_interval = 10       # Less frequent polling
batch_write_interval = 30
max_delta_bytes = 1000000000

[sync]
enabled = true
interval = 300           # Sync every 5 minutes
retry_delay = 10
max_retries = 3

[api]
host = "127.0.0.1"
port = 7373
cors_enabled = true

[database]
pool_size = 2            # Smaller connection pool

[auto_update]
enabled = true
check_on_startup = false
check_interval_hours = 24
auto_apply = true
auto_restart = true

[storage]
log_retention_days = 7
aggregate_retention_months = 3
cleanup_interval_hours = 48
vacuum_after_cleanup = false  # Skip vacuum to save I/O
max_storage_mb = 200
```

### High-Traffic Network

Optimized for networks with significant throughput:

```toml
[monitoring]
poll_interval = 1
batch_write_interval = 3
max_delta_bytes = 10000000000  # 10GB/s threshold

[sync]
enabled = true
interval = 15           # More frequent sync
retry_delay = 3
max_retries = 5

[api]
host = "127.0.0.1"
port = 7373
cors_enabled = true

[database]
pool_size = 10          # Larger pool for concurrency

[auto_update]
enabled = true
check_on_startup = true
check_interval_hours = 4
auto_apply = true
auto_restart = true

[storage]
log_retention_days = 14
aggregate_retention_months = 6
cleanup_interval_hours = 12
vacuum_after_cleanup = true
max_storage_mb = 800

[storage.neon]
log_retention_days = 3
aggregate_retention_months = 2
max_storage_mb = 450
warning_threshold_percent = 75
cleanup_on_sync = true
```

---

## Troubleshooting

### Configuration Not Loading

1. Verify the file path is correct
2. Check TOML syntax with a validator
3. Ensure the file is readable by the PacketBuddy process

### Database Connection Issues

1. Verify `NEON_DB_URL` is set correctly
2. Check that the URL includes `sslmode=require`
3. Ensure your IP is allowed in NeonDB dashboard

### Storage Warnings

1. Check current database size with the API status endpoint
2. Reduce retention periods if approaching limits
3. Run manual cleanup via the API

### Sync Failures

1. Check network connectivity
2. Verify NeonDB is not paused (free tier auto-pauses)
3. Review sync logs for specific error messages
