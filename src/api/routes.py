"""FastAPI routes for local HTTP API."""

import csv
import io
import json
from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse

from ..core.storage import storage
from ..core.monitor import monitor
from ..core.sync import sync
from ..core.device import get_device_info
from ..utils.formatters import format_usage_response
from ..utils.cost_calculator import get_cost_breakdown, DEFAULT_COST_PER_GB_INR
from ..utils.config import config
from ..version import get_fresh_version, get_release_date


router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """Service health check."""
    device_id, os_type, hostname = get_device_info()
    
    device_count = 1
    if sync.enabled:
        device_count = await sync.get_device_count()

    db_stats = storage.get_database_stats()
    db_size_mb = db_stats.get('db_size_mb', 0)
    
    storage_cfg = getattr(config, 'storage', None)
    max_storage_mb = getattr(storage_cfg, 'max_storage_mb', 400) if storage_cfg else 400
    
    storage_warning = None
    if db_size_mb > max_storage_mb:
        storage_warning = f"Database size ({db_size_mb}MB) exceeds limit ({max_storage_mb}MB)"

    return {
        "status": "running",
        "version": get_fresh_version(),
        "release_date": get_release_date(),
        "device_id": device_id,
        "os_type": os_type,
        "hostname": hostname,
        "device_count": device_count,
        "sync_enabled": sync.enabled,
        "timestamp": datetime.utcnow().isoformat(),
        "storage": {
            "db_size_mb": db_size_mb,
            "max_storage_mb": max_storage_mb,
            "usage_logs_count": db_stats.get('usage_logs_count', 0),
            "daily_aggregates_count": db_stats.get('daily_aggregates_count', 0),
            "monthly_aggregates_count": db_stats.get('monthly_aggregates_count', 0),
            "synced_count": db_stats.get('synced_count', 0),
            "unsynced_count": db_stats.get('unsynced_count', 0),
            "storage_usage_percent": db_stats.get('storage_usage_percent', 0),
            "warning": storage_warning
        }
    }


@router.get("/live")
async def live():
    """Current upload/download speed."""
    speed_sent, speed_received = monitor.get_current_speed()
    
    return format_usage_response(
        bytes_sent=int(speed_sent),
        bytes_received=int(speed_received)
    )


@router.get("/today")
async def today():
    """Today's total usage."""
    bytes_sent, bytes_received, peak_speed = storage.get_today_usage()
    
    response = format_usage_response(bytes_sent, bytes_received, peak_speed)
    
    # Add cost information
    cost_data = get_cost_breakdown(bytes_sent, bytes_received)
    response["cost"] = cost_data

    # Add global today stats if enabled
    if sync.enabled:
        global_sent, global_received = await sync.get_global_today_usage()
        
        response["global"] = format_usage_response(global_sent, global_received)
        response["global"]["cost"] = get_cost_breakdown(global_sent, global_received)
    
    return response


@router.get("/cost")
async def cost(cost_per_gb: float = Query(DEFAULT_COST_PER_GB_INR, description="Cost per GB in INR")):
    """
    Calculate cost for today's usage.
    
    Default: ₹7.50 per GB (average Indian mobile data cost)
    """
    bytes_sent, bytes_received, peak_speed = storage.get_today_usage()
    total_bytes = bytes_sent + bytes_received
    
    cost_data = get_cost_breakdown(bytes_sent, bytes_received, cost_per_gb)
    
    return {
        "usage": {
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_received,
            "total_bytes": total_bytes,
            "gb_used": round(total_bytes / (1024 ** 3), 2)
        },
        "cost": cost_data,
        "info": {
            "cost_per_gb_inr": cost_per_gb,
            "currency": "INR",
            "note": "Based on average Indian mobile data costs (2026)"
        }
    }


@router.get("/month")
async def month(month: Optional[str] = Query(None, description="YYYY-MM format")):
    """Monthly usage breakdown by day."""
    if month is None:
        month = datetime.utcnow().strftime("%Y-%m")
    
    daily_data = storage.get_month_usage(month)
    
    # Format response
    days = []
    total_sent = 0
    total_received = 0
    
    for row in daily_data:
        days.append({
            "date": row["date"],
            "bytes_sent": row["bytes_sent"],
            "bytes_received": row["bytes_received"],
            "total_bytes": row["bytes_sent"] + row["bytes_received"]
        })
        total_sent += row["bytes_sent"]
        total_received += row["bytes_received"]
    
    return {
        "month": month,
        "days": days,
        "summary": format_usage_response(total_sent, total_received)
    }


