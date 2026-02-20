"""FastAPI server with CORS and static file serving."""

import asyncio
import signal
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from ..utils.config import config
from ..core.monitor import monitor
from ..core.sync import sync
from ..core.storage import storage
from ..utils.updater import auto_update_check
from .routes import router


# Create FastAPI app
app = FastAPI(
    title="PacketBuddy API",
    description="Ultra-lightweight network usage tracking",
    version="1.4.3"
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


async def periodic_cleanup():
    """Periodic cleanup task for old data."""
    storage_cfg = getattr(config, 'storage', None)
    cleanup_interval_hours = getattr(storage_cfg, 'cleanup_interval_hours', 24) if storage_cfg else 24
    log_retention_days = getattr(storage_cfg, 'log_retention_days', 30) if storage_cfg else 30
    aggregate_retention_months = getattr(storage_cfg, 'aggregate_retention_months', 12) if storage_cfg else 12
    vacuum_after_cleanup = getattr(storage_cfg, 'vacuum_after_cleanup', True) if storage_cfg else True
    max_storage_mb = getattr(storage_cfg, 'max_storage_mb', 400) if storage_cfg else 400
    
    neon_cfg = getattr(storage_cfg, 'neon', None) if storage_cfg else None
    neon_log_retention_days = getattr(neon_cfg, 'neon_log_retention_days', 7) if neon_cfg else 7
    neon_aggregate_retention_months = getattr(neon_cfg, 'neon_aggregate_retention_months', 3) if neon_cfg else 3
    
    cleanup_interval_seconds = cleanup_interval_hours * 3600
    
    await asyncio.sleep(60)
    
    while True:
        try:
            print(f"🧹 Running periodic cleanup (interval: {cleanup_interval_hours}h)...")
            cleanup_results = {
                'synced_logs_deleted': 0,
                'daily_aggregates_deleted': 0,
                'monthly_aggregates_deleted': 0,
                'neon_logs_deleted': 0,
                'neon_daily_deleted': 0,
                'neon_monthly_deleted': 0,
                'vacuum_run': False,
                'storage_warning': None,
                'neon_storage_before_percent': None,
                'neon_storage_after_percent': None,
                'neon_vacuum_run': False,
                'aggressive_cleanup_triggered': False
            }
            
            try:
                deleted_logs = storage.cleanup_synced_logs(days_to_keep=log_retention_days)
                cleanup_results['synced_logs_deleted'] = deleted_logs
                print(f"  Local: Deleted {deleted_logs} synced logs older than {log_retention_days} days")
            except Exception as e:
                print(f"  Local log cleanup failed: {e}")
            
            try:
                aggregates_result = storage.cleanup_old_aggregates(months_to_keep=aggregate_retention_months)
                cleanup_results['daily_aggregates_deleted'] = aggregates_result.get('daily', 0)
                cleanup_results['monthly_aggregates_deleted'] = aggregates_result.get('monthly', 0)
                print(f"  Local: Deleted {aggregates_result.get('daily', 0)} daily, {aggregates_result.get('monthly', 0)} monthly aggregates")
            except Exception as e:
                print(f"  Local aggregates cleanup failed: {e}")
            
            if vacuum_after_cleanup:
                try:
                    storage.vacuum_database()
                    cleanup_results['vacuum_run'] = True
                    print("  Local: Database vacuum completed")
                except Exception as e:
                    print(f"  Database vacuum failed: {e}")
            
            if config.sync_enabled:
                try:
                    neon_storage_before = await sync.get_storage_usage_percent()
                    cleanup_results['neon_storage_before_percent'] = neon_storage_before
                    print(f"  NeonDB: Storage usage before cleanup: {neon_storage_before:.1f}%")
                    
                    if neon_storage_before > 80:
                        print(f"  NeonDB: ⚠️ Storage crisis detected ({neon_storage_before:.1f}% > 80%), running aggressive cleanup...")
                        cleanup_results['aggressive_cleanup_triggered'] = True
                        try:
                            aggressive_result = await sync.aggressive_cleanup()
                            print(f"  NeonDB: Aggressive cleanup deleted {aggressive_result.get('logs_deleted', 0)} logs, {aggressive_result.get('aggregates_deleted', 0)} aggregates")
                        except Exception as e:
                            print(f"  NeonDB: Aggressive cleanup failed: {e}")
                except Exception as e:
                    print(f"  NeonDB: Failed to check storage usage: {e}")
                
                try:
                    neon_logs_deleted = await sync.cleanup_old_logs(days_to_keep=neon_log_retention_days)
                    cleanup_results['neon_logs_deleted'] = neon_logs_deleted
                    print(f"  NeonDB: Deleted {neon_logs_deleted} old logs (retention: {neon_log_retention_days} days)")
                except Exception as e:
                    print(f"  NeonDB log cleanup failed: {e}")
                
                try:
                    neon_aggregates = await sync.cleanup_old_aggregates(months_to_keep=neon_aggregate_retention_months)
                    cleanup_results['neon_daily_deleted'] = neon_aggregates.get('daily_deleted', 0)
                    cleanup_results['neon_monthly_deleted'] = neon_aggregates.get('monthly_deleted', 0)
                    print(f"  NeonDB: Deleted {neon_aggregates.get('daily_deleted', 0)} daily, {neon_aggregates.get('monthly_deleted', 0)} monthly aggregates (retention: {neon_aggregate_retention_months} months)")
                except Exception as e:
                    print(f"  NeonDB aggregates cleanup failed: {e}")
                
                try:
                    await sync.vacuum_database()
                    cleanup_results['neon_vacuum_run'] = True
                    print("  NeonDB: Database vacuum completed")
                except Exception as e:
                    print(f"  NeonDB vacuum failed: {e}")
                
                try:
                    neon_storage_after = await sync.get_storage_usage_percent()
                    cleanup_results['neon_storage_after_percent'] = neon_storage_after
                    print(f"  NeonDB: Storage usage after cleanup: {neon_storage_after:.1f}%")
                except Exception as e:
                    print(f"  NeonDB: Failed to check storage usage after cleanup: {e}")
            
            try:
                db_stats = storage.get_database_stats()
                db_size_mb = db_stats.get('db_size_mb', 0)
                if db_size_mb > max_storage_mb:
                    cleanup_results['storage_warning'] = f"Database size ({db_size_mb}MB) exceeds limit ({max_storage_mb}MB)"
                    print(f"  ⚠️  Storage warning: {db_size_mb}MB exceeds {max_storage_mb}MB limit")
            except Exception as e:
                print(f"  Storage stats check failed: {e}")
            
            print("✅ Periodic cleanup completed")
            
        except Exception as e:
            print(f"Periodic cleanup failed (will retry): {e}")
        
        await asyncio.sleep(cleanup_interval_seconds)


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

    cleanup_task = asyncio.create_task(periodic_cleanup())
    background_tasks.add(cleanup_task)
    cleanup_task.add_done_callback(background_tasks.discard)

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
