# PacketBuddy API Reference

## Introduction

PacketBuddy provides a local REST API for accessing network usage data, statistics, and managing storage. The API runs on **http://127.0.0.1:7373** by default.

### Base URL

```
http://127.0.0.1:7373/api
```

### Response Format

All endpoints return JSON responses unless otherwise specified. Common response fields include:

- `bytes_sent` - Data uploaded (in bytes)
- `bytes_received` - Data downloaded (in bytes)
- `total_bytes` - Combined upload + download
- `human_readable` - Human-formatted versions of byte values

---

## Endpoints

### GET /api/health

Service health check with system information.

**Response:**

```json
{
  "status": "running",
  "version": "1.0.0",
  "device_id": "abc123def456",
  "os_type": "Windows",
  "hostname": "MY-COMPUTER",
  "device_count": 1,
  "sync_enabled": false,
  "timestamp": "2026-02-21T10:30:00.000000",
  "storage": {
    "db_size_mb": 12.5,
    "max_storage_mb": 400,
    "usage_logs_count": 15000,
    "daily_aggregates_count": 45,
    "monthly_aggregates_count": 3,
    "synced_count": 0,
    "unsynced_count": 15000,
    "storage_usage_percent": 3.1,
    "warning": null
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status ("running") |
| `version` | string | PacketBuddy version |
| `device_id` | string | Unique device identifier |
| `os_type` | string | Operating system |
| `hostname` | string | Device hostname |
| `device_count` | integer | Number of synced devices |
| `sync_enabled` | boolean | Whether cloud sync is enabled |
| `timestamp` | string | Current UTC timestamp (ISO 8601) |
| `storage` | object | Storage statistics |

---

### GET /api/live

Get current upload/download speed in real-time.

**Response:**

```json
{
  "bytes_sent": 524288,
  "bytes_received": 2097152,
  "total_bytes": 2621440,
  "human_readable": {
    "sent": "524.29 KB",
    "received": "2.10 MB",
    "total": "2.62 MB"
  }
}
```

**Note:** Values represent current throughput in bytes per second.

---

### GET /api/today

Get today's total usage with cost breakdown.

**Response:**

```json
{
  "bytes_sent": 5368709120,
  "bytes_received": 21474836480,
  "total_bytes": 26843545600,
  "peak_speed": 125829120,
  "human_readable": {
    "sent": "5.37 GB",
    "received": "21.47 GB",
    "total": "26.84 GB",
    "peak_speed": "125.83 MB/s"
  },
  "cost": {
    "upload": {
      "gb_used": 5.0,
      "cost_inr": 37.50,
      "cost_formatted": "₹37.50"
    },
    "download": {
      "gb_used": 20.0,
      "cost_inr": 150.00,
      "cost_formatted": "₹150.00"
    },
    "total": {
      "gb_used": 25.0,
      "cost_inr": 187.50,
      "cost_formatted": "₹187.50"
    },
    "cost_per_gb": 7.5,
    "currency": "INR"
  },
  "global": {
    "bytes_sent": 6442450944,
    "bytes_received": 23622320128,
    "total_bytes": 30064771072,
    "human_readable": {
      "sent": "6.44 GB",
      "received": "23.62 GB",
      "total": "30.06 GB"
    },
    "cost": {
      "upload": {"gb_used": 6.0, "cost_inr": 45.00, "cost_formatted": "₹45.00"},
      "download": {"gb_used": 22.0, "cost_inr": 165.00, "cost_formatted": "₹165.00"},
      "total": {"gb_used": 28.0, "cost_inr": 210.00, "cost_formatted": "₹210.00"},
      "cost_per_gb": 7.5,
      "currency": "INR"
    }
  }
}
```

**Note:** The `global` field is only present when cloud sync is enabled.

---

### GET /api/cost

Calculate cost for today's usage with customizable rate.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cost_per_gb` | float | 7.50 | Cost per GB in INR |

**Response:**