@router.get("/summary")
async def summary():
    """Lifetime total usage."""
    bytes_sent, bytes_received = storage.get_lifetime_usage()
    
    response = format_usage_response(bytes_sent, bytes_received)
    
    # Add cost information
    cost_data = get_cost_breakdown(bytes_sent, bytes_received)
    response["cost"] = cost_data

    # Add global lifetime stats if enabled
    if sync.enabled:
        global_sent, global_received = await sync.get_global_lifetime_usage()
        
        response["global"] = format_usage_response(global_sent, global_received)
        response["global"]["cost"] = get_cost_breakdown(global_sent, global_received)
    
    return response


@router.get("/range")
async def range_query(
    from_date: str = Query(..., description="YYYY-MM-DD"),
    to_date: str = Query(..., description="YYYY-MM-DD")
):
    """Usage for arbitrary date range."""
    try:
        start = datetime.strptime(from_date, "%Y-%m-%d").date()
        end = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid date format. Use YYYY-MM-DD"}
        )
    
    daily_data = storage.get_range_usage(start, end)
    
    # Format response
    days = []
    total_sent = 0
    total_received = 0
    
    for row in daily_data:
        days.append({
            "date": row["date"],
            "bytes_sent": row["bytes_sent"],
            "bytes_received": row["bytes_received"],
            "total_bytes": row["bytes_sent"] + row["bytes_received"]
        })
        total_sent += row["bytes_sent"]
        total_received += row["bytes_received"]
    
    return {
        "from": from_date,
        "to": to_date,
        "days": days,
        "summary": format_usage_response(total_sent, total_received)
    }


def _gather_export_data():
    """Shared data gathering for export endpoints.
    
    Collects all data from storage once, computes derived insights,
    and returns a complete data dict to avoid redundant DB queries.
    """
    from ..utils.formatters import format_bytes
    
    device_id, os_type, hostname = get_device_info()
    stats = storage.get_all_export_stats()
    
    daily_data = stats["daily_data"]
    monthly_summaries = stats["monthly_summaries"]
    total_sent = stats["total_sent"]
    total_received = stats["total_received"]
    overall_peak = stats["overall_peak"]
    tracking_stats = stats["tracking_stats"]
    
    total_bytes = total_sent + total_received
    days_tracked = tracking_stats.get("total_days_tracked", 0) if tracking_stats else 0
    avg_daily = total_bytes / max(days_tracked, 1)
    
    peak_day = max(daily_data, key=lambda x: x["bytes_sent"] + x["bytes_received"]) if daily_data else None
    
    today = date.today()
    current_year = today.year
    year_data = [d for d in daily_data if d["date"].startswith(str(current_year))]
    year_sent = sum(d["bytes_sent"] for d in year_data)
    year_received = sum(d["bytes_received"] for d in year_data)
    year_total = year_sent + year_received
    
    return {
        "device_id": device_id,
        "os_type": os_type,
        "hostname": hostname,
        "daily_data": daily_data,
        "monthly_summaries": monthly_summaries,
        "total_sent": total_sent,
        "total_received": total_received,
        "total_bytes": total_bytes,
        "overall_peak": overall_peak,
        "tracking_stats": tracking_stats,
        "days_tracked": days_tracked,
        "avg_daily": avg_daily,
        "peak_day": peak_day,
        "current_year": current_year,
        "year_data": year_data,
        "year_sent": year_sent,
        "year_received": year_received,
        "year_total": year_total,
        "format_bytes": format_bytes,
    }


@router.get("/export")
async def export(format: str = Query("json", description="csv, json, html, or llm")):
    """Export all usage data in various formats."""
    
    if format == "csv":
        return await export_csv()
    elif format == "html":
        return await export_html()
    elif format == "llm" or format == "toon":
        return await export_llm_friendly()
    else:
        # Enhanced JSON format
        return await export_json()


