"""Auto-update functionality for PacketBuddy."""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/instax-dutta/packet-buddy.git"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def is_git_repo() -> bool:
    """Check if the project is in a git repository."""
    git_dir = PROJECT_ROOT / ".git"
    return git_dir.exists()


def get_current_commit() -> Optional[str]:
    """Get the current commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to get current commit: {e}")
    return None


def get_remote_commit() -> Optional[str]:
    """Get the latest commit hash from remote."""
    try:
        # Fetch latest without pulling
        subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to get remote commit: {e}")
    return None


def check_for_updates() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if updates are available.
    
    Returns:
        Tuple of (has_update, current_commit, latest_commit)
    """
    if not is_git_repo():
        logger.warning("Not a git repository, auto-update disabled")
        return False, None, None
    
    current = get_current_commit()
    if not current:
        return False, None, None
    
    latest = get_remote_commit()
    if not latest:
        return False, current, None
    
    has_update = current != latest
    return has_update, current, latest


def perform_update() -> bool:
    """
    Perform the update by pulling latest changes.
    
    Returns:
        True if update was successful, False otherwise
    """
    try:
        logger.info("Starting auto-update...")
        
        # Stash any local changes (if any)
        subprocess.run(
            ["git", "stash"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Git pull failed: {result.stderr}")
            return False
        
        # Update dependencies if requirements.txt changed
        requirements_file = PROJECT_ROOT / "requirements.txt"
        if requirements_file.exists():
            logger.info("Updating dependencies...")
            venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
            
            if venv_python.exists():
                subprocess.run(
                    [str(venv_python), "-m", "pip", "install", "--quiet", "-r", str(requirements_file)],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=120
                )
        
        # Update system PATH and service registration
        logger.info("Updating system PATH and service registration...")
        update_path()
        register_service()
        
        logger.info("Auto-update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False


def update_path() -> bool:
    """
    Update the system PATH to include the PacketBuddy scripts directory.
    This ensures the 'pb' command works after an update, especially if the
    installation directory has changed.
    
    Returns:
        True if PATH was updated or already correct, False on error.
    """
    import platform
    system = platform.system()
    
    scripts_dir = str(PROJECT_ROOT / "scripts")
    
    try:
        if system == "Windows":
            # Use PowerShell to update User PATH
            # This script:
            # 1. Gets current user PATH
            # 2. Removes any stale packet-buddy paths
            # 3. Adds current scripts directory if not present
            ps_script = '''
$scriptsDir = $env:PB_SCRIPTS_DIR
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')

# Split path into components
$pathParts = $currentPath -split ';' | Where-Object { $_ -ne '' }

# Remove any existing packet-buddy paths (stale or current)
$cleanedParts = $pathParts | Where-Object { $_ -notlike '*packet-buddy*scripts*' }

# Add current scripts directory
$cleanedParts += $scriptsDir

# Join and set the new PATH
$newPath = ($cleanedParts | Select-Object -Unique) -join ';'
[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')

Write-Host 'PATH updated successfully'
'''
            # Set environment variable for the PowerShell script
            env = os.environ.copy()
            env['PB_SCRIPTS_DIR'] = scripts_dir
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"PATH updated: added {scripts_dir}")
                return True
            else:
                logger.error(f"Failed to update PATH: {result.stderr}")
                return False
                
        elif system == "Darwin":
            # macOS - check common shell profiles
            logger.info("macOS detected. PATH update guidance:")
            logger.info(f"  Add to ~/.zshrc or ~/.bash_profile: export PATH=\"$PATH:{scripts_dir}\"")
            return True
            
        elif system == "Linux":
            # Linux - check common shell profiles  
            logger.info("Linux detected. PATH update guidance:")
            logger.info(f"  Add to ~/.bashrc or ~/.profile: export PATH=\"$PATH:{scripts_dir}\"")
            return True
            
    except Exception as e:
        logger.error(f"Failed to update PATH: {e}")
        return False
    
    return True


def register_service() -> bool:
    """
    Ensure the PacketBuddy service is registered with the OS.
    On Windows, this creates/updates a scheduled task with watchdog triggers.
    """
    import platform
    import subprocess
    system = platform.system()
    
    try:
        if system == "Windows":
            # Detect pythonw.exe in venv
            venv_pythonw = PROJECT_ROOT / "venv" / "Scripts" / "pythonw.exe"
            if not venv_pythonw.exists():
                venv_pythonw = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
            
            launcher_script = PROJECT_ROOT / "service" / "windows" / "launcher.py"
            
            if not venv_pythonw.exists() or not launcher_script.exists():
                return False
                
            # Use PowerShell to register a robust task
            ps_script = '''
$taskName = "PacketBuddy"
$pythonExe = $env:PB_PYTHON_EXE
$launcherScript = $env:PB_LAUNCHER_SCRIPT

$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$launcherScript`""
$triggers = @(
    New-ScheduledTaskTrigger -AtLogOn,
    New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 60)
)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0)

# Register/Update the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Settings $settings -Force
Write-Host "Service registered successfully"
'''
            env = os.environ.copy()
            env['PB_PYTHON_EXE'] = str(venv_pythonw)
            env['PB_LAUNCHER_SCRIPT'] = str(launcher_script)
            
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                timeout=30
            )
            return True
            
        elif system == "Darwin":
            # macOS - usually handled by setup.sh, but could verify launchd here
            return True
            
        elif system == "Linux":
            # Linux - usually handled by setup.sh, but could verify systemd here
            return True
            
    except Exception as e:
        logger.error(f"Failed to register service: {e}")
        return False
    
    return True


def restart_service():
    """Restart the PacketBuddy service after update."""
    stop_service()
    start_service()


def start_service():
    """Start the PacketBuddy service."""
    import platform
    system = platform.system()
    try:
        if system == "Darwin":
            os.system(f"launchctl kickstart -p gui/{os.getuid()}/com.packetbuddy.daemon")
        elif system == "Windows":
            subprocess.run(["schtasks", "/run", "/tn", "PacketBuddy"], capture_output=True)
        elif system == "Linux":
            subprocess.run(["systemctl", "--user", "start", "packetbuddy.service"], capture_output=True)
        logger.info("Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start service: {e}")


def stop_service():
    """Stop the PacketBuddy service."""
    import platform
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/com.packetbuddy.daemon"], capture_output=True)
        elif system == "Windows":
            subprocess.run(["schtasks", "/end", "/tn", "PacketBuddy"], capture_output=True)
        elif system == "Linux":
            subprocess.run(["systemctl", "--user", "stop", "packetbuddy.service"], capture_output=True)
        logger.info("Service stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop service: {e}")


def auto_update_check(force_restart: bool = True, auto_apply: bool = True) -> bool:
    """
    Check for updates and optionally apply them automatically.
    
    Args:
        force_restart: Whether to restart the service after update
        auto_apply: Whether to automatically apply updates (default: True)
        
    Returns:
        True if update was applied, False otherwise
    """
    has_update, current, latest = check_for_updates()
    
    if not has_update:
        logger.info("No updates available")
        return False
    
    logger.info(f"Update available: {current[:7] if current else 'unknown'} -> {latest[:7] if latest else 'unknown'}")
    
    if not auto_apply:
        logger.info("Auto-apply disabled, skipping update")
        return False
    
    logger.info("Automatically applying update...")
    
    if perform_update():
        logger.info("✅ Update applied successfully!")
        print(f"\n{'='*60}")
        print(f"📦 PacketBuddy Updated Successfully!")
        print(f"{'='*60}")
        print(f"Previous version: {current[:7] if current else 'unknown'}")
        print(f"New version: {latest[:7] if latest else 'unknown'}")
        print(f"{'='*60}\n")
        
        if force_restart:
            logger.info("Restarting service to apply changes...")
            print("🔄 Restarting service to apply changes...")
            restart_service()
            
        return True
    
    logger.error("❌ Update failed")
    return False