```json
{
  "usage": {
    "bytes_sent": 5368709120,
    "bytes_received": 21474836480,
    "total_bytes": 26843545600,
    "gb_used": 25.0
  },
  "cost": {
    "upload": {
      "gb_used": 5.0,
      "cost_inr": 37.50,
      "cost_formatted": "₹37.50"
    },
    "download": {
      "gb_used": 20.0,
      "cost_inr": 150.00,
      "cost_formatted": "₹150.00"
    },
    "total": {
      "gb_used": 25.0,
      "cost_inr": 187.50,
      "cost_formatted": "₹187.50"
    },
    "cost_per_gb": 7.5,
    "currency": "INR"
  },
  "info": {
    "cost_per_gb_inr": 7.5,
    "currency": "INR",
    "note": "Based on average Indian mobile data costs (2026)"
  }
}
```

**Example:**

```
GET /api/cost?cost_per_gb=10.0
```

---

### GET /api/month

Get monthly usage breakdown by day.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `month` | string | Current month | Month in YYYY-MM format |

**Response:**

```json
{
  "month": "2026-02",
  "days": [
    {
      "date": "2026-02-01",
      "bytes_sent": 1073741824,
      "bytes_received": 5368709120,
      "total_bytes": 6442450944
    },
    {
      "date": "2026-02-02",
      "bytes_sent": 2147483648,
      "bytes_received": 7516192768,
      "total_bytes": 9663676416
    }
  ],
  "summary": {
    "bytes_sent": 3221225472,
    "bytes_received": 12884901888,
    "total_bytes": 16106127360,
    "human_readable": {
      "sent": "3.22 GB",
      "received": "12.88 GB",
      "total": "16.11 GB"
    }
  }
}
```

**Example:**

```
GET /api/month?month=2025-12
```

---

### GET /api/summary

Get lifetime total usage statistics.

**Response:**

```json
{
  "bytes_sent": 107374182400,
  "bytes_received": 536870912000,
  "total_bytes": 644245094400,
  "human_readable": {
    "sent": "107.37 GB",
    "received": "536.87 GB",
    "total": "644.25 GB"
  },
  "cost": {
    "upload": {
      "gb_used": 100.0,
      "cost_inr": 750.00,
      "cost_formatted": "₹750.00"
    },
    "download": {
      "gb_used": 500.0,
      "cost_inr": 3750.00,
      "cost_formatted": "₹3,750.00"
    },
    "total": {
      "gb_used": 600.0,
      "cost_inr": 4500.00,
      "cost_formatted": "₹4,500.00"
    },
    "cost_per_gb": 7.5,
    "currency": "INR"
  },
  "global": {
    "bytes_sent": 118111600640,
    "bytes_received": 591660339200,
    "total_bytes": 709771939840,
    "human_readable": {
      "sent": "118.11 GB",
      "received": "591.66 GB",
      "total": "709.77 GB"
    },
    "cost": {
      "upload": {"gb_used": 110.0, "cost_inr": 825.00, "cost_formatted": "₹825.00"},
      "download": {"gb_used": 550.0, "cost_inr": 4125.00, "cost_formatted": "₹4,125.00"},
      "total": {"gb_used": 660.0, "cost_inr": 4950.00, "cost_formatted": "₹4,950.00"},
      "cost_per_gb": 7.5,
      "currency": "INR"
    }
  }
}
```

**Note:** The `global` field is only present when cloud sync is enabled.

---

### GET /api/range

