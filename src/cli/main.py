"""CLI interface for PacketBuddy."""

import platform
import click
from datetime import datetime
from tabulate import tabulate

IS_WINDOWS = platform.system() == 'Windows'
TABLE_FMT = "grid" if IS_WINDOWS else "fancy_grid"


def safe_emoji(emoji: str, fallback: str) -> str:
    """Return emoji on Unix, ASCII fallback on Windows."""
    return fallback if IS_WINDOWS else emoji


E_STATS = safe_emoji("📊", "[Stats]")
E_ERROR = safe_emoji("❌", "[X]")
E_OK = safe_emoji("✅", "[OK]")
E_WARN = safe_emoji("⚠", "!")
E_ROCKET = safe_emoji("🚀", "->")
E_INFO = safe_emoji("ℹ", "i")
E_SEARCH = safe_emoji("🔍", "?")
E_PACKAGE = safe_emoji("📦", "*")
E_RECYCLE = safe_emoji("♻", "~")
E_BULB = safe_emoji("💡", "*")
E_CHECK = safe_emoji("✓", "+")
E_CALENDAR = safe_emoji("📅", "")
E_CHART = safe_emoji("📈", "")
E_GLOBE = safe_emoji("🌐", "")
E_TRASH = safe_emoji("🧹", "")
E_HAMMER = safe_emoji("🔧", "")
E_STOP = safe_emoji("🛑", "")
E_HOURGLASS = safe_emoji("⏳", "...")
E_PARTY = safe_emoji("🎉", "!")
E_REFRESH = safe_emoji("🔄", "~")


import asyncio

from ..core.storage import storage as db
from ..utils.formatters import format_bytes, format_speed
from ..core.monitor import monitor
from ..api.server import run_server
from ..utils.config import config
from ..core.sync import sync


@click.group()
def cli():
    """PacketBuddy - Ultra-lightweight network usage tracker."""
    pass


@cli.command()
def live():
    """Show current upload/download speed."""
    speed_sent, speed_received = monitor.get_current_speed()
    
    table = [
        ["Upload Speed", format_speed(speed_sent)],
        ["Download Speed", format_speed(speed_received)],
        ["Total Speed", format_speed(speed_sent + speed_received)],
    ]
    
    click.echo("\n" + tabulate(table, headers=["Metric", "Value"], tablefmt=TABLE_FMT))


@cli.command()
def today():
    """Show today's usage."""
    bytes_sent, bytes_received, peak_speed = db.get_today_usage()
    total = bytes_sent + bytes_received
    
    table = [
        ["Uploaded", format_bytes(bytes_sent)],
        ["Downloaded", format_bytes(bytes_received)],
        ["Total", format_bytes(total)],
    ]
    
    click.echo(f"\n{E_STATS} Today's Usage\n")
    click.echo(tabulate(table, headers=["Type", "Amount"], tablefmt=TABLE_FMT))


@cli.command()
@click.argument("month", required=False)
def month(month: str = None):
    """Show monthly usage breakdown."""
    if month is None:
        month = datetime.utcnow().strftime("%Y-%m")
    
    daily_data = db.get_month_usage(month)
    
    if not daily_data:
        click.echo(f"\n{E_ERROR} No data for {month}")
        return
    
    table = []
    total_sent = 0
    total_received = 0
    
    for row in daily_data:
        sent = row["bytes_sent"]
        received = row["bytes_received"]
        total_sent += sent
        total_received += received
        
        table.append([
            row["date"],
            format_bytes(sent),
            format_bytes(received),
            format_bytes(sent + received)
        ])
    
    click.echo(f"\n{E_CALENDAR} Usage for {month}\n")
    click.echo(tabulate(table, headers=["Date", "Uploaded", "Downloaded", "Total"], tablefmt=TABLE_FMT))
    
    click.echo(f"\n{E_CHART} Month Summary:")
    click.echo(f"   Total Uploaded: {format_bytes(total_sent)}")
    click.echo(f"   Total Downloaded: {format_bytes(total_received)}")
    click.echo(f"   Total: {format_bytes(total_sent + total_received)}\n")


@cli.command()
def summary():
    """Show lifetime usage summary."""
    bytes_sent, bytes_received = db.get_lifetime_usage()
    total = bytes_sent + bytes_received
    
    table = [
        ["Total Uploaded", format_bytes(bytes_sent)],
        ["Total Downloaded", format_bytes(bytes_received)],
        ["Grand Total", format_bytes(total)],
    ]
    
    click.echo(f"\n{E_GLOBE} Lifetime Usage Summary\n")
    click.echo(tabulate(table, headers=["Metric", "Amount"], tablefmt=TABLE_FMT))


