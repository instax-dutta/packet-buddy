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
            timeout=10
        )
        
        result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
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
            timeout=10
        )
        
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
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
                    timeout=120
                )
        
        logger.info("Auto-update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False


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


def auto_update_check(force_restart: bool = True) -> bool:
    """
    Check for updates and apply them if available.
    
    Args:
        force_restart: Whether to restart the service after update
        
    Returns:
        True if update was applied, False otherwise
    """
    has_update, current, latest = check_for_updates()
    
    if not has_update:
        logger.info("No updates available")
        return False
    
    logger.info(f"Update available: {current[:7]} -> {latest[:7]}")
    
    if perform_update():
        logger.info("Update applied successfully!")
        
        if force_restart:
            logger.info("Restarting service...")
            restart_service()
            
        return True
    
    return False
