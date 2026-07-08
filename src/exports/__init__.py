"""Export rewind system API routes."""

import logging

from datetime import date as date_type

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from .data_provider import compute_export_data
from .html_report import generate_html_report
from .markdown_report import generate_markdown_report

logger = logging.getLogger(__name__)

export_router = APIRouter(prefix="/api/exports")


@export_router.get("/generate")
async def generate_export(
    range_type: str = Query("all", description="today, week, month, year, all, custom"),
    format: str = Query("html", description="html or markdown"),
    start_date: str = Query(None, description="YYYY-MM-DD for custom range"),
    end_date: str = Query(None, description="YYYY-MM-DD for custom range"),
):
    try:
        start = date_type.fromisoformat(start_date) if start_date else None
        end = date_type.fromisoformat(end_date) if end_date else None

        data = compute_export_data(
            range_type=range_type,
            start_date=start,
            end_date=end,
        )

        if data.get("total_bytes", 0) == 0:
            return HTMLResponse(status_code=204)

        if format == "markdown":
            content = generate_markdown_report(data)
            return PlainTextResponse(
                content=content,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=packetbuddy_report_{data.get('start_date', 'export')}.md"
                },
            )

        content = generate_html_report(data)
        return HTMLResponse(
            content=content,
            headers={
                "Content-Disposition": f"attachment; filename=packetbuddy_report_{data.get('start_date', 'export')}.html"
            },
        )
    except Exception as e:
        logger.exception("Failed to generate export")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate export", "detail": str(e)},
        )