@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.option("--output", type=click.Path(), help="Output file path")
def export(format: str, output: str = None):
    """Export all usage data."""
    import json
    import csv
    
    logs = db.get_all_usage_logs()
    
    if not logs:
        click.echo(f"{E_ERROR} No data to export")
        return
    
    if output is None:
        output = f"packetbuddy_export.{format}"
    
    if format == "json":
        with open(output, "w") as f:
            json.dump({"logs": logs}, f, indent=2, default=str)
    
    else:  # CSV
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "bytes_sent", "bytes_received"])
            writer.writeheader()
            writer.writerows(logs)
    
    click.echo(f"{E_OK} Exported {len(logs)} records to {output}")


@cli.command()
def serve():
    """Start the API server and dashboard."""
    run_server()


@cli.command()
@click.option("--check-only", is_flag=True, help="Only check for updates, don't apply")
@click.option("--force", is_flag=True, help="Force update even if already up to date")
def update(check_only: bool, force: bool):
    """Check for and apply updates from GitHub.
    
    Note: PacketBuddy automatically updates in the background.
    Use this command to force an immediate update or check status.
    """
    from ..utils.updater import check_for_updates, perform_update, restart_service
    
    click.echo(f"\n{E_SEARCH} Checking for updates...")
    click.echo(f"{E_INFO}  PacketBuddy automatically updates in the background")
    click.echo("   This command is for manual/force updates\n")
    
    has_update, current, latest = check_for_updates()
    
    if not has_update and not force:
        if current and latest:
            click.echo(f"{E_OK} You're already on the latest version ({current[:7]})")
            click.echo(f"\n{E_BULB} Tip: Updates are applied automatically when available")
        else:
            click.echo(f"{E_INFO}  Auto-update not available (not a git repository)")
        return
    
    if force and not has_update:
        click.echo(f"{E_WARN}  Forcing update even though you're on latest version ({current[:7]})")
    else:
        click.echo(f"\n{E_PACKAGE} Update available!")
        click.echo(f"   Current: {current[:7]}")
        click.echo(f"   Latest:  {latest[:7]}")
    
    if check_only:
        click.echo(f"\n{E_INFO}  Run 'pb update' to apply the update immediately")
        click.echo("   (or wait for automatic update in background)")
        return
    
    if click.confirm(f"\n{E_ROCKET} Apply update now?", default=True):
        click.echo(f"\n{E_HOURGLASS} Updating...")
        
        if perform_update():
            click.echo(f"{E_OK} Update completed successfully!")
            click.echo(f"{E_HAMMER} PATH has been updated to the current installation")
            click.echo(f"\n{E_INFO}  Your data is safe - nothing was deleted")
            
            if click.confirm(f"\n{E_REFRESH} Restart service now?", default=True):
                click.echo(f"{E_RECYCLE}  Restarting service...")
                restart_service()
                click.echo(f"{E_OK} Service restarted!")
                click.echo(f"\n{E_PARTY} All done! PacketBuddy is now up to date.\n")
            else:
                click.echo(f"\n{E_INFO}  Please restart the service manually:")
                click.echo("   macOS: launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon")
                click.echo("   Windows: schtasks /run /tn PacketBuddy")
                click.echo("   Linux: systemctl --user restart packetbuddy.service\n")
        else:
            click.echo(f"{E_ERROR} Update failed. Check logs for details.\n")


@cli.group()
def storage():
    """Database storage management commands."""
    pass