Get usage for an arbitrary date range.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_date` | string | Yes | Start date (YYYY-MM-DD) |
| `to_date` | string | Yes | End date (YYYY-MM-DD) |

**Response:**

```json
{
  "from": "2026-01-15",
  "to": "2026-01-20",
  "days": [
    {
      "date": "2026-01-15",
      "bytes_sent": 1073741824,
      "bytes_received": 5368709120,
      "total_bytes": 6442450944
    },
    {
      "date": "2026-01-16",
      "bytes_sent": 1610612736,
      "bytes_received": 6442450944,
      "total_bytes": 8053063680
    }
  ],
  "summary": {
    "bytes_sent": 2684354560,
    "bytes_received": 11811160064,
    "total_bytes": 14495514624,
    "human_readable": {
      "sent": "2.68 GB",
      "received": "11.81 GB",
      "total": "14.50 GB"
    }
  }
}
```

**Example:**

```
GET /api/range?from_date=2026-01-01&to_date=2026-01-31
```

---

### GET /api/export

Export all usage data in various formats.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | "json" | Export format: `json`, `csv`, `html`, `llm` |

#### JSON Format (default)

Returns comprehensive JSON with metadata, summaries, monthly data, and daily data.

**Response Structure:**

```json
{
  "metadata": {
    "exported_at": "2026-02-21T10:30:00.000000",
    "device": {
      "hostname": "MY-COMPUTER",
      "os_type": "Windows",
      "device_id": "abc123def456"
    },
    "tracking_period": {
      "first_date": "2025-01-01",
      "last_date": "2026-02-21",
      "total_days": 417
    }
  },
  "summary": {
    "totals": {
      "bytes_sent": 107374182400,
      "bytes_received": 536870912000,
      "total_bytes": 644245094400,
      "human_readable": {
        "sent": "107.37 GB",
        "received": "536.87 GB",
        "total": "644.25 GB"
      }
    },
    "averages": {
      "daily_bytes": 1545742400,
      "daily_human": "1.55 GB"
    },
    "peak_speed": {
      "bytes_per_second": 125829120,
      "human_readable": "125.83 MB/s"
    },
    "peak_day": {
      "date": "2026-01-15",
      "bytes": 16106127360,
      "human": "16.11 GB"
    }
  },
  "monthly_data": [...],
  "daily_data": [...]
}
```

#### CSV Format

Returns CSV file with download attachment.

**CSV Headers:**

```
date,bytes_sent,bytes_received,total_bytes,peak_speed
```

#### HTML Format

Returns a styled HTML year wrap-up report with visualizations.

#### LLM Format

Returns TOON (Token Optimized Object Notation) format for efficient LLM analysis.

**Example:**

```
GET /api/export?format=csv
GET /api/export?format=html
GET /api/export?format=llm
```

---

### GET /api/export/llm

Export data in TOON format specifically optimized for LLM analysis.

**Response:**

```
# PacketBuddy Network Usage Export - TOON Format

[meta]
format = "TOON (Token Optimized Object Notation)"
generated = "2026-02-21T10:30:00.000000"
device = "MY-COMPUTER"
os = "Windows"
device_id = "abc123def456"
version = "1.0.0"

[tracking]
first_date = "2025-01-01"
last_date = "2026-02-21"
total_days = 417

[totals]
bytes_sent = 107374182400
bytes_received = 536870912000
total_bytes = 644245094400
human = {sent="107.37 GB", received="536.87 GB", total="644.25 GB"}

[year_2026]
bytes_sent = 53687091200
bytes_received = 268435456000
total_bytes = 322122547200
days = 52
human = {sent="53.69 GB", received="268.44 GB", total="322.12 GB"}

[records]
peak_speed_bps = 125829120
peak_speed_human = "125.83 MB/s"
peak_day_date = "2026-01-15"
peak_day_bytes = 16106127360
peak_day_human = "16.11 GB"

[averages]
daily_bytes = 1545742400
daily_human = "1.55 GB"

[ratios]
upload_download = 0.20
upload_percent = 16.7
download_percent = 83.3

[comparisons]
dvd_equivalent = 137
cd_equivalent = 921
hd_movie_equivalent = 128

[monthly_data]
month_0 = {name="2026-02", sent=10737418240, received=53687091200, total=64424509440, peak=125829120, days=21, human="64.42 GB"}
...

[recent_30_days]
day_0 = {date="2026-02-21", sent=5368709120, received=21474836480, total=26843545600, peak=125829120}
...