@router.get("/export/wrapup")
async def export_wrapup(format: str = Query("html", description="html or toon")):
    """Unified year wrap-up export.
    
    Generates a shareable HTML report or AI-friendly TOON format.
    Replaces the separate /export?format=html and /export/llm endpoints.
    """
    if format == "toon":
        return await export_llm_friendly()
    return await export_html()


async def export_csv():
    """Export data as CSV with comprehensive fields."""
    daily_data = storage.get_all_daily_aggregates()
    
    # Generate CSV with peak speeds
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "bytes_sent", "bytes_received", "total_bytes", "peak_speed"])
    writer.writeheader()
    
    for day in daily_data:
        writer.writerow({
            "date": day["date"],
            "bytes_sent": day["bytes_sent"],
            "bytes_received": day["bytes_received"],
            "total_bytes": day["bytes_sent"] + day["bytes_received"],
            "peak_speed": day["peak_speed"]
        })
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=packetbuddy_export.csv"}
    )


async def export_json():
    """Export comprehensive JSON with all statistics."""
    from ..utils.formatters import format_bytes
    
    device_id, os_type, hostname = get_device_info()
    
    # Get comprehensive data in a single connection
    stats = storage.get_all_export_stats()
    daily_data = stats["daily_data"]
    monthly_summaries = stats["monthly_summaries"]
    total_sent = stats["total_sent"]
    total_received = stats["total_received"]
    overall_peak = stats["overall_peak"]
    tracking_stats = stats["tracking_stats"]
    
    # Calculate insights
    total_bytes = total_sent + total_received
    days_tracked = tracking_stats.get("total_days_tracked", 0) if tracking_stats else 0
    avg_daily = total_bytes / max(days_tracked, 1)
    
    # Find peak day
    peak_day = max(daily_data, key=lambda x: x["bytes_sent"] + x["bytes_received"]) if daily_data else None
    
    export_data = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "device": {
                "hostname": hostname,
                "os_type": os_type,
                "device_id": device_id
            },
            "tracking_period": {
                "first_date": tracking_stats.get("first_tracked_date") if tracking_stats else None,
                "last_date": tracking_stats.get("last_tracked_date") if tracking_stats else None,
                "total_days": days_tracked
            }
        },
        "summary": {
            "totals": {
                "bytes_sent": total_sent,
                "bytes_received": total_received,
                "total_bytes": total_bytes,
                "human_readable": {
                    "sent": format_bytes(total_sent),
                    "received": format_bytes(total_received),
                    "total": format_bytes(total_bytes)
                }
            },
            "averages": {
                "daily_bytes": int(avg_daily),
                "daily_human": format_bytes(int(avg_daily))
            },
            "peak_speed": {
                "bytes_per_second": overall_peak,
                "human_readable": format_bytes(overall_peak) + "/s"
            },
            "peak_day": {
                "date": peak_day["date"] if peak_day else None,
                "bytes": (peak_day["bytes_sent"] + peak_day["bytes_received"]) if peak_day else 0,
                "human": format_bytes(peak_day["bytes_sent"] + peak_day["bytes_received"]) if peak_day else "0 B"
            } if peak_day else None
        },
        "monthly_data": [
            {
                "month": m["month"],
                "bytes_sent": m["bytes_sent"],
                "bytes_received": m["bytes_received"],
                "total_bytes": m["bytes_sent"] + m["bytes_received"],
                "peak_speed": m["peak_speed"],
                "days_tracked": m["days_tracked"],
                "human_readable": {
                    "sent": format_bytes(m["bytes_sent"]),
                    "received": format_bytes(m["bytes_received"]),
                    "total": format_bytes(m["bytes_sent"] + m["bytes_received"]),
                    "peak_speed": format_bytes(m["peak_speed"]) + "/s"
                }
            }
            for m in monthly_summaries
        ],
        "daily_data": [
            {
                "date": d["date"],
                "bytes_sent": d["bytes_sent"],
                "bytes_received": d["bytes_received"],
                "total_bytes": d["bytes_sent"] + d["bytes_received"],
                "peak_speed": d["peak_speed"],
                "human_readable": {
                    "sent": format_bytes(d["bytes_sent"]),
                    "received": format_bytes(d["bytes_received"]),
                    "total": format_bytes(d["bytes_sent"] + d["bytes_received"]),
                    "peak_speed": format_bytes(d["peak_speed"]) + "/s"
                }
            }
            for d in daily_data
        ]
    }
    
    return JSONResponse(content=export_data)


