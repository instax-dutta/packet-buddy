# PacketBuddy Installation Guide

This guide covers installing, configuring, and maintaining PacketBuddy across Windows, macOS, and Linux platforms.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
   - [Quick Install](#quick-install)
   - [Manual Installation](#manual-installation)
3. [Post-Installation Setup](#post-installation-setup)
4. [Verifying Installation](#verifying-installation)
5. [Updating PacketBuddy](#updating-packetbuddy)
6. [Uninstallation](#uninstallation)

---

## System Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.11 or higher |
| **Operating System** | Windows 10/11, macOS 12+, Linux (modern distributions) |
| **Memory** | 512 MB RAM minimum |
| **Disk Space** | 100 MB minimum |
| **Network** | Administrative/root privileges for packet capture |

### Platform-Specific Notes

- **Windows**: Administrator privileges required for setup and packet capture
- **macOS**: May need to grant permissions in System Preferences > Security & Privacy
- **Linux**: Root/sudo access required for packet capture interfaces

---

## Installation Methods

### Quick Install

#### Windows

Run the automated setup script with administrator privileges:

```powershell
# Right-click and "Run as administrator" or use PowerShell:
.\setup.bat
```

The setup.bat script automatically:
- Detects and validates Python installation
- Creates a virtual environment
- Installs all dependencies
- Configures the PacketBuddy command

#### Unix (macOS/Linux)

Run the shell setup script:

```bash
chmod +x setup.sh
./setup.sh
```

The setup.sh script handles:
- Python version verification
- Virtual environment creation
- Dependency installation
- Command-line tool configuration

---

### Manual Installation

For users who prefer manual control or have specific environment requirements:

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/packet-buddy.git
cd packet-buddy
```

#### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Unix (macOS/Linux):**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

#### Step 4: Verify Installation

```bash
pb --version
```

---

## Post-Installation Setup

### Service Installation

PacketBuddy includes service files in the `service/` directory for running as a background service.

#### Windows Task Scheduler Setup

1. Open Task Scheduler (taskschd.msc)

2. Create a new task:
   - **General**: Name it "PacketBuddy", select "Run whether user is logged on or not"
   - **Triggers**: Add "At startup" trigger
   - **Actions**: Add "Start a program" action
     - Program: `D:\packet-buddy\venv\Scripts\pb.exe`
     - Arguments: `serve`

3. Or use the command line:

```powershell
# Create scheduled task via command line
schtasks /create /tn "PacketBuddy" /tr "D:\packet-buddy\venv\Scripts\pb.exe serve" /sc onstart /ru SYSTEM
```

4. Manage the service:

```powershell
pb service start
pb service stop
pb service restart
```

#### Linux systemd Service Setup

1. Copy the service file:

```bash
sudo cp service/packetbuddy.service /etc/systemd/system/
```

2. Edit the service file to match your installation path:

```bash
sudo nano /etc/systemd/system/packetbuddy.service
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable packetbuddy
sudo systemctl start packetbuddy
```

4. Manage the service:

```bash
# Using systemctl
sudo systemctl start packetbuddy
sudo systemctl stop packetbuddy
sudo systemctl restart packetbuddy
sudo systemctl status packetbuddy

# Or using pb command
pb service start
pb service stop
pb service restart
```

#### macOS launchd Setup

1. Copy the launchd plist:

```bash
cp service/com.packetbuddy.plist ~/Library/LaunchAgents/
```

2. Edit the plist to match your installation path:

```bash
nano ~/Library/LaunchAgents/com.packetbuddy.plist
```

3. Load and start the service:

```bash
launchctl load ~/Library/LaunchAgents/com.packetbuddy.plist
launchctl start com.packetbuddy
```

4. Manage the service:

```bash
# Stop
launchctl stop com.packetbuddy

# Unload (disable from auto-start)
launchctl unload ~/Library/LaunchAgents/com.packetbuddy.plist

# Or using pb command
pb service start
pb service stop
pb service restart
```

---

## Verifying Installation

### Check Version

```bash
pb --version
```

### Run a Quick Test

```bash
# Start the server
pb serve

# In another terminal, test the service
pb service status
```

### Verify Dependencies

```bash
pb --check-deps
```

### Test Packet Capture

```bash
# Requires elevated privileges
sudo pb capture --test
```

---

## Updating PacketBuddy

### Using the Update Command

```bash
pb update
```

This command:
- Pulls the latest changes from the repository
- Updates dependencies
- Restarts the service if running

### Manual Update

```bash
# Navigate to installation directory
cd D:\packet-buddy

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Unix:
source venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service if applicable
pb service restart
```

---

## Uninstallation

### Remove Service

**Windows:**
```powershell
# Remove scheduled task
schtasks /delete /tn "PacketBuddy" /f

# Or disable via Task Scheduler
```

**Linux:**
```bash
sudo systemctl stop packetbuddy
sudo systemctl disable packetbuddy
sudo rm /etc/systemd/system/packetbuddy.service
sudo systemctl daemon-reload
```

**macOS:**
```bash
launchctl unload ~/Library/LaunchAgents/com.packetbuddy.plist
rm ~/Library/LaunchAgents/com.packetbuddy.plist
```

### Remove Files

```bash
# Delete the installation directory
rm -rf D:\packet-buddy   # Windows
rm -rf ~/packet-buddy    # Unix
```

### Clean Up Virtual Environment

If manually installed, deactivate and remove:

```bash
deactivate
rm -rf venv
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `pb: command not found` | Ensure virtual environment is activated or pb is in PATH |
| Permission denied (packet capture) | Run with administrator/sudo privileges |
| Python version mismatch | Install Python 3.11+ and ensure it's in PATH |
| Service fails to start | Check logs: `pb logs` or system logs |

### Getting Help

- Check logs: `pb logs --tail`
- GitHub Issues: https://github.com/yourusername/packet-buddy/issues
- Documentation: See other wiki pages

---

## Next Steps

After installation, see:
- [Getting Started Guide](Getting-Started.md)
- [Configuration Reference](Configuration.md)
- [Command Reference](Command-Reference.md)