[llm_prompts]
year_wrapup = "Create a fun, Spotify-style 2026 wrap-up based on this network usage data..."
professional = "Generate a professional network usage summary..."
personal = "Analyze my internet usage patterns..."
trends = "Identify trends in my internet usage over time..."
```

**Note:** TOON format uses approximately 60% fewer tokens than equivalent markdown while preserving all data.

---

### GET /api/storage

Get comprehensive storage information for both local database and NeonDB (if sync enabled).

**Response:**

```json
{
  "local": {
    "db_size_mb": 12.5,
    "max_storage_mb": 400,
    "usage_percent": 3.1,
    "usage_logs_count": 15000,
    "daily_aggregates_count": 45,
    "monthly_aggregates_count": 3,
    "synced_count": 0,
    "unsynced_count": 15000,
    "oldest_log": "2025-01-01T00:00:00",
    "newest_log": "2026-02-21T10:30:00"
  },
  "neon": {
    "total_mb": 45.2,
    "max_storage_mb": 450,
    "usage_percent": 10.0,
    "free_tier_limit_mb": 512,
    "warning_threshold_percent": 80,
    "tables": {
      "usage_logs": 30.5,
      "daily_aggregates": 10.2,
      "monthly_aggregates": 4.5
    },
    "device_count": 2,
    "log_count": 30000,
    "oldest_log": "2025-01-01T00:00:00",
    "newest_log": "2026-02-21T10:30:00",
    "logs_per_device": [
      {"device_id": "abc123", "count": 15000},
      {"device_id": "def456", "count": 15000}
    ]
  },
  "retention": {
    "local_log_days": 30,
    "local_aggregate_months": 12,
    "neon_log_days": 7,
    "neon_aggregate_months": 3
  }
}
```

**Note:** The `neon` field is `null` when cloud sync is disabled. Warnings appear when storage exceeds thresholds.

---

### POST /api/storage/cleanup

Manually trigger storage cleanup for both local and NeonDB.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `aggressive` | boolean | false | Run aggressive cleanup for storage crisis |
| `vacuum` | boolean | true | Run VACUUM after cleanup to reclaim space |

**Response:**

```json
{
  "local": {
    "logs_deleted": 5000,
    "aggregates_deleted": {
      "daily": 30,
      "monthly": 2
    }
  },
  "neon": {
    "logs_deleted": 3000,
    "aggregates_deleted": {
      "daily": 20,
      "monthly": 1
    },
    "vacuum_run": true,
    "storage_after_percent": 5.2
  },
  "vacuum_run": true
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Error message description"
}
```

### Common Errors

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters or date format |
| 500 | Internal Server Error - Unexpected server error |

### Example Error Response

**Request:**

```
GET /api/range?from_date=invalid&to_date=2026-01-31
```

**Response (400):**

```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

---

## Using the API with curl

### Basic Examples

**Health Check:**

```bash
curl http://127.0.0.1:7373/api/health
```

**Live Speed:**

```bash
curl http://127.0.0.1:7373/api/live
```

**Today's Usage:**

```bash
curl http://127.0.0.1:7373/api/today
```

**Calculate Cost with Custom Rate:**

```bash
curl "http://127.0.0.1:7373/api/cost?cost_per_gb=10.0"
```

**Monthly Report:**

```bash
curl "http://127.0.0.1:7373/api/month?month=2026-01"
```

**Date Range Query:**

```bash
curl "http://127.0.0.1:7373/api/range?from_date=2026-01-01&to_date=2026-01-31"
```

**Export as CSV:**

```bash
curl "http://127.0.0.1:7373/api/export?format=csv" -o packetbuddy_export.csv
```

**Export HTML Report:**

```bash
curl "http://127.0.0.1:7373/api/export?format=html" -o wrap_up.html
```

**Trigger Cleanup:**

```bash
curl -X POST "http://127.0.0.1:7373/api/storage/cleanup?vacuum=true"
```

**Aggressive Cleanup:**

```bash
curl -X POST "http://127.0.0.1:7373/api/storage/cleanup?aggressive=true&vacuum=true"
```

---

## Integration Examples

### Python

