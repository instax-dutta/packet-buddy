"""Spotify Wrapped-style HTML report generator."""

import logging
from datetime import datetime

from ..core.device import get_device_info
from ..utils.formatters import format_bytes, format_speed

logger = logging.getLogger(__name__)

SECTION_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  background: #0a0a1a;
  color: #e0e0e0;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  padding: 24px 16px;
  min-height: 100vh;
}
.wrapper { max-width: 720px; margin: 0 auto; }

/* Hero */
.hero {
  background: linear-gradient(135deg, #1a1a3e 0%, #0f3460 50%, #533483 100%);
  border-radius: 24px;
  padding: 48px 32px 40px;
  text-align: center;
  margin-bottom: 24px;
}
.hero .eyebrow { font-size: 14px; letter-spacing: 2px; text-transform: uppercase; color: #53d8fb; margin-bottom: 8px; }
.hero h1 { font-size: 28px; font-weight: 800; color: #fff; margin-bottom: 4px; }
.hero .hostname { font-size: 15px; color: rgba(255,255,255,0.6); margin-bottom: 24px; }
.hero .giant-number { font-size: 56px; font-weight: 900; color: #fff; line-height: 1.1; margin-bottom: 8px; }
.hero .date-range { font-size: 13px; color: rgba(255,255,255,0.5); margin-bottom: 20px; }
.hero .breakdown {
  display: flex; justify-content: center; gap: 32px; font-size: 14px;
}
.hero .breakdown .label { color: rgba(255,255,255,0.5); }
.hero .breakdown .up { color: #53d8fb; font-weight: 700; }
.hero .breakdown .down { color: #e94560; font-weight: 700; }

/* Card base */
.card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.06);
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 16px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.06);
}
.stat-card .stat-value { font-size: 24px; font-weight: 800; color: #fff; line-height: 1.2; }
.stat-card .stat-label { font-size: 12px; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

/* Personality */
.personality-card {
  background: linear-gradient(135deg, #1a1a3e, #533483);
  border-radius: 16px;
  padding: 28px 24px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.06);
}
.personality-card .icon { font-size: 48px; margin-bottom: 8px; }
.personality-card .type { font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.personality-card .desc { font-size: 14px; color: rgba(255,255,255,0.7); line-height: 1.5; }

/* Section title */
.section-title {
  font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 16px;
}

/* Month bars */
.month-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.month-label { width: 56px; font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.7); flex-shrink: 0; text-align: right; }
.month-bar-track { flex: 1; height: 24px; background: rgba(255,255,255,0.06); border-radius: 6px; overflow: hidden; }
.month-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #53d8fb, #e94560);
  border-radius: 6px;
  transition: width 0.4s ease;
  min-width: 4px;
}
.month-value { width: 80px; font-size: 12px; color: rgba(255,255,255,0.5); text-align: left; flex-shrink: 0; }

/* Peak day highlight */
.peak-day-box {
  background: rgba(83, 216, 251, 0.08);
  border: 1px solid rgba(83, 216, 251, 0.2);
  border-radius: 10px;
  padding: 14px 16px;
  margin-top: 12px;
}
.peak-day-box .label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #53d8fb; margin-bottom: 4px; }
.peak-day-box .value { font-size: 15px; font-weight: 700; color: #fff; }

/* Fun facts grid */
.fun-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.fun-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 16px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.06);
}
.fun-card .fun-emoji { font-size: 32px; margin-bottom: 6px; }
.fun-card .fun-value { font-size: 22px; font-weight: 800; color: #fff; line-height: 1.2; }
.fun-card .fun-label { font-size: 12px; color: rgba(255,255,255,0.45); margin-top: 2px; }

/* Footer */
.footer {
  text-align: center;
  padding: 24px;
  font-size: 12px;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.5px;
}

@media (max-width: 480px) {
  .hero { padding: 32px 20px 28px; }
  .hero h1 { font-size: 22px; }
  .hero .giant-number { font-size: 40px; }
  .hero .breakdown { gap: 16px; font-size: 13px; flex-wrap: wrap; }
  .stats-grid { gap: 8px; }
  .stat-card .stat-value { font-size: 20px; }
  .fun-grid { gap: 8px; }
  .fun-card .fun-value { font-size: 18px; }
  .month-value { display: none; }
}
"""


def _period_label(start_date: str, end_date: str, days_tracked: int) -> str:
    if start_date == end_date:
        return "Day"
    if start_date and start_date.endswith("-01-01") and days_tracked > 300:
        return "Year"
    if start_date and start_date.endswith("-01") and days_tracked <= 31:
        return "Month"
    if days_tracked <= 7:
        return "Week"
    return "Period"


def _month_bars(breakdown: list) -> str:
    if not breakdown:
        return ""
    max_total = max(m["total_bytes"] for m in breakdown)
    rows = []
    for m in breakdown:
        pct = (m["total_bytes"] / max_total * 100) if max_total > 0 else 0
        rows.append(
            f"""        <div class="month-row">
          <span class="month-label">{m["month"]}</span>
          <div class="month-bar-track">
            <div class="month-bar-fill" style="width: {pct:.1f}%"></div>
          </div>
          <span class="month-value">{format_bytes(m["total_bytes"])}</span>
        </div>"""
        )
    return "\n".join(rows)


def _peak_day_html(data: dict) -> str:
    peak_day = data.get("peak_day")
    peak_speed = data.get("peak_speed", 0)
    if not peak_day:
        return ""
    speed_str = format_speed(peak_speed) if peak_speed else ""
    return (
        f'        <div class="peak-day-box">\n'
        f'          <div class="label">Peak Day</div>\n'
        f'          <div class="value">{peak_day}{" &middot; " + speed_str if speed_str else ""}</div>\n'
        f'        </div>'
    )


def generate_html_report(data: dict) -> str:
    _device_id, _os_type, hostname = get_device_info()
    start = data.get("start_date", "")
    end = data.get("end_date", "")
    days = data.get("days_tracked", 0)
    label = _period_label(start, end, days)

    total = data.get("total_bytes", 0)
    sent = data.get("total_sent", 0)
    received = data.get("total_received", 0)
    daily_avg = data.get("daily_avg", 0)
    peak_speed = data.get("peak_speed", 0)

    personality = data.get("personality", {})
    comparisons = data.get("fun_comparisons", {})
    breakdown = data.get("monthly_breakdown", [])

    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    month_section = ""
    if breakdown:
        month_section = (
            f'    <div class="card">\n'
            f'      <div class="section-title">Monthly Breakdown</div>\n'
            f'{_month_bars(breakdown)}\n'
            f'{_peak_day_html(data)}\n'
            f'    </div>'
        )

    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        f'  <title>Your {label} in Internet &mdash; PacketBuddy</title>\n'
        f'  <style>{SECTION_CSS}</style>\n'
        '</head>\n'
        '<body>\n'
        '  <div class="wrapper">\n'
        '\n'
        '    <!-- Hero -->\n'
        '    <div class="hero">\n'
        f'      <div class="eyebrow">Your {label} in Internet</div>\n'
        f'      <h1>{hostname}</h1>\n'
        f'      <div class="hostname">{start} &mdash; {end}</div>\n'
        f'      <div class="giant-number">{format_bytes(total)}</div>\n'
        f'      <div class="date-range">total data transferred</div>\n'
        f'      <div class="breakdown">\n'
        f'        <div><span class="label">Upload </span><span class="up">{format_bytes(sent)}</span></div>\n'
        f'        <div><span class="label">Download </span><span class="down">{format_bytes(received)}</span></div>\n'
        f'      </div>\n'
        '    </div>\n'
        '\n'
        '    <!-- Personality -->\n'
        f'    <div class="personality-card">\n'
        f'      <div class="icon">{personality.get("icon", "")}</div>\n'
        f'      <div class="type">{personality.get("type", "User")}</div>\n'
        f'      <div class="desc">{personality.get("desc", "")}</div>\n'
        '    </div>\n'
        '\n'
        '    <!-- Stats Grid -->\n'
        '    <div class="stats-grid">\n'
        f'      <div class="stat-card"><div class="stat-value">{format_bytes(total)}</div><div class="stat-label">Total Data</div></div>\n'
        f'      <div class="stat-card"><div class="stat-value">{days}</div><div class="stat-label">Days Tracked</div></div>\n'
        f'      <div class="stat-card"><div class="stat-value">{format_speed(peak_speed)}</div><div class="stat-label">Peak Speed</div></div>\n'
        f'      <div class="stat-card"><div class="stat-value">{format_bytes(daily_avg)}</div><div class="stat-label">Daily Average</div></div>\n'
        '    </div>\n'
        '\n'
        '    <!-- Monthly Breakdown -->\n'
        f'{month_section}\n'
        '\n'
        '    <!-- Fun Comparisons -->\n'
        '    <div class="card">\n'
        '      <div class="section-title">Fun Facts</div>\n'
        '      <div class="fun-grid">\n'
        f'        <div class="fun-card"><div class="fun-emoji">&#x1F4BF;</div><div class="fun-value">{comparisons.get("dvd_equivalent", 0)}</div><div class="fun-label">DVDs Worth</div></div>\n'
        f'        <div class="fun-card"><div class="fun-emoji">&#x1F3AC;</div><div class="fun-value">{comparisons.get("hd_movies", 0)}</div><div class="fun-label">HD Movies</div></div>\n'
        f'        <div class="fun-card"><div class="fun-emoji">&#x1F310;</div><div class="fun-value">{comparisons.get("web_pages", 0):,}</div><div class="fun-label">Web Pages</div></div>\n'
        f'        <div class="fun-card"><div class="fun-emoji">&#x2615;</div><div class="fun-value">{comparisons.get("coffee_cups", 0)}</div><div class="fun-label">Cups of Coffee</div></div>\n'
        '      </div>\n'
        '    </div>\n'
        '\n'
        '    <!-- Footer -->\n'
        '    <div class="footer">\n'
        f'      Generated by PacketBuddy &mdash; {now}\n'
        '    </div>\n'
        '\n'
        '  </div>\n'
        '</body>\n'
        '</html>'
    )
