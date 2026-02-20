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
from ..version import get_fresh_version


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
        # Ensure global is at least as much as local
        global_sent = max(global_sent, bytes_sent)
        global_received = max(global_received, bytes_received)
        
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
        # Merge local and global
        global_sent = max(global_sent, bytes_sent)
        global_received = max(global_received, bytes_received)
        
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


@router.get("/export")
async def export(format: str = Query("json", description="csv, json, html, or llm")):
    """Export all usage data in various formats."""
    
    if format == "csv":
        return await export_csv()
    elif format == "html":
        return await export_html()
    elif format == "llm":
        return await export_llm_friendly()
    else:
        # Enhanced JSON format
        return await export_json()


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
    
    # Get comprehensive data
    daily_data = storage.get_all_daily_aggregates()
    monthly_summaries = storage.get_monthly_summaries()
    total_sent, total_received = storage.get_lifetime_usage()
    overall_peak = storage.get_overall_peak_speed()
    tracking_stats = storage.get_tracking_stats()
    
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
    """Export beautiful HTML year wrap-up report."""
    from ..utils.formatters import format_bytes
    
    device_id, os_type, hostname = get_device_info()
    
    # Get comprehensive data
    daily_data = storage.get_all_daily_aggregates()
    monthly_summaries = storage.get_monthly_summaries()
    total_sent, total_received = storage.get_lifetime_usage()
    overall_peak = storage.get_overall_peak_speed()
    tracking_stats = storage.get_tracking_stats()
    
    # Calculate insights
    total_bytes = total_sent + total_received
    days_tracked = tracking_stats.get("total_days_tracked", 0) if tracking_stats else 0
    avg_daily = total_bytes / max(days_tracked, 1)
    
    # Find peak day
    peak_day = max(daily_data, key=lambda x: x["bytes_sent"] + x["bytes_received"]) if daily_data else None
    
    # Get current year data
    today = date.today()
    current_year = today.year
    year_data = [d for d in daily_data if d["date"].startswith(str(current_year))]
    year_sent = sum(d["bytes_sent"] for d in year_data)
    year_received = sum(d["bytes_received"] for d in year_data)
    year_total = year_sent + year_received
    
    # Generate beautiful HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PacketBuddy {current_year} Year Wrap-Up - {hostname}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .subtitle {{
            text-align: center;
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 40px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }}
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
            padding: 30px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
        }}
        .section h2 {{
            font-size: 2em;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }}
        .monthly-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .month-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
        }}
        .month-name {{
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        .month-stat {{
            font-size: 0.9em;
            margin: 5px 0;
            opacity: 0.95;
        }}
        .highlight {{
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            opacity: 0.8;
            font-size: 0.9em;
        }}
        .emoji {{
            font-size: 1.5em;
            margin-right: 10px;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 {current_year} Internet Wrap-Up</h1>
        <div class="subtitle">Your year in data - {hostname}</div>
        
        <div class="highlight">
            <h2 style="margin-bottom: 15px;">🎉 This Year's Total</h2>
            <div class="stat-value">{format_bytes(year_total)}</div>
            <p style="font-size: 1.1em; margin-top: 10px;">
                ↑ {format_bytes(year_sent)} uploaded • ↓ {format_bytes(year_received)} downloaded
            </p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label"><span class="emoji">📊</span>Total All-Time</div>
                <div class="stat-value">{format_bytes(total_bytes)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><span class="emoji">📅</span>Days Tracked</div>
                <div class="stat-value">{days_tracked}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><span class="emoji">⚡</span>Peak Speed</div>
                <div class="stat-value">{format_bytes(overall_peak)}/s</div>
            </div>
            <div class="stat-card">
                <div class="stat-label"><span class="emoji">📈</span>Daily Average</div>
                <div class="stat-value">{format_bytes(int(avg_daily))}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📆 Monthly Breakdown</h2>
            <div class="monthly-grid">
"""
    
    # Add monthly cards
    for month_data in monthly_summaries:
        month_name = datetime.strptime(month_data["month"] + "-01", "%Y-%m-%d").strftime("%B %Y")
        month_total = month_data["bytes_sent"] + month_data["bytes_received"]
        html_content += f"""
                <div class="month-card">
                    <div class="month-name">{month_name}</div>
                    <div class="month-stat">📦 {format_bytes(month_total)}</div>
                    <div class="month-stat">↑ {format_bytes(month_data["bytes_sent"])}</div>
                    <div class="month-stat">↓ {format_bytes(month_data["bytes_received"])}</div>
                    <div class="month-stat">⚡ {format_bytes(month_data["peak_speed"])}/s</div>
                </div>
"""
    
    html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Highlights</h2>
"""
    
    if peak_day:
        peak_day_date = datetime.strptime(peak_day["date"], "%Y-%m-%d").strftime("%B %d, %Y")
        peak_day_total = peak_day["bytes_sent"] + peak_day["bytes_received"]
        html_content += f"""
            <p style="font-size: 1.2em; margin: 15px 0;">
                <span class="emoji">🌟</span><strong>Most Active Day:</strong> {peak_day_date}
                <br><span style="margin-left: 50px;">{format_bytes(peak_day_total)} transferred</span>
            </p>
"""
    
    # Add upload/download ratio
    ratio = total_sent / max(total_received, 1)
    html_content += f"""
            <p style="font-size: 1.2em; margin: 15px 0;">
                <span class="emoji">⚖️</span><strong>Upload/Download Ratio:</strong> {ratio:.2f}:1
            </p>
            <p style="font-size: 1.2em; margin: 15px 0;">
                <span class="emoji">💾</span><strong>Storage Equivalent:</strong> 
                {int(total_bytes / (1024**3) / 4.7)} DVDs or {int(total_bytes / (1024**3) / 0.7)} CDs
            </p>
        </div>
        
        <div class="footer">
            <p>Generated by PacketBuddy v{get_fresh_version()} on {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}</p>
            <p style="margin-top: 10px;">Device: {hostname} ({os_type})</p>
        </div>
    </div>
</body>
</html>
"""
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=packetbuddy_wrap_up_{current_year}.html"
        }
    )


@router.get("/export/llm")
async def export_llm_friendly():
    """Export data in TOON format (Token Optimized Object Notation) for LLM analysis."""
    from ..utils.formatters import format_bytes
    
    device_id, os_type, hostname = get_device_info()
    
    # Get comprehensive data
    daily_data = storage.get_all_daily_aggregates()
    monthly_summaries = storage.get_monthly_summaries()
    total_sent, total_received = storage.get_lifetime_usage()
    overall_peak = storage.get_overall_peak_speed()
    tracking_stats = storage.get_tracking_stats()
    
    # Calculate insights
    total_bytes = total_sent + total_received
    days_tracked = tracking_stats.get("total_days_tracked", 0) if tracking_stats else 0
    avg_daily = total_bytes / max(days_tracked, 1)
    
    # Get current year data
    today = date.today()
    current_year = today.year
    year_data = [d for d in daily_data if d["date"].startswith(str(current_year))]
    year_sent = sum(d["bytes_sent"] for d in year_data)
    year_received = sum(d["bytes_received"] for d in year_data)
    year_total = year_sent + year_received
    
    # Find peak day
    peak_day = max(daily_data, key=lambda x: x["bytes_sent"] + x["bytes_received"]) if daily_data else None
    
    # Generate TOON format report (Token Optimized Object Notation)
    # ~60% fewer tokens than markdown while maintaining all data
    report = f"""# PacketBuddy Network Usage Export - TOON Format

[meta]
format = "TOON (Token Optimized Object Notation)"
generated = "{datetime.utcnow().isoformat()}"
device = "{hostname}"
os = "{os_type}"
device_id = "{device_id}"
version = "{get_fresh_version()}"

[tracking]
first_date = "{tracking_stats.get("first_tracked_date", "N/A")}"
last_date = "{tracking_stats.get("last_tracked_date", "N/A")}"
total_days = {days_tracked}

[totals]
bytes_sent = {total_sent}
bytes_received = {total_received}
total_bytes = {total_bytes}
human = {{sent="{format_bytes(total_sent)}", received="{format_bytes(total_received)}", total="{format_bytes(total_bytes)}"}}

[year_{current_year}]
bytes_sent = {year_sent}
bytes_received = {year_received}
total_bytes = {year_total}
days = {len(year_data)}
human = {{sent="{format_bytes(year_sent)}", received="{format_bytes(year_received)}", total="{format_bytes(year_total)}"}}

[records]
peak_speed_bps = {overall_peak}
peak_speed_human = "{format_bytes(overall_peak)}/s"
"""
    
    if peak_day:
        peak_day_total = peak_day["bytes_sent"] + peak_day["bytes_received"]
        report += f"""peak_day_date = "{peak_day["date"]}"
peak_day_bytes = {peak_day_total}
peak_day_human = "{format_bytes(peak_day_total)}"
peak_day_sent = {peak_day["bytes_sent"]}
peak_day_received = {peak_day["bytes_received"]}
peak_day_speed = {peak_day["peak_speed"]}
"""
    
    report += f"""
[averages]
daily_bytes = {int(avg_daily)}
daily_human = "{format_bytes(int(avg_daily))}"

[ratios]
upload_download = {(total_sent / max(total_received, 1)):.2f}
upload_percent = {(total_sent / max(total_bytes, 1) * 100):.1f}
download_percent = {(total_received / max(total_bytes, 1) * 100):.1f}

[comparisons]
dvd_equivalent = {int(total_bytes / (1024**3) / 4.7)}
cd_equivalent = {int(total_bytes / (1024**3) / 0.7)}
hd_movie_equivalent = {int(total_bytes / (1024**3) / 5)}

"""
    
    # Add monthly data in compact format
    report += "[monthly_data]\n"
    for i, month_data in enumerate(monthly_summaries):
        month_total = month_data["bytes_sent"] + month_data["bytes_received"]
        report += f"""month_{i} = {{name="{month_data["month"]}", sent={month_data["bytes_sent"]}, received={month_data["bytes_received"]}, total={month_total}, peak={month_data["peak_speed"]}, days={month_data["days_tracked"]}, human="{format_bytes(month_total)}"}}
"""
    
    # Add recent 30 days in compact format
    report += "\n[recent_30_days]\n"
    recent_data = [d for d in daily_data if datetime.strptime(d["date"], "%Y-%m-%d").date() >= today - timedelta(days=30)]
    for i, day in enumerate(sorted(recent_data, key=lambda x: x["date"], reverse=True)[:30]):
        day_total = day["bytes_sent"] + day["bytes_received"]
        report += f"""day_{i} = {{date="{day["date"]}", sent={day["bytes_sent"]}, received={day["bytes_received"]}, total={day_total}, peak={day["peak_speed"]}}}
"""
    
    # Add LLM analysis prompts
    report += f"""
[llm_prompts]
year_wrapup = "Create a fun, Spotify-style {current_year} wrap-up based on this network usage data. Include interesting insights, fun facts, and comparisons."
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
            "neon_log_days": config.storage.neon.neon_log_retention_days if hasattr(config.storage, 'neon') else 7,
            "neon_aggregate_months": config.storage.neon.neon_aggregate_retention_months if hasattr(config.storage, 'neon') else 3,
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
                "log_count": neon_stats.get("log_count", 0),
                "oldest_log": neon_stats.get("oldest_log"),
                "newest_log": neon_stats.get("newest_log"),
                "logs_per_device": neon_stats.get("logs_per_device", []),
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
            neon_log_days = neon_config.neon_log_retention_days if neon_config else 7
            neon_agg_months = neon_config.neon_aggregate_retention_months if neon_config else 3
            
            if aggressive:
                neon_results = await sync.aggressive_cleanup()
            else:
                neon_deleted = await sync.cleanup_old_logs(neon_log_days)
                neon_aggregates = await sync.cleanup_old_aggregates(neon_agg_months)
                neon_results = {
                    "logs_deleted": neon_deleted,
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