```python
import requests

BASE_URL = "http://127.0.0.1:7373/api"

def get_today_usage():
    response = requests.get(f"{BASE_URL}/today")
    return response.json()

def get_monthly_report(month):
    response = requests.get(f"{BASE_URL}/month", params={"month": month})
    return response.json()

def get_range_usage(from_date, to_date):
    response = requests.get(f"{BASE_URL}/range", params={
        "from_date": from_date,
        "to_date": to_date
    })
    return response.json()

def export_data(format="json"):
    response = requests.get(f"{BASE_URL}/export", params={"format": format})
    return response.content if format != "json" else response.json()

# Usage
today = get_today_usage()
print(f"Today's usage: {today['human_readable']['total']}")

january = get_monthly_report("2026-01")
print(f"January total: {january['summary']['human_readable']['total']}")
```

### JavaScript / Node.js

```javascript
const BASE_URL = 'http://127.0.0.1:7373/api';

async function getTodayUsage() {
  const response = await fetch(`${BASE_URL}/today`);
  return response.json();
}

async function getMonthlyReport(month) {
  const response = await fetch(`${BASE_URL}/month?month=${month}`);
  return response.json();
}

async function getRangeUsage(fromDate, toDate) {
  const response = await fetch(
    `${BASE_URL}/range?from_date=${fromDate}&to_date=${toDate}`
  );
  return response.json();
}

async function triggerCleanup(aggressive = false) {
  const response = await fetch(
    `${BASE_URL}/storage/cleanup?aggressive=${aggressive}&vacuum=true`,
    { method: 'POST' }
  );
  return response.json();
}

// Usage
getTodayUsage().then(data => {
  console.log(`Today's usage: ${data.human_readable.total}`);
});
```

### Shell Scripting

```bash
#!/bin/bash

API_BASE="http://127.0.0.1:7373/api"

get_today_total() {
    curl -s "$API_BASE/today" | jq -r '.human_readable.total'
}

get_monthly_total() {
    local month=$1
    curl -s "$API_BASE/month?month=$month" | jq -r '.summary.human_readable.total'
}

check_health() {
    curl -s "$API_BASE/health" | jq -r '.status'
}

export_csv() {
    curl -s "$API_BASE/export?format=csv" -o packetbuddy_$(date +%Y%m%d).csv
}

# Usage
echo "Service status: $(check_health)"
echo "Today's usage: $(get_today_total)"
echo "January 2026: $(get_monthly_total 2026-01)"
```

### PowerShell

```powershell
$ApiBase = "http://127.0.0.1:7373/api"

function Get-TodayUsage {
    $response = Invoke-RestMethod -Uri "$ApiBase/today"
    return $response
}

function Get-MonthlyReport {
    param([string]$Month)
    $response = Invoke-RestMethod -Uri "$ApiBase/month?month=$Month"
    return $response
}

function Export-Data {
    param([string]$Format = "json")
    $response = Invoke-RestMethod -Uri "$ApiBase/export?format=$Format"
    return $response
}

# Usage
$today = Get-TodayUsage
Write-Host "Today's usage: $($today.human_readable.total)"
```

---

## Data Types Reference

### Byte Values

All byte values are raw integers representing bytes. Use the `human_readable` fields for display purposes.

| Unit | Multiplier |
|------|------------|
| KB | 1,000 bytes |
| MB | 1,000,000 bytes |
| GB | 1,000,000,000 bytes |
| TB | 1,000,000,000,000 bytes |

### Date Formats

| Format | Example | Usage |
|--------|---------|-------|
| ISO 8601 | `2026-02-21T10:30:00.000000` | Timestamps |
| Date | `2026-02-21` | Date parameters |
| Month | `2026-02` | Month parameters |

### Cost Calculation

Default cost calculation uses ₹7.50 per GB, based on average Indian mobile data costs (2026).

Available cost tiers:

| Tier | Cost per GB (INR) |
|------|-------------------|
| budget | ₹7.00 |
| standard | ₹7.50 |
| premium | ₹10.00 |
| broadband | ₹5.00 |

---

## Rate Limiting

The local API has no rate limiting. However, frequent polling of `/api/live` (more than once per second) is not recommended as it provides instantaneous speed measurements.
