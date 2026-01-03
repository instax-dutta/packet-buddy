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
from ..core.device import get_device_info
from ..utils.formatters import format_usage_response
from ..utils.cost_calculator import get_cost_breakdown, DEFAULT_COST_PER_GB_INR


router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    """Service health check."""
    device_id, os_type, hostname = get_device_info()
    
    # Calculate uptime (simplified for now)
    return {
        "status": "running",
        "device_id": device_id,
        "os_type": os_type,
        "hostname": hostname,
        "timestamp": datetime.utcnow().isoformat()
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
    bytes_sent, bytes_received = storage.get_today_usage()
    
    response = format_usage_response(bytes_sent, bytes_received)
    # Add cost information
    cost_data = get_cost_breakdown(bytes_sent, bytes_received)
    response["cost"] = cost_data
    
    return response


@router.get("/cost")
async def cost(cost_per_gb: float = Query(DEFAULT_COST_PER_GB_INR, description="Cost per GB in INR")):
    """
    Calculate cost for today's usage.
    
    Default: ₹7.50 per GB (average Indian mobile data cost)
    """
    bytes_sent, bytes_received = storage.get_today_usage()
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
async def export(format: str = Query("json", description="csv, json, or llm")):
    """Export all usage data."""
    logs = storage.get_all_usage_logs()
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp", "bytes_sent", "bytes_received"])
        writer.writeheader()
        writer.writerows(logs)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=packetbuddy_export.csv"}
        )
    
    elif format == "llm":
        # LLM-friendly markdown format with insights
        return await export_llm_friendly()
    
    else:
        # JSON format
        return JSONResponse(content={"logs": logs})


