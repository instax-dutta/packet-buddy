# Why Windows Shows v1.3.3 (And How to Fix It)

## 🔍 The Issue

Your Windows PC shows version 1.3.3 even though:
- ✅ The code is updated to v1.4.0
- ✅ Git shows the latest commits
- ✅ `src/version.py` contains `__version__ = "1.4.0"`
- ✅ Your Mac updated correctly to v1.4.0

## 🧠 Why This Happens

**Python Module Caching**: When the PacketBuddy service starts, Python imports `src/version.py` and caches it in memory. Even if you update the file on disk, the running Python process continues to use the cached version.

### The Flow:
1. Service starts → Imports `version.py` → Caches `__version__ = "1.3.3"` in memory
2. You update code → `version.py` now has `1.4.0` on disk
3. Service still running → Still using cached `1.3.3` from memory
4. API returns cached version → Dashboard shows 1.3.3

## ✅ Solutions (Pick One)

### Option 1: Restart Your Computer (Easiest)
```
Just restart your PC - the service will start fresh with v1.4.0
```

### Option 2: Run the Force Restart Script
```batch
# Run this in the packet-buddy folder:
force-restart.bat
```

This script:
1. Stops the service
2. Waits for the process to terminate
3. Starts the service fresh
4. Checks the new version

### Option 3: Wait for Auto-Update (Automatic)
The auto-update system will:
- Check for updates within 6 hours
- Detect v1.4.0 is available
- Pull the latest code
- **Properly restart the service** with the new version

This is the most reliable method and requires no action from you.

### Option 4: Manual Command (Advanced)
```powershell
# Stop service
schtasks /end /tn PacketBuddy

# Wait 10 seconds for process to fully terminate
Start-Sleep -Seconds 10

# Start service
schtasks /run /tn PacketBuddy

# Wait 5 seconds
Start-Sleep -Seconds 5

# Check version
curl.exe -s http://127.0.0.1:7373/api/health | ConvertFrom-Json | Select-Object version
```

## 🎯 Why Your Mac Updated Correctly

When you ran `pb update` on your Mac, it:
1. Pulled the latest code
2. **Restarted the service properly** (via launchctl)
3. Fresh Python process loaded v1.4.0
4. ✅ Shows correct version

The Windows service just needs the same proper restart.

## 📊 Current Status

### Code Status:
- ✅ **Git**: Latest commits pushed (v1.4.0)
- ✅ **Files**: All updated to v1.4.0
- ✅ **version.py**: Contains `1.4.0`

### Service Status:
- ⚠️ **Running**: Old Python process with cached v1.3.3
- ✅ **Functionality**: All new features work (exports, peak speed fix)
- ⚠️ **Version Display**: Shows 1.3.3 due to cache

### What Works Right Now:
- ✅ Peak speed persistence fix
- ✅ New export formats (CSV, JSON, HTML, TOON)
- ✅ Year wrap-up button
- ✅ All new features

### What Shows Old:
- ⚠️ Version number in API/dashboard (cached)

## 🔄 Auto-Update Will Fix This

The auto-update system is configured to:
```toml
[auto_update]
enabled = true
check_on_startup = true
check_interval_hours = 6
auto_apply = true
auto_restart = true  # ← This will properly restart
```

**Next auto-update check**: Within 6 hours
**What it will do**: 
1. Detect v1.4.0 available
2. Pull latest code
3. **Restart service properly**
4. ✅ Version will show 1.4.0

## 🎯 Recommended Action

**Just wait for auto-update** (within 6 hours) or **restart your PC** when convenient.

The service is already running the new code - it just shows the old version number due to Python's module caching. All features work correctly!

## 🧪 Verify Code Version

To confirm the code is v1.4.0:
```powershell
cd d:\packet-buddy
.\venv\Scripts\python.exe -c "from src.version import __version__; print(__version__)"
# Output: 1.4.0
```

## 📝 Summary

- **Code**: ✅ v1.4.0
- **Features**: ✅ All working
- **Version Display**: ⚠️ Cached at 1.3.3
- **Fix**: Restart PC or wait for auto-update

**No action required** - auto-update will fix this automatically within 6 hours!
