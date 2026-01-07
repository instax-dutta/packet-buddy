"""Human-readable formatting utilities."""

from typing import Dict


def format_bytes(bytes_count: int) -> str:
    """Convert bytes to human-readable format."""
    if bytes_count < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(bytes_count)
    unit_index = 0
    
    # Use 1000-base to match Bandwidth+, ISPs, and consumer billing standards
    while size >= 1000 and unit_index < len(units) - 1:
        size /= 1000
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_speed(bytes_per_second: float) -> str:
    """Format speed in bytes/sec to human-readable format."""
    return f"{format_bytes(int(bytes_per_second))}/s"


def format_usage_response(bytes_sent: int, bytes_received: int) -> Dict:
    """Format usage data for API responses."""
    total_bytes = bytes_sent + bytes_received
    
    return {
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "total_bytes": total_bytes,
        "human_readable": {
            "sent": format_bytes(bytes_sent),
            "received": format_bytes(bytes_received),
            "total": format_bytes(total_bytes),
        }
    }