@router.get("/export/llm")
async def export_llm_friendly():
    """Export data in LLM-friendly format for year wrap-ups and analysis."""
    from ..utils.formatters import format_bytes
    
    device_id, os_type, hostname = get_device_info()
    
    # Get all-time stats
    total_sent, total_received = storage.get_lifetime_usage()
    total_bytes = total_sent + total_received
    
    # Get daily data for analysis
    today = date.today()
    year_start = date(today.year, 1, 1)
    year_data = storage.get_range_usage(year_start, today)
    
    # Calculate insights
    days_tracked = len(year_data) if year_data else 0
    avg_daily = total_bytes / max(days_tracked, 1)
    
    # Find peak day
    peak_day = {"date": "N/A", "total": 0}
    monthly_totals = {}
    
    for day in year_data:
        day_total = day["bytes_sent"] + day["bytes_received"]
        if day_total > peak_day["total"]:
            peak_day = {"date": day["date"], "total": day_total, "sent": day["bytes_sent"], "received": day["bytes_received"]}
        
        month = day["date"][:7]  # YYYY-MM
        if month not in monthly_totals:
            monthly_totals[month] = {"sent": 0, "received": 0}
        monthly_totals[month]["sent"] += day["bytes_sent"]
        monthly_totals[month]["received"] += day["bytes_received"]
    
    # Generate markdown report
    report = f"""# 🌐 PacketBuddy Network Usage Report

## 📊 Report Summary

**Generated:** {datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")}  
**Device:** {hostname} ({os_type})  
**Device ID:** {device_id}  
**Tracking Period:** {year_start.strftime("%B %d, %Y")} - {today.strftime("%B %d, %Y")}  
**Days Tracked:** {days_tracked} days

---

## 🎯 Quick Stats

| Metric | Value |
|--------|-------|
| Total Upload | {format_bytes(total_sent)} |
| Total Download | {format_bytes(total_received)} |
| **Grand Total** | **{format_bytes(total_bytes)}** |
| Average Daily Usage | {format_bytes(int(avg_daily))} |
| Upload/Download Ratio | {(total_sent / max(total_received, 1)):.2f}:1 |

---

## 📈 Detailed Insights

### Usage Patterns

- **Most Active Day:** {peak_day['date']}
  - Uploaded: {format_bytes(peak_day['sent'])}
  - Downloaded: {format_bytes(peak_day['received'])}
  - Total: {format_bytes(peak_day['total'])}

- **Average Daily Breakdown:**
  - Upload: {format_bytes(int(total_sent / max(days_tracked, 1)))}
  - Download: {format_bytes(int(total_received / max(days_tracked, 1)))}

### Monthly Breakdown

"""
    
    # Add monthly data
    for month in sorted(monthly_totals.keys(), reverse=True):
        data = monthly_totals[month]
        month_total = data["sent"] + data["received"]
        month_name = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%B %Y")
        
        report += f"""#### {month_name}
- Upload: {format_bytes(data['sent'])}
- Download: {format_bytes(data['received'])}
- Total: {format_bytes(month_total)}

"""
    
    # Add daily data section
    report += """---

## 📅 Daily Usage Data

### Last 30 Days

"""
    
    # Get last 30 days
    recent_data = [d for d in year_data if datetime.strptime(d["date"], "%Y-%m-%d").date() >= today - timedelta(days=30)]
    
    for day in sorted(recent_data, key=lambda x: x["date"], reverse=True)[:30]:
        day_total = day["bytes_sent"] + day["bytes_received"]
        report += f"- **{day['date']}**: {format_bytes(day_total)} (↑ {format_bytes(day['bytes_sent'])}, ↓ {format_bytes(day['bytes_received'])})\n"
    
    # Add context for LLMs
    report += f"""

---

## 🤖 Analysis Context

### Data Summary for LLM Processing

This report contains network usage data from **{hostname}** running **{os_type}**. The data spans **{days_tracked} days** from {year_start.strftime("%B %d, %Y")} to {today.strftime("%B %d, %Y")}.

### Key Metrics for Analysis:
- **Total data transferred**: {format_bytes(total_bytes)} ({total_bytes} bytes)
- **Upload percentage**: {(total_sent / max(total_bytes, 1) * 100):.1f}%
- **Download percentage**: {(total_received / max(total_bytes, 1) * 100):.1f}%
- **Consistency**: {days_tracked} days of continuous tracking

### Suggested Analysis Questions:
1. What are my internet usage patterns throughout the year?
2. Which months had the highest/lowest usage?
3. What is my average daily data consumption?
4. How does my upload vs download ratio compare to typical users?
5. Are there any unusual spikes in usage that might indicate specific activities?

### Data Interpretation Notes:
- 1 GB = 1,073,741,824 bytes
- Upload = Data sent from this device to the internet
- Download = Data received from the internet to this device
- Total = Upload + Download

---

## 📊 Raw Data for Custom Analysis

### JSON Summary

```json
{{
  "device": {{
    "hostname": "{hostname}",
    "os_type": "{os_type}",
    "device_id": "{device_id}"
  }},
  "period": {{
    "start": "{year_start.isoformat()}",
    "end": "{today.isoformat()}",
    "days_tracked": {days_tracked}
  }},
  "totals": {{
    "bytes_sent": {total_sent},
    "bytes_received": {total_received},
    "total_bytes": {total_bytes},
    "human_readable": {{
      "sent": "{format_bytes(total_sent)}",
      "received": "{format_bytes(total_received)}",
      "total": "{format_bytes(total_bytes)}"
    }}
  }},
  "averages": {{
    "daily_bytes": {int(avg_daily)},
    "daily_human": "{format_bytes(int(avg_daily))}"
  }},
  "peak_day": {{
    "date": "{peak_day['date']}",
    "bytes": {peak_day['total']},
    "human": "{format_bytes(peak_day['total'])}"
  }}
}}
```

---

## 💡 Tips for Year Wrap-Up Creation

When creating a year wrap-up with an LLM (ChatGPT, Claude, etc.), try these prompts:

1. **Spotify-Style Wrap:**
   > "Create a fun, Spotify-style year wrap-up based on this network usage data. Include interesting insights, fun facts, and comparisons."

2. **Professional Summary:**
   > "Generate a professional network usage summary I can share with my IT team, highlighting efficiency and patterns."

3. **Personal Insights:**
   > "Analyze my internet usage patterns and give me insights about my digital life. What does this data say about my work/life balance?"

4. **Comparison Analysis:**
   > "Compare my internet usage to typical user averages and give me insights on whether I'm a heavy or light user."

---

**Generated by PacketBuddy v1.0.0**  
*Ultra-lightweight network usage tracker*

"""
    
    return Response(
        content=report,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=packetbuddy_report_{today.strftime('%Y%m%d')}.md"
        }
    )