async def export_html():
    """Export beautiful, socially shareable HTML year wrap-up report."""
    d = _gather_export_data()
    fmt = d["format_bytes"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta property="og:title" content="PacketBuddy {d['current_year']} Wrap-Up — {d['hostname']}">
    <meta property="og:description" content="I used {fmt(d['year_total'])} of internet data this year! See my full breakdown.">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <title>PacketBuddy {d['current_year']} Year Wrap-Up — {d['hostname']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: #0a0a1a;
            color: #e8e8f0;
            padding: 0;
            line-height: 1.5;
        }}
        .wrap {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px;
        }}
        .card {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 24px;
            backdrop-filter: blur(8px);
        }}
        .hero {{
            text-align: center;
            padding: 48px 32px 36px;
            background: linear-gradient(135deg, #1a1a3e, #0f3460, #1a1a3e);
            border-bottom: 3px solid #e94560;
        }}
        .hero h1 {{
            font-size: 3.2em;
            font-weight: 900;
            letter-spacing: -1px;
            background: linear-gradient(90deg, #e94560, #0f3460, #533483);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .hero h1 span {{
            -webkit-text-fill-color: #e8e8f0;
        }}
        .hero .sub {{
            font-size: 1.15em;
            opacity: 0.7;
            margin-top: 8px;
            font-weight: 500;
        }}
        .hero-total {{
            margin-top: 28px;
            padding: 24px;
            background: rgba(233,69,96,0.12);
            border: 1px solid rgba(233,69,96,0.25);
            border-radius: 20px;
            display: inline-block;
            min-width: 320px;
        }}
        .hero-total .label {{ font-size: 0.85em; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }}
        .hero-total .value {{ font-size: 3em; font-weight: 900; margin: 4px 0; }}
        .hero-total .detail {{ font-size: 1em; opacity: 0.7; }}
        .hero-total .detail .up {{ color: #e94560; }}
        .hero-total .detail .down {{ color: #53d8fb; }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-top: 24px;
        }}
        .stat-item {{
            text-align: center;
            padding: 20px 12px;
            background: rgba(255,255,255,0.04);
            border-radius: 16px;
        }}
        .stat-item .num {{ font-size: 1.8em; font-weight: 900; }}
        .stat-item .lbl {{ font-size: 0.8em; opacity: 0.55; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; font-weight: 600; }}
        .stat-item .ico {{ font-size: 1.4em; margin-bottom: 6px; }}
        .section-title {{
            font-size: 1.5em;
            font-weight: 800;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .month-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 12px;
        }}
        .month-item {{
            background: rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 14px;
            text-align: center;
        }}
        .month-item .name {{ font-weight: 700; font-size: 0.9em; margin-bottom: 6px; opacity: 0.85; }}
        .month-item .vol {{ font-weight: 800; font-size: 1.1em; color: #53d8fb; }}
        .month-item .meta {{ font-size: 0.75em; opacity: 0.5; margin-top: 4px; }}
        .highlight {{
            background: linear-gradient(90deg, #e94560, #533483);
            border-radius: 16px;
            padding: 20px 24px;
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .highlight .hl-label {{ font-weight: 700; font-size: 0.9em; opacity: 0.85; }}
        .highlight .hl-value {{ font-weight: 900; font-size: 1.3em; }}
        .footer {{
            text-align: center;
            padding: 24px;
            opacity: 0.4;
            font-size: 0.85em;
        }}
        @media (max-width: 700px) {{
            .stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .hero h1 {{ font-size: 2em; }}
            .hero-total .value {{ font-size: 2em; }}
            .month-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="wrap">
        <div class="card hero">
            <h1>🌐 <span>{d['current_year']} Internet Wrap-Up</span></h1>
            <div class="sub">{d['hostname']} — {d['os_type']}</div>
            <div class="hero-total">
                <div class="label">Total Data This Year</div>
                <div class="value">{fmt(d['year_total'])}</div>
                <div class="detail">
                    <span class="up">↑ {fmt(d['year_sent'])}</span> &nbsp;•&nbsp; <span class="down">↓ {fmt(d['year_received'])}</span>
                </div>
            </div>
        </div>

        <div class="stat-grid">
            <div class="stat-item"><div class="ico">📊</div><div class="num">{fmt(d['total_bytes'])}</div><div class="lbl">All-Time Total</div></div>
            <div class="stat-item"><div class="ico">📅</div><div class="num">{d['days_tracked']}</div><div class="lbl">Days Tracked</div></div>
            <div class="stat-item"><div class="ico">⚡</div><div class="num">{fmt(d['overall_peak'])}/s</div><div class="lbl">Peak Speed</div></div>
            <div class="stat-item"><div class="ico">📈</div><div class="num">{fmt(int(d['avg_daily']))}</div><div class="lbl">Daily Avg</div></div>
        </div>"""[1:]
    
    html_content += """
        <div class="card">
            <div class="section-title">📆 Monthly Breakdown</div>
            <div class="month-grid">
"""    
    for m in d["monthly_summaries"]:
        month_name = datetime.strptime(m["month"] + "-01", "%Y-%m-%d").strftime("%b %Y")
        m_total = m["bytes_sent"] + m["bytes_received"]
        html_content += f"""
                <div class="month-item">
                    <div class="name">{month_name}</div>
                    <div class="vol">{fmt(m_total)}</div>
                    <div class="meta">↑ {fmt(m['bytes_sent'])} / ↓ {fmt(m['bytes_received'])}</div>
                </div>"""
    
    html_content += """
            </div>
        </div>

        <div class="card">
            <div class="section-title">🏆 Highlights</div>
"""
    if d["peak_day"]:
        pd = d["peak_day"]
        pd_date = datetime.strptime(pd["date"], "%Y-%m-%d").strftime("%B %d, %Y")
        pd_total = pd["bytes_sent"] + pd["bytes_received"]
        html_content += f"""
            <div class="highlight">
                <div><div class="hl-label">🌟 Most Active Day</div><div class="hl-value">{fmt(pd_total)}</div></div>
                <div style="text-align:right"><div class="hl-label">{pd_date}</div><div class="hl-value" style="font-size:1em;opacity:0.7">↑ {fmt(pd['bytes_sent'])} / ↓ {fmt(pd['bytes_received'])}</div></div>
            </div>"""
    
    ratio = d["total_sent"] / max(d["total_received"], 1)
    dvd_count = int(d["total_bytes"] / (1024**3) / 4.7)
    cd_count = int(d["total_bytes"] / (1024**3) / 0.7)
    html_content += f"""
            <div class="highlight" style="background:linear-gradient(90deg,#1a1a3e,#16213e);border:1px solid rgba(255,255,255,0.06)">
                <div><div class="hl-label">⚖️ Upload/Download Ratio</div><div class="hl-value">{ratio:.2f}:1</div></div>
                <div><div class="hl-label">💾 Storage Equivalent</div><div class="hl-value">{dvd_count} DVDs</div></div>
            </div>
        </div>

        <div class="footer">
            Generated by <strong>PacketBuddy</strong> v{get_fresh_version()} &bull; {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}
            <br>Device: {d['hostname']} ({d['os_type']})
        </div>
    </div>
</body>
</html>
"""
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=packetbuddy_wrap_up_{d['current_year']}.html"
        }
    )


@router.get("/export/llm")
async def export_llm_friendly():
    """Export data in TOON format (Token Optimized Object Notation) for LLM analysis."""
    d = _gather_export_data()
    fmt = d["format_bytes"]
    today = date.today()
    
    report = f"""# PacketBuddy Network Usage Export - TOON Format

[meta]
format = "TOON (Token Optimized Object Notation)"
generated = "{datetime.utcnow().isoformat()}"
device = "{d['hostname']}"
os = "{d['os_type']}"
device_id = "{d['device_id']}"
version = "{get_fresh_version()}"

[tracking]
first_date = "{d['tracking_stats'].get("first_tracked_date", "N/A")}"
last_date = "{d['tracking_stats'].get("last_tracked_date", "N/A")}"
total_days = {d['days_tracked']}

[totals]
bytes_sent = {d['total_sent']}
bytes_received = {d['total_received']}
total_bytes = {d['total_bytes']}
human = {{sent="{fmt(d['total_sent'])}", received="{fmt(d['total_received'])}", total="{fmt(d['total_bytes'])}"}}

[year_{d['current_year']}]
bytes_sent = {d['year_sent']}
bytes_received = {d['year_received']}
total_bytes = {d['year_total']}
days = {len(d['year_data'])}
human = {{sent="{fmt(d['year_sent'])}", received="{fmt(d['year_received'])}", total="{fmt(d['year_total'])}"}}

[records]
peak_speed_bps = {d['overall_peak']}
peak_speed_human = "{fmt(d['overall_peak'])}/s"
"""
    
    if d["peak_day"]:
        pd = d["peak_day"]
        pd_total = pd["bytes_sent"] + pd["bytes_received"]
        report += f"""peak_day_date = "{pd['date']}"
peak_day_bytes = {pd_total}
peak_day_human = "{fmt(pd_total)}"
peak_day_sent = {pd['bytes_sent']}
peak_day_received = {pd['bytes_received']}
peak_day_speed = {pd['peak_speed']}
"""
    
    ratio = d["total_sent"] / max(d["total_received"], 1)
    report += f"""
[averages]
daily_bytes = {int(d['avg_daily'])}
daily_human = "{fmt(int(d['avg_daily']))}"

[ratios]
upload_download = {ratio:.2f}
upload_percent = {(d['total_sent'] / max(d['total_bytes'], 1) * 100):.1f}
download_percent = {(d['total_received'] / max(d['total_bytes'], 1) * 100):.1f}

[comparisons]
dvd_equivalent = {int(d['total_bytes'] / (1024**3) / 4.7)}
cd_equivalent = {int(d['total_bytes'] / (1024**3) / 0.7)}
hd_movie_equivalent = {int(d['total_bytes'] / (1024**3) / 5)}

"""
    
    report += "[monthly_data]\n"
    for i, m in enumerate(d["monthly_summaries"]):
        m_total = m["bytes_sent"] + m["bytes_received"]
        report += f"""month_{i} = {{name="{m['month']}", sent={m['bytes_sent']}, received={m['bytes_received']}, total={m_total}, peak={m['peak_speed']}, days={m['days_tracked']}, human="{fmt(m_total)}"}}
"""
    
    report += "\n[recent_30_days]\n"
    recent_data = [dd for dd in d["daily_data"] if datetime.strptime(dd["date"], "%Y-%m-%d").date() >= today - timedelta(days=30)]
    for i, day in enumerate(sorted(recent_data, key=lambda x: x["date"], reverse=True)[:30]):
        day_total = day["bytes_sent"] + day["bytes_received"]
        report += f"""day_{i} = {{date="{day['date']}", sent={day['bytes_sent']}, received={day['bytes_received']}, total={day_total}, peak={day['peak_speed']}}}
"""
    
    report += f"""
[llm_prompts]
year_wrapup = "Create a fun, Spotify-style {d['current_year']} wrap-up based on this network usage data. Include interesting insights, fun facts, and comparisons."
professional = "Generate a professional network usage summary highlighting efficiency, patterns, and recommendations for optimization."
personal = "Analyze my internet usage patterns and give me insights about my digital life. What does this data say about my online behavior?"
trends = "Identify trends in my internet usage over time. Are there seasonal patterns? Which months had unusual activity?"

[interpretation]
note_1 = "1 GB = 1,073,741,824 bytes"
note_2 = "Upload = Data sent from device to internet"
note_3 = "Download = Data received from internet to device"
note_4 = "Peak speed = Highest combined upload+download speed in bytes/second"
note_5 = "All byte values are in raw bytes unless marked with 'human' suffix"

[usage_tips]
tip_1 = "This TOON format uses ~60% fewer tokens than markdown"
tip_2 = "All data is preserved in compact key=value format"
tip_3 = "Use the llm_prompts section for suggested analysis questions"
tip_4 = "Human-readable values are in 'human' fields for easy reading"
tip_5 = "Monthly and daily data use indexed format (month_0, day_0, etc.)"
"""
    
    return Response(
        content=report,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=packetbuddy_export_{today.strftime('%Y%m%d')}.toon"
        }
    )


@router.get("/storage")
async def storage_info():
    """Get comprehensive storage information for both local and NeonDB."""
    local_stats = storage.get_database_stats()
    
    response = {
        "local": {
            "db_size_mb": local_stats.get('db_size_mb', 0),
            "max_storage_mb": config.storage.max_storage_mb,
            "usage_percent": local_stats.get('storage_usage_percent', 0),
            "usage_logs_count": local_stats.get('usage_logs_count', 0),
            "daily_aggregates_count": local_stats.get('daily_aggregates_count', 0),
            "monthly_aggregates_count": local_stats.get('monthly_aggregates_count', 0),
            "synced_count": local_stats.get('synced_count', 0),
            "unsynced_count": local_stats.get('unsynced_count', 0),
            "oldest_log": local_stats.get('oldest_timestamp'),
            "newest_log": local_stats.get('newest_timestamp'),
        },
        "neon": None,
        "retention": {
            "local_log_days": config.storage.log_retention_days,
            "local_aggregate_months": config.storage.aggregate_retention_months,
            "neon_aggregate_months": config.storage.neon.neon_aggregate_retention_months if hasattr(config.storage, 'neon') else 6,
        }
    }
    
    if sync.enabled:
        try:
            neon_storage = await sync.get_storage_usage()
            neon_usage_percent = await sync.get_storage_usage_percent()
            neon_stats = await sync.get_remote_stats()
            
            neon_config = getattr(config.storage, 'neon', None)
            warning_threshold = neon_config.neon_storage_warning_threshold if neon_config else 80
            max_storage_mb = neon_config.neon_max_storage_mb if neon_config else 450
            
            response["neon"] = {
                "total_mb": neon_storage.get("total_mb", 0),
                "max_storage_mb": max_storage_mb,
                "usage_percent": neon_usage_percent,
                "free_tier_limit_mb": 512,
                "warning_threshold_percent": warning_threshold,
                "tables": neon_storage.get("tables", {}),
                "device_count": neon_stats.get("device_count", 0),
                "daily_count": neon_stats.get("daily_count", 0),
                "monthly_count": neon_stats.get("monthly_count", 0),
            }
            
            if neon_usage_percent >= warning_threshold:
                response["neon"]["warning"] = f"NeonDB storage at {neon_usage_percent}% - consider cleanup"
            if neon_usage_percent >= 90:
                response["neon"]["critical"] = f"NeonDB storage CRITICAL at {neon_usage_percent}% - immediate cleanup recommended"
                
        except Exception as e:
            response["neon"] = {"error": str(e)}
    
    return response


@router.post("/storage/cleanup")
async def trigger_cleanup(
    aggressive: bool = Query(False, description="Run aggressive cleanup for storage crisis"),
    vacuum: bool = Query(True, description="Run VACUUM after cleanup")
):
    """Manually trigger storage cleanup for both local and NeonDB."""
    results = {
        "local": {"logs_deleted": 0, "aggregates_deleted": {}},
        "neon": None,
        "vacuum_run": False
    }
    
    try:
        deleted_logs = storage.cleanup_synced_logs(config.storage.log_retention_days)
        deleted_aggregates = storage.cleanup_old_aggregates(config.storage.aggregate_retention_months)
        results["local"] = {
            "logs_deleted": deleted_logs,
            "aggregates_deleted": deleted_aggregates
        }
        
        if vacuum:
            storage.vacuum_database()
            results["vacuum_run"] = True
    except Exception as e:
        results["local"]["error"] = str(e)
    
    if sync.enabled:
        try:
            neon_config = getattr(config.storage, 'neon', None)
            neon_agg_months = neon_config.neon_aggregate_retention_months if neon_config else 6
            
            if aggressive:
                neon_results = await sync.aggressive_cleanup()
            else:
                neon_aggregates = await sync.cleanup_old_aggregates(neon_agg_months)
                neon_results = {
                    "aggregates_deleted": neon_aggregates,
                    "vacuum_run": False
                }
            
            if vacuum:
                neon_results["vacuum_run"] = await sync.vacuum_database()
            
            results["neon"] = neon_results
            
            results["neon"]["storage_after_percent"] = await sync.get_storage_usage_percent()
            
        except Exception as e:
            results["neon"] = {"error": str(e)}
    
    return results