@storage.command(name="cleanup")
@click.option("--days", default=None, help="Days to keep synced logs (default from config)")
@click.option("--vacuum/--no-vacuum", default=None, help="Run VACUUM after cleanup")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
@click.option("--neon", is_flag=True, help="Cleanup NeonDB remote storage")
@click.option("--aggressive", is_flag=True, help="Aggressive cleanup for storage crisis")
def storage_cleanup(days, vacuum, dry_run, neon, aggressive):
    """Clean up old synced log entries to free storage space."""
    from datetime import datetime, timedelta
    
    if neon and aggressive:
        if not config.sync_enabled:
            click.echo(f"\n{E_WARN} NeonDB sync is not enabled")
            click.echo("   Set NEON_DB_URL environment variable to enable")
            return
        
        async def do_aggressive_neon_cleanup():
            try:
                storage_info_before = await sync.get_storage_usage()
                usage_before = storage_info_before.get("total_mb", 0)
                
                results = await sync.aggressive_cleanup()
                
                storage_info_after = await sync.get_storage_usage()
                usage_after = storage_info_after.get("total_mb", 0)
                
                return results, usage_before, usage_after
            except Exception as e:
                return None, 0, str(e)
        
        click.echo(f"\n{click.style('NeonDB Aggressive Cleanup', fg='red', bold=True)}")
        click.echo("   This will reduce retention to minimal levels")
        click.echo("   Logs: 3 days | Daily aggregates: 1 month | Monthly aggregates: 2 months")
        click.echo()
        
        results, usage_before, usage_after = asyncio.run(do_aggressive_neon_cleanup())
        
        if isinstance(usage_after, str):
            click.echo(f"\n{E_ERROR} Cleanup failed: {usage_after}")
            return
        
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['logs_deleted']} log entries")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['aggregates_deleted']['daily']} daily aggregates")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['aggregates_deleted']['monthly']} monthly aggregates")
        
        if results['vacuum_run']:
            click.echo(f"   {click.style(E_CHECK, fg='green')} VACUUM ANALYZE completed")
        
        freed = usage_before - usage_after
        click.echo(f"\n{click.style('Storage freed:', fg='cyan')} {freed:.2f} MB")
        click.echo(f"   Before: {usage_before:.2f} MB | After: {usage_after:.2f} MB")
        return
    
    if neon:
        if not config.sync_enabled:
            click.echo(f"\n{E_WARN} NeonDB sync is not enabled")
            click.echo("   Set NEON_DB_URL environment variable to enable")
            return
        
        neon_config = getattr(config.storage, 'neon', None)
        log_days = neon_config.neon_log_retention_days if neon_config else 7
        agg_months = neon_config.neon_aggregate_retention_months if neon_config else 3
        should_vacuum = vacuum if vacuum is not None else True
        
        async def do_neon_cleanup():
            try:
                storage_info_before = await sync.get_storage_usage()
                usage_before = storage_info_before.get("total_mb", 0)
                
                deleted_logs = await sync.cleanup_old_logs(log_days)
                deleted_aggs = await sync.cleanup_old_aggregates(agg_months)
                
                storage_info_after = await sync.get_storage_usage()
                usage_after = storage_info_after.get("total_mb", 0)
                
                return deleted_logs, deleted_aggs, usage_before, usage_after
            except Exception as e:
                return 0, {}, 0, str(e)
        
        click.echo(f"\n{click.style('NeonDB Cleanup', fg='cyan', bold=True)}")
        click.echo(f"   Log retention: {log_days} days")
        click.echo(f"   Aggregate retention: {agg_months} months")
        click.echo()
        
        deleted_logs, deleted_aggs, usage_before, usage_after = asyncio.run(do_neon_cleanup())
        
        if isinstance(usage_after, str):
            click.echo(f"\n{E_ERROR} Cleanup failed: {usage_after}")
            return
        
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_logs} log entries")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggs.get('daily_deleted', 0)} daily aggregates")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggs.get('monthly_deleted', 0)} monthly aggregates")
        
        freed = usage_before - usage_after
        click.echo(f"\n{click.style('Storage freed:', fg='cyan')} {freed:.2f} MB")
        click.echo(f"   Before: {usage_before:.2f} MB | After: {usage_after:.2f} MB")
        return
    
    days_to_keep = days if days is not None else config.storage.log_retention_days
    should_vacuum = vacuum if vacuum is not None else config.storage.vacuum_after_cleanup
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    click.echo(f"\n{click.style('Storage Cleanup', fg='cyan', bold=True)}")
    click.echo(f"   Retention: {days_to_keep} days")
    click.echo(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"   Mode: {'dry run (no changes)' if dry_run else 'live'}")
    click.echo()
    
    try:
        if dry_run:
            synced_count = db.get_synced_log_count()
            click.echo(f"   Synced logs that would be deleted: {click.style(str(synced_count), fg='yellow')}")
            if should_vacuum:
                click.echo(f"   VACUUM would run after cleanup")
            click.echo(f"\n{click.style('Dry run complete. No changes made.', fg='green')}")
            return
        
        click.echo("   Cleaning up synced logs...")
        deleted_logs = db.cleanup_synced_logs(days_to_keep)
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_logs} synced log entries")
        
        click.echo("   Cleaning up old aggregates...")
        deleted_aggregates = db.cleanup_old_aggregates(config.storage.aggregate_retention_months)
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggregates['daily']} daily aggregates")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggregates['monthly']} monthly aggregates")
        
        if should_vacuum:
            click.echo("   Running VACUUM to reclaim space...")
            db.vacuum_database()
            click.echo(f"   {click.style(E_CHECK, fg='green')} VACUUM completed")
        
        click.echo(f"\n{click.style('Cleanup complete!', fg='green', bold=True)}")
        
    except Exception as e:
        click.echo(f"\n{click.style(f'{E_ERROR} Error during cleanup:', fg='red')} {e}")


@storage.command(name="stats")
def storage_stats():
    """Show database storage statistics."""
    try:
        stats = db.get_database_stats()
        
        click.echo(f"\n{click.style('Database Statistics', fg='cyan', bold=True)}\n")
        
        table = [
            ["Usage Logs", f"{stats['usage_logs_count']:,}"],
            ["Daily Aggregates", f"{stats['daily_aggregates_count']:,}"],
            ["Monthly Aggregates", f"{stats['monthly_aggregates_count']:,}"],
            ["Synced Logs", click.style(str(stats['synced_count']), fg='green')],
            ["Unsynced Logs", click.style(str(stats['unsynced_count']), fg='yellow')],
        ]
        
        click.echo(tabulate(table, headers=["Table", "Count"], tablefmt=TABLE_FMT))
        
        click.echo(f"\n{click.style('Timestamps', fg='cyan', bold=True)}")
        if stats['oldest_timestamp']:
            click.echo(f"   Oldest log: {stats['oldest_timestamp']}")
            click.echo(f"   Newest log: {stats['newest_timestamp']}")
        else:
            click.echo("   No logs recorded yet")
        
        click.echo(f"\n{click.style('Storage', fg='cyan', bold=True)}")
        click.echo(f"   Database size: {stats['db_size_mb']} MB")
        
        if stats['storage_usage_percent'] >= 80:
            usage_style = {'fg': 'red', 'bold': True}
            warning = f" {click.style(f'{E_WARN} WARNING: High storage usage!', fg='red')}"
        elif stats['storage_usage_percent'] >= 60:
            usage_style = {'fg': 'yellow'}
            warning = ""
        else:
            usage_style = {'fg': 'green'}
            warning = ""
        
        usage_pct = click.style(f"{stats['storage_usage_percent']}%", **usage_style)
        click.echo(f"   Storage usage: {usage_pct}{warning}")
        
    except Exception as e:
        click.echo(f"\n{click.style(f'{E_ERROR} Error getting stats:', fg='red')} {e}")


@storage.command(name="neon")
def storage_neon():
    """Show NeonDB storage statistics and usage."""
    
    if not config.sync_enabled:
        click.echo(f"\n{E_WARN} NeonDB sync is not enabled")
        click.echo("   Set NEON_DB_URL environment variable to enable")
        return
    
    async def get_neon_info():
        try:
            storage_info = await sync.get_storage_usage()
            usage_percent = await sync.get_storage_usage_percent()
            remote_stats = await sync.get_remote_stats()
            return storage_info, usage_percent, remote_stats
        except Exception as e:
            return None, None, str(e)
    
    try:
        storage_info, usage_percent, remote_stats = asyncio.run(get_neon_info())
        
        if isinstance(remote_stats, str):
            click.echo(f"\n{E_ERROR} Failed to get NeonDB info: {remote_stats}")
            return
        
        click.echo(f"\n{click.style('NeonDB Storage', fg='cyan', bold=True)}\n")
        
        total_mb = storage_info.get("total_mb", 0) if storage_info else 0
        neon_config = getattr(config.storage, 'neon', None)
        warning_threshold = neon_config.neon_storage_warning_threshold if neon_config else 80
        
        actual_usage_percent = usage_percent if usage_percent is not None else 0.0
        
        if actual_usage_percent >= 90:
            usage_style = {'fg': 'red', 'bold': True}
        elif actual_usage_percent >= warning_threshold:
            usage_style = {'fg': 'yellow'}
        else:
            usage_style = {'fg': 'green'}
        
        usage_table = [
            ["Total Used", f"{total_mb} MB"],
            ["Free Tier Limit", "512 MB (0.5 GB)"],
            ["Usage", click.style(f"{actual_usage_percent}%", **usage_style)],
            ["Warning Threshold", f"{warning_threshold}%"],
        ]
        click.echo(tabulate(usage_table, headers=["Metric", "Value"], tablefmt=TABLE_FMT))
        
        if actual_usage_percent >= 90:
            click.echo(f"\n{click.style(f'{E_WARN} CRITICAL: Storage almost full!', fg='red', bold=True)}")
            click.echo("   Run 'pb storage cleanup --neon --aggressive' to free space")
        elif actual_usage_percent >= warning_threshold:
            click.echo(f"\n{click.style(f'{E_WARN} Warning: Storage usage high', fg='yellow')}")
            click.echo("   Run 'pb storage cleanup --neon' to free space")
        
        tables = storage_info.get("tables", {}) if storage_info else {}
        if tables:
            click.echo(f"\n{click.style('Table Sizes', fg='cyan', bold=True)}")
            table_data = [[name, f"{info.get('total_size_mb', 0)} MB"] for name, info in tables.items()]
            click.echo(tabulate(table_data, headers=["Table", "Size"], tablefmt=TABLE_FMT))
        
        click.echo(f"\n{click.style('Statistics', fg='cyan', bold=True)}")
        click.echo(f"   Devices: {remote_stats.get('device_count', 0) if remote_stats else 0}")
        click.echo(f"   Total logs: {remote_stats.get('log_count', 0) if remote_stats else 0}")
        
        click.echo(f"\n{click.style('Retention Settings', fg='cyan', bold=True)}")
        log_days = neon_config.neon_log_retention_days if neon_config else 7
        agg_months = neon_config.neon_aggregate_retention_months if neon_config else 3
        click.echo(f"   Logs: {log_days} days")
        click.echo(f"   Aggregates: {agg_months} months")
        
    except Exception as e:
        click.echo(f"\n{E_ERROR} Error: {e}")


@cli.command()
@click.option("--days", default=None, help="Days to keep synced logs (default from config)")
@click.option("--vacuum/--no-vacuum", default=None, help="Run VACUUM after cleanup")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting")
def cleanup(days, vacuum, dry_run):
    """Clean up old synced log entries to free storage space."""
    from datetime import datetime, timedelta
    
    days_to_keep = days if days is not None else config.storage.log_retention_days
    should_vacuum = vacuum if vacuum is not None else config.storage.vacuum_after_cleanup
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    click.echo(f"\n{click.style('Storage Cleanup', fg='cyan', bold=True)}")
    click.echo(f"   Retention: {days_to_keep} days")
    click.echo(f"   Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"   Mode: {'dry run (no changes)' if dry_run else 'live'}")
    click.echo()
    
    try:
        if dry_run:
            synced_count = db.get_synced_log_count()
            click.echo(f"   Synced logs that would be deleted: {click.style(str(synced_count), fg='yellow')}")
            if should_vacuum:
                click.echo(f"   VACUUM would run after cleanup")
            click.echo(f"\n{click.style('Dry run complete. No changes made.', fg='green')}")
            return
        
        click.echo("   Cleaning up synced logs...")
        deleted_logs = db.cleanup_synced_logs(days_to_keep)
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_logs} synced log entries")
        
        click.echo("   Cleaning up old aggregates...")
        deleted_aggregates = db.cleanup_old_aggregates(config.storage.aggregate_retention_months)
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggregates['daily']} daily aggregates")
        click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {deleted_aggregates['monthly']} monthly aggregates")
        
        if should_vacuum:
            click.echo("   Running VACUUM to reclaim space...")
            db.vacuum_database()
            click.echo(f"   {click.style(E_CHECK, fg='green')} VACUUM completed")
        
        click.echo(f"\n{click.style('Cleanup complete!', fg='green', bold=True)}")
        
    except Exception as e:
        click.echo(f"\n{click.style(f'{E_ERROR} Error during cleanup:', fg='red')} {e}")


@cli.command()
def stats():
    """Show database storage statistics."""
    try:
        stats_data = db.get_database_stats()
        
        click.echo(f"\n{click.style('Database Statistics', fg='cyan', bold=True)}\n")
        
        table = [
            ["Usage Logs", f"{stats_data['usage_logs_count']:,}"],
            ["Daily Aggregates", f"{stats_data['daily_aggregates_count']:,}"],
            ["Monthly Aggregates", f"{stats_data['monthly_aggregates_count']:,}"],
            ["Synced Logs", f"{click.style(str(stats_data['synced_count']), fg='green')}"],
            ["Unsynced Logs", f"{click.style(str(stats_data['unsynced_count']), fg='yellow')}"],
        ]
        
        click.echo(tabulate(table, headers=["Table", "Count"], tablefmt=TABLE_FMT))
        
        click.echo(f"\n{click.style('Timestamps', fg='cyan', bold=True)}")
        if stats_data['oldest_timestamp']:
            click.echo(f"   Oldest log: {stats_data['oldest_timestamp']}")
            click.echo(f"   Newest log: {stats_data['newest_timestamp']}")
        else:
            click.echo("   No logs recorded yet")
        
        click.echo(f"\n{click.style('Storage', fg='cyan', bold=True)}")
        click.echo(f"   Database size: {stats_data['db_size_mb']} MB")
        
        if stats_data['storage_usage_percent'] >= 80:
            usage_style = {'fg': 'red', 'bold': True}
            warning = f" {click.style(f'{E_WARN} WARNING: High storage usage!', fg='red')}"
        elif stats_data['storage_usage_percent'] >= 60:
            usage_style = {'fg': 'yellow'}
            warning = ""
        else:
            usage_style = {'fg': 'green'}
            warning = ""
        
        usage_pct = click.style(f"{stats_data['storage_usage_percent']}%", **usage_style)
        click.echo(f"   Storage usage: {usage_pct}{warning}")
        
    except Exception as e:
        click.echo(f"\n{click.style(f'{E_ERROR} Error getting stats:', fg='red')} {e}")


@cli.command(name="neon-cleanup")
def neon_cleanup():
    """Shortcut for aggressive NeonDB cleanup when storage is critically high."""
    if not config.sync_enabled:
        click.echo(f"\n{E_WARN} NeonDB sync is not enabled")
        click.echo("   Set NEON_DB_URL environment variable to enable")
        return
    
    async def do_aggressive_cleanup():
        try:
            storage_info_before = await sync.get_storage_usage()
            usage_before = storage_info_before.get("total_mb", 0)
            
            results = await sync.aggressive_cleanup()
            
            storage_info_after = await sync.get_storage_usage()
            usage_after = storage_info_after.get("total_mb", 0)
            
            return results, usage_before, usage_after
        except Exception as e:
            return None, 0, str(e)
    
    click.echo(f"\n{click.style('NeonDB Aggressive Cleanup', fg='red', bold=True)}")
    click.echo("   This will reduce retention to minimal levels")
    click.echo("   Logs: 3 days | Daily aggregates: 1 month | Monthly aggregates: 2 months")
    click.echo()
    
    results, usage_before, usage_after = asyncio.run(do_aggressive_cleanup())
    
    if isinstance(usage_after, str):
        click.echo(f"\n{E_ERROR} Cleanup failed: {usage_after}")
        return
    
    if results is None:
        click.echo(f"\n{E_ERROR} Cleanup failed: Unknown error")
        return
    
    click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['logs_deleted']} log entries")
    click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['aggregates_deleted']['daily']} daily aggregates")
    click.echo(f"   {click.style(E_CHECK, fg='green')} Deleted {results['aggregates_deleted']['monthly']} monthly aggregates")
    
    if results['vacuum_run']:
        click.echo(f"   {click.style(E_CHECK, fg='green')} VACUUM ANALYZE completed")
    
    freed = usage_before - usage_after
    click.echo(f"\n{click.style('Storage freed:', fg='cyan')} {freed:.2f} MB")
    click.echo(f"   Before: {usage_before:.2f} MB | After: {usage_after:.2f} MB")


@cli.group()
def service():
    """Manage the background monitoring service."""
    pass


@service.command(name="start")
def service_start():
    """Start the background service."""
    from ..utils.updater import start_service
    click.echo(f"{E_ROCKET} Starting PacketBuddy background service...")
    start_service()
    click.echo(f"{E_OK} Done. You can close this window now.")


@service.command(name="stop")
def service_stop():
    """Stop the background service."""
    from ..utils.updater import stop_service
    click.echo(f"{E_STOP} Stopping PacketBuddy background service...")
    stop_service()
    click.echo(f"{E_OK} Done.")


@service.command(name="restart")
def service_restart():
    """Restart the background service."""
    from ..utils.updater import restart_service
    click.echo(f"{E_RECYCLE}  Restarting PacketBuddy background service...")
    restart_service()
    click.echo(f"{E_OK} Done.")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
