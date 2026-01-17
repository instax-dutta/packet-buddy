"""FastAPI server with CORS and static file serving."""

import asyncio
import signal
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from ..utils.config import config
from ..core.monitor import monitor
from ..core.sync import sync
from ..utils.updater import auto_update_check
from .routes import router


# Create FastAPI app
app = FastAPI(
    title="PacketBuddy API",
    description="Ultra-lightweight network usage tracking",
    version="1.3.0"
)

# Enable CORS
if config.get("api", "cors_enabled", default=True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(router)

# Serve dashboard static files
dashboard_path = Path(__file__).parent.parent.parent / "dashboard"
if dashboard_path.exists():
    app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")


@app.get("/")
async def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard/")


# Background tasks
background_tasks = set()


async def run_background_services():
    """Run monitor and sync services in background."""
    tasks = [
        asyncio.create_task(monitor.start()),
    ]
    
    # Only start sync if enabled
    if config.sync_enabled:
        tasks.append(asyncio.create_task(sync.start()))
    
    # Keep references to prevent garbage collection
    for task in tasks:
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    
    # Run automatic update check in the background periodically
    async def periodic_update_check():
        # Check if auto-update is enabled in config
        auto_update_enabled = config.get("auto_update", "enabled", default=True)
        check_on_startup = config.get("auto_update", "check_on_startup", default=True)
        auto_apply = config.get("auto_update", "auto_apply", default=True)
        auto_restart = config.get("auto_update", "auto_restart", default=True)
        check_interval_hours = config.get("auto_update", "check_interval_hours", default=6)
        
        if not auto_update_enabled:
            print("ℹ️  Automatic updates disabled in config")
            return
        
        # Initial check on startup (after settling period)
        if check_on_startup:
            await asyncio.sleep(10)  # Wait for system to settle
            try:
                print("🔍 Checking for updates on startup...")
                auto_update_check(force_restart=auto_restart, auto_apply=auto_apply)
            except Exception as e:
                print(f"Startup update check failed: {e}")
        
        # Periodic update checks (every N hours)
        check_interval_seconds = check_interval_hours * 3600
        while True:
            await asyncio.sleep(check_interval_seconds)
            try:
                print(f"🔍 Periodic update check (every {check_interval_hours}h)...")
                auto_update_check(force_restart=auto_restart, auto_apply=auto_apply)
            except Exception as e:
                print(f"Periodic update check failed: {e}")

    update_task = asyncio.create_task(periodic_update_check())
    background_tasks.add(update_task)
    update_task.add_done_callback(background_tasks.discard)

    await asyncio.gather(*tasks, return_exceptions=True)


@app.on_event("startup")
async def startup_event():
    """Start background services on server startup."""
    asyncio.create_task(run_background_services())


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown."""
    print("\nShutting down gracefully...")
    
    # Stop monitor and sync
    await monitor.stop()
    
    if config.sync_enabled:
        await sync.stop()
    
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
    
    print("Shutdown complete.")


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    
    host = config.get("api", "host", default="127.0.0.1")
    port = config.get("api", "port", default=7373)
    
    print(f"Starting PacketBuddy API server on http://{host}:{port}")
    print(f"Dashboard: http://{host}:{port}/dashboard")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # Reduce noise
    )


if __name__ == "__main__":
    run_server()
