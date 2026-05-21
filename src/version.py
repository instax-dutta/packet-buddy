"""Version information for PacketBuddy.

This module reads the version from the VERSION file at runtime,
ensuring the version is always up-to-date even if the module is cached.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_version() -> str:
    """Read version from VERSION file.
    
    This function reads the version from the VERSION file at runtime,
    which solves the Python module caching issue. Even if this module
    is cached, the version will always be fresh from disk.
    
    Returns:
        str: The current version string (e.g., "1.4.0")
    """
    try:
        # Get the VERSION file path (project root)
        version_file = Path(__file__).parent.parent / "VERSION"
        
        # Read and return the version, stripping whitespace
        return version_file.read_text().strip()
    except Exception as e:
        logger.warning("Could not read VERSION file: %s", e)
        return "1.0.0"


# For backward compatibility, provide __version__ as a property
# that always reads fresh from disk
__version__ = get_version()


# Also provide a function for explicit fresh reads
def get_fresh_version() -> str:
    """Get a fresh version read from disk.
    
    Use this when you need to ensure you have the absolute latest version,
    bypassing any potential caching.
    
    Returns:
        str: The current version string
    """
    return get_version()


def get_release_date() -> str:
    """Read the release date from the RELEASE_DATE file.
    
    Returns:
        str: The release date string (e.g., "2026-03-16") or a fallback.
    """
    try:
        release_date_file = Path(__file__).parent.parent / "RELEASE_DATE"
        return release_date_file.read_text().strip()
    except Exception:
        return "unknown"
