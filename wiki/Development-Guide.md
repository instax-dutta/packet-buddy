# PacketBuddy Development Guide

This guide provides comprehensive information for developers contributing to PacketBuddy.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Code Style Guidelines](#code-style-guidelines)
- [Key Modules and Their Responsibilities](#key-modules-and-their-responsibilities)
- [Running in Development Mode](#running-in-development-mode)
- [Testing](#testing)
- [Building and Packaging](#building-and-packaging)
- [Debugging Tips](#debugging-tips)
- [Pull Request Process](#pull-request-process)
- [Code of Conduct](#code-of-conduct)

---

## Development Environment Setup

### Prerequisites

- **Python 3.11 or higher** - Required for modern async features and type hints
- **Git** - Version control
- **A NeonDB account** (optional) - For testing cloud sync functionality

### Setup Steps

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/packet-buddy.git
cd packet-buddy

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/packet-buddy.git

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# 6. Run in development mode
python -m src.api.server

# 7. Open dashboard
open http://127.0.0.1:7373/dashboard
```

### AI-Assisted Development

PacketBuddy is **AI-ready**. The hidden `.agent/` directory contains:
- High-level technical blueprints
- Architectural protocols
- Maintenance guides curated for LLMs and AI coding agents

Point your AI tool (Cursor, Copilot, or custom agent) to the `.agent/` folder for instant project context.

---

## Project Structure

```
packet-buddy/
├── src/
│   ├── core/           # Core business logic
│   │   ├── monitor.py      # Network monitoring
│   │   ├── storage.py      # SQLite operations
│   │   ├── sync.py         # NeonDB cloud sync
│   │   └── device.py       # Device identification
│   ├── api/            # REST API (FastAPI)
│   │   ├── server.py       # Main FastAPI application
│   │   └── routes.py       # API endpoints
│   ├── cli/            # Command-line interface
│   │   └── main.py         # CLI commands (Click)
│   ├── utils/          # Utilities
│   │   ├── config.py       # Configuration management
│   │   ├── formatters.py   # Human-readable formatting
│   │   ├── cost_calculator.py  # Data cost calculations
│   │   └── updater.py      # Auto-update functionality
│   └── version.py          # Version information
├── dashboard/          # Web dashboard (static files)
│   ├── index.html          # Main HTML
│   ├── style.css           # Styles
│   └── app.js              # JavaScript frontend
├── service/            # Auto-start configurations
│   ├── macos/              # macOS LaunchAgent
│   └── windows/            # Windows Task Scheduler
├── tests/              # Test suite (to be added)
├── wiki/               # Documentation wiki
├── .agent/             # AI agent context (hidden)
├── requirements.txt    # Production dependencies
└── requirements-dev.txt # Development dependencies
```

---

## Code Style Guidelines

We follow **PEP 8** with a few modifications:

### Formatting Tools

```bash
# Format code with black
black src/

# Sort imports with isort
isort src/

# Check with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

### Code Style Conventions

1. **Line Length**: Maximum 100 characters (black default)
2. **Imports**: Use absolute imports from `src.` prefix
3. **Type Hints**: Required for all function signatures
4. **Docstrings**: Use triple-quoted docstrings for public functions and classes
5. **Comments**: Add comments for complex logic, avoid redundant comments

### Example Code Style

```python
"""Module docstring describing purpose."""

import asyncio
from datetime import datetime
from typing import Optional, Tuple

from .utils.config import config


class ExampleClass:
    """Brief description of the class.
    
    Longer description if needed.
    """
    
    def __init__(self, param: str):
        """Initialize the class.
        
        Args:
            param: Description of parameter.
        """
        self.param = param
    
    async def do_something(self, value: int) -> Tuple[bool, Optional[str]]:
        """Perform an operation.
        
        Args:
            value: The input value.
            
        Returns:
            Tuple of success status and optional message.
        """
        if value < 0:
            return False, "Value must be positive"
        return True, None
```

---

## Key Modules and Their Responsibilities

### `src/core/` - Core Business Logic

The core module contains all business logic for network monitoring and data persistence.

#### `monitor.py` - NetworkMonitor

**Responsibilities:**
- Async network usage monitoring using `psutil`
- Primary network interface detection (macOS, Windows, Linux)
- Real-time upload/download speed calculation
- Battery-aware polling (adjusts intervals on battery power)
- Batch writing for database efficiency
- Counter reset detection (handles sleep/resume)

**Key Classes:**
- `NetworkMonitor` - Main monitoring class with async loops

**Global Instance:** `monitor` - Singleton instance for application-wide use

```python
from src.core.monitor import monitor

# Get current speed
speed_sent, speed_received = monitor.get_current_speed()

# Start monitoring (async)
await monitor.start()
```

#### `storage.py` - Storage

**Responsibilities:**
- SQLite database management with context managers
- Usage log insertion with automatic aggregation
- Daily/monthly aggregate maintenance
- Data cleanup and vacuum operations
- Sync status tracking

**Key Classes:**
- `Storage` - Database manager with connection pooling

**Database Tables:**
- `devices` - Device registration
- `usage_logs` - Raw usage data with sync status
- `daily_aggregates` - Daily summaries with peak speeds
- `monthly_aggregates` - Monthly summaries
- `sync_cursor` - Sync position tracking
- `system_state` - Persistent key-value state

```python
from src.core.storage import storage

# Get today's usage
sent, received, peak = storage.get_today_usage()

# Insert usage data
storage.insert_usage(bytes_sent=1024, bytes_received=2048, speed=500)
```

#### `sync.py` - NeonSync

**Responsibilities:**
- Async NeonDB (PostgreSQL) synchronization
- Connection pool management with `asyncpg`
- Remote schema initialization
- Batch sync with retry logic
- Global usage aggregation across devices
- Storage cleanup for NeonDB free tier

**Key Classes:**
- `NeonSync` - Cloud sync manager

**Configuration:**
- Requires `NEON_DB_URL` environment variable
- Sync interval: 300 seconds (5 minutes) by default

```python
from src.core.sync import sync

# Check if sync is enabled
if sync.enabled:
    # Get global usage across all devices
    global_sent, global_received = await sync.get_global_today_usage()
```

#### `device.py` - Device Management

**Responsibilities:**
- Persistent device UUID generation and storage
- OS detection (Darwin, Windows, Linux)
- Hostname retrieval

**Key Functions:**
- `get_or_create_device_id()` - Returns persistent UUID
- `get_device_info()` - Returns `(device_id, os_type, hostname)`

---

### `src/api/` - REST API

FastAPI-based REST API for the dashboard and external integrations.

#### `server.py` - FastAPI Application

**Responsibilities:**
- FastAPI app creation with CORS middleware
- Static file serving for dashboard
- Background service lifecycle management
- Periodic cleanup tasks
- Auto-update scheduling

**Key Functions:**
- `run_server()` - Entry point for uvicorn server
- `startup_event()` - Starts monitor and sync services
- `shutdown_event()` - Graceful shutdown handling
- `periodic_cleanup()` - Scheduled data cleanup

**Endpoints:**
- `GET /` - Redirect to dashboard
- `GET /dashboard/*` - Static dashboard files

#### `routes.py` - API Endpoints

**All endpoints prefixed with `/api`:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check with device info |
| `/live` | GET | Current upload/download speed |
| `/today` | GET | Today's total usage with cost |
| `/cost` | GET | Cost calculation for today's usage |
| `/month` | GET | Monthly usage breakdown by day |
| `/summary` | GET | Lifetime total usage |
| `/range` | GET | Usage for arbitrary date range |
| `/export` | GET | Export data (JSON, CSV, HTML, LLM) |
| `/export/llm` | GET | LLM-friendly export (TOON format) |
| `/storage` | GET | Storage statistics (local + NeonDB) |
| `/storage/cleanup` | POST | Manual cleanup trigger |

**Export Formats:**
- `json` - Comprehensive JSON with all statistics
- `csv` - CSV with daily aggregates
- `html` - Beautiful year wrap-up HTML report
- `llm` - Token-optimized TOON format for AI analysis

---

### `src/cli/` - CLI Interface

Click-based command-line interface for direct user interaction.

#### `main.py` - CLI Commands

**Commands:**

| Command | Description |
|---------|-------------|
| `pb live` | Show current upload/download speed |
| `pb today` | Show today's usage |
| `pb month [YYYY-MM]` | Show monthly usage breakdown |
| `pb summary` | Show lifetime usage summary |
| `pb export --format json/csv` | Export all usage data |
| `pb serve` | Start API server and dashboard |
| `pb update [--check-only] [--force]` | Check/apply updates |
| `pb stats` | Show database statistics |
| `pb cleanup [--dry-run]` | Clean up old synced logs |
| `pb storage cleanup` | Storage cleanup command group |
| `pb storage stats` | Database storage statistics |
| `pb storage neon` | NeonDB storage statistics |
| `pb neon-cleanup` | Aggressive NeonDB cleanup |
| `pb service start/stop/restart` | Manage background service |

**Windows Compatibility:**
- Emojis automatically replaced with ASCII fallbacks on Windows
- Table format adjusted for Windows console (`grid` instead of `fancy_grid`)

---

### `src/utils/` - Utilities

#### `config.py` - Configuration

**Responsibilities:**
- TOML-based configuration management
- Default configuration with deep merge
- Environment variable support (`NEON_DB_URL`)
- Storage retention configuration

**Configuration Structure:**
```toml
[monitoring]
poll_interval = 1
batch_write_interval = 30
max_delta_bytes = 1_000_000_000

[sync]
enabled = true
interval = 300

[api]
host = "127.0.0.1"
port = 7373

[storage]
log_retention_days = 30
aggregate_retention_months = 12
cleanup_interval_hours = 24

[storage.neon]
log_retention_days = 7
aggregate_retention_months = 3
```

**Data Classes:**
- `NeonStorageConfig` - NeonDB-specific settings
- `StorageConfig` - Overall storage settings

#### `formatters.py` - Data Formatting

**Key Functions:**
- `format_bytes(bytes_count)` - Convert to human-readable (KB, MB, GB)
- `format_speed(bytes_per_second)` - Format speed with /s suffix
- `format_usage_response(sent, received, peak)` - API response formatting

**Note:** Uses 1000-base (not 1024) to match ISP/billing standards.

#### `cost_calculator.py` - Cost Calculations

**Key Constants:**
- `DEFAULT_COST_PER_GB_INR = 7.50` - Indian mobile data average (2026)

**Key Functions:**
- `calculate_cost(bytes, cost_per_gb)` - Calculate cost for bytes
- `get_cost_breakdown(sent, received, cost_per_gb)` - Detailed breakdown
- `estimate_monthly_cost(daily_bytes, days, cost_per_gb)` - Monthly estimate

#### `updater.py` - Auto-Update System

**Responsibilities:**
- Git-based auto-update from GitHub
- System PATH updates (Windows)
- Service registration (Windows Task Scheduler)
- Cross-platform service management

**Key Functions:**
- `check_for_updates()` - Returns (has_update, current, latest)
- `perform_update()` - Pulls latest changes
- `auto_update_check()` - Background update check with auto-apply

---

## Running in Development Mode

### Start the Development Server

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the API server
python -m src.api.server
```

The server will start at `http://127.0.0.1:7373` with:
- Dashboard at `/dashboard`
- API endpoints at `/api/*`

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEON_DB_URL` | PostgreSQL connection string for NeonDB | Optional (for cloud sync) |

### Configuration File

Create `~/.packetbuddy/config.toml` to override defaults:

```toml
[monitoring]
poll_interval = 2

[api]
port = 8080

[storage]
log_retention_days = 60
```

### Database Location

- **Local SQLite:** `~/.packetbuddy/packetbuddy.db`
- **Device ID:** `~/.packetbuddy/device_id`
- **Config:** `~/.packetbuddy/config.toml`

---

## Testing

### Current Status

**No test suite currently exists.** This is identified as a high-priority development task.

### Planned Testing Approach

```bash
# Run all tests (when implemented)
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_monitor.py

# Run with verbose output
pytest -v
```

### Testing Priorities

1. Unit tests for `formatters.py` and `cost_calculator.py`
2. Integration tests for `storage.py`
3. API endpoint tests for `routes.py`
4. Mock-based tests for `sync.py`

---

## Building and Packaging

### Current Distribution

PacketBuddy is distributed as a Git repository with:
- Source code installation
- Virtual environment setup scripts
- Platform-specific service registration

### Build Commands

```bash
# No build process required - Python source distribution
# Users install via git clone and pip install -r requirements.txt
```

### Platform-Specific Setup

**macOS:**
```bash
./service/macos/setup.sh  # Creates LaunchAgent
```

**Windows:**
```powershell
.\service\windows\setup.ps1  # Creates Scheduled Task
```

**Linux:**
```bash
./service/linux/setup.sh  # Creates systemd user service
```

---

## Debugging Tips

### Log Files

- **Error log:** `~/.packetbuddy/stderr.log`
- **Console output:** Check terminal when running `python -m src.api.server`

### Common Issues

#### 1. Database Locked Errors

```bash
# Check for multiple instances
ps aux | grep packetbuddy

# Kill stray processes
pkill -f "src.api.server"
```

#### 2. Sync Not Working

```bash
# Verify NeonDB URL is set
echo $NEON_DB_URL

# Check sync status via API
curl http://127.0.0.1:7373/api/health | jq '.sync_enabled'
```

#### 3. Dashboard Not Loading

```bash
# Verify dashboard files exist
ls dashboard/

# Check file permissions
chmod -R 755 dashboard/
```

#### 4. Port Already in Use

```bash
# Find process using port 7373
lsof -i :7373  # macOS/Linux
netstat -ano | findstr :7373  # Windows

# Change port in config
echo '[api]\nport = 8080' > ~/.packetbuddy/config.toml
```

### Debug Mode

Enable verbose logging by modifying `server.py`:

```python
uvicorn.run(
    app,
    host=host,
    port=port,
    log_level="debug",  # Change from "warning"
)
```

### Database Inspection

```bash
# Open SQLite database
sqlite3 ~/.packetbuddy/packetbuddy.db

# Useful queries
SELECT * FROM daily_aggregates ORDER BY date DESC LIMIT 10;
SELECT COUNT(*) FROM usage_logs WHERE synced = 0;
SELECT * FROM system_state;
```

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run linters
black src/
isort src/
flake8 src/
mypy src/

# Test manually
python -m src.api.server
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add amazing feature"
```

**Commit Message Format:**

| Prefix | Description |
|--------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `style:` | Formatting, missing semicolons, etc. |
| `refactor:` | Code restructuring |
| `test:` | Adding tests |
| `chore:` | Maintenance tasks |

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/amazing-feature

# Go to GitHub and create a Pull Request
```

### 6. PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex areas
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
- [ ] Related issues linked

### Code Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Maintainer Review**: A maintainer reviews your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, your PR will be merged
5. **Release**: Your contribution will be in the next release

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:

- Age, body size, disability
- Ethnicity, gender identity and expression
- Level of experience, education
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**

- Being respectful and welcoming
- Being patient with beginners
- Accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy

**Unacceptable behavior:**

- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## Questions?

- **General Questions**: [GitHub Discussions](https://github.com/instax-dutta/packet-buddy/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/instax-dutta/packet-buddy/issues)
- **Email**: See repository for contact information

## Recognition

Contributors are recognized in:

- [AUTHORS.md](../AUTHORS.md) file
- Release notes
- GitHub contributors page

Your contributions, no matter how small, are valued and appreciated!

---

**Thank you for making PacketBuddy better!**

Made with love by the PacketBuddy community
