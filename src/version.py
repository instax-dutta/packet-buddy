"""Version information for PacketBuddy."""
from pathlib import Path

VERSION_FILE = Path(__file__).parent.parent / "VERSION"

def get_version() -> str:
    """Get the current version from VERSION file."""
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "1.3.2"  # Fallback

__version__ = get_version()
