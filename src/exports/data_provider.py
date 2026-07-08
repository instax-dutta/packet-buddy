import logging
from datetime import date, datetime, timedelta
from typing import Optional
from collections import defaultdict

from ..core.storage import storage
from ..core.sync import sync
from ..core.device import get_device_info
from ..utils.formatters import format_bytes
from ..utils.cost_calculator import get_cost_breakdown

logger = logging.getLogger(__name__)

PERSONALITIES = [
    {
        "type": "Streamer",
        "icon": "🎬",
        "min_ratio": 0,
        "max_ratio": 0.3,
        "desc": "You mostly consume content — streaming, browsing, and downloading. Your upload is relatively low compared to your download.",
    },
    {
        "type": "Browsing",
        "icon": "🌐",
        "min_ratio": 0.3,
        "max_ratio": 0.6,
        "desc": "A balanced casual user. You upload a fair amount — social media posts, file sharing, and occasional video calls.",
    },
    {
        "type": "Creator",
        "icon": "🎨",
        "min_ratio": 0.6,
        "max_ratio": 1.0,
        "desc": "You upload almost as much as you download. Content creators, streamers, and remote workers fall in this category.",
    },
    {
        "type": "Power User",
        "icon": "⚡",
        "min_ratio": 1.0,
        "max_ratio": float("inf"),
        "desc": "You upload more than you download — running servers, seeding torrents, or heavy cloud backups. Your upload pipeline is the star.",
    },
]


def classify_personality(sent: int, received: int) -> dict:
    ratio = sent / max(received, 1)
    for p in PERSONALITIES:
        if p["min_ratio"] <= ratio < p["max_ratio"]:
            return p
    return PERSONALITIES[-1]


def compute_comparisons(total_bytes: int) -> dict:
    gb = total_bytes / (1024 ** 3)
    return {
        "dvd_equivalent": max(0, round(gb / 4.7, 1)),
        "hd_movies": max(0, round(gb / 5, 1)),
        "web_pages": max(0, total_bytes // (2 * 1024 * 1024)),
        "coffee_cups": max(0, round(gb * 0.5, 1)),
    }


def compute_export_data(
    range_type: str = "all",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_global: bool = True,
) -> dict:
    today = date.today()

    if range_type == "today":
        start = today
        end = today
    elif range_type == "week":
        start = today - timedelta(days=today.weekday())
        end = today
    elif range_type == "month":
        start = today.replace(day=1)
        end = today
    elif range_type == "year":
        start = today.replace(month=1, day=1)
        end = today
    elif range_type == "custom":
        start = start_date if start_date else today
        end = end_date if end_date else today
    else:
        start = date.min
        end = today

    all_days = storage.get_all_daily_aggregates()

    for d in all_days:
        if isinstance(d["date"], str):
            d["date"] = date.fromisoformat(d["date"])

    filtered = [d for d in all_days if start <= d["date"] <= end]

    if not filtered:
        return {
            "total_sent": 0,
            "total_received": 0,
            "total_bytes": 0,
            "days_tracked": 0,
            "daily_avg": 0,
            "peak_speed": 0,
            "peak_day": None,
            "personality": classify_personality(0, 1),
            "fun_comparisons": compute_comparisons(0),
            "monthly_breakdown": [],
            "cost": get_cost_breakdown(0, 0),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

    total_sent = sum(d["bytes_sent"] for d in filtered)
    total_received = sum(d["bytes_received"] for d in filtered)
    total_bytes = total_sent + total_received
    days_tracked = len(filtered)

    daily_avg = round(total_bytes / days_tracked) if days_tracked else 0

    peak_day_entry = max(filtered, key=lambda d: d.get("peak_speed", 0))
    peak_speed = peak_day_entry.get("peak_speed", 0) if peak_day_entry else 0
    peak_day = peak_day_entry["date"].isoformat() if peak_day_entry else None

    personality = classify_personality(total_sent, total_received)
    comparisons = compute_comparisons(total_bytes)
    cost = get_cost_breakdown(total_sent, total_received)

    monthly = defaultdict(lambda: {"sent": 0, "received": 0})
    for d in filtered:
        month_key = d["date"].strftime("%Y-%m")
        monthly[month_key]["sent"] += d["bytes_sent"]
        monthly[month_key]["received"] += d["bytes_received"]

    monthly_breakdown = []
    for month_key in sorted(monthly.keys()):
        m = monthly[month_key]
        monthly_breakdown.append({
            "month": month_key,
            "bytes_sent": m["sent"],
            "bytes_received": m["received"],
            "total_bytes": m["sent"] + m["received"],
        })

    return {
        "total_sent": total_sent,
        "total_received": total_received,
        "total_bytes": total_bytes,
        "days_tracked": days_tracked,
        "daily_avg": daily_avg,
        "peak_speed": peak_speed,
        "peak_day": peak_day,
        "personality": personality,
        "fun_comparisons": comparisons,
        "monthly_breakdown": monthly_breakdown,
        "cost": cost,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }