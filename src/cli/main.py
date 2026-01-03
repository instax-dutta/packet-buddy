"""CLI interface for PacketBuddy."""

import click
from datetime import datetime
from tabulate import tabulate

from ..core.storage import storage
from ..utils.formatters import format_bytes, format_speed
from ..core.monitor import monitor
from ..api.server import run_server


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
    
    click.echo("\n" + tabulate(table, headers=["Metric", "Value"], tablefmt="fancy_grid"))


@cli.command()
def today():
    """Show today's usage."""
    bytes_sent, bytes_received = storage.get_today_usage()
    total = bytes_sent + bytes_received
    
    table = [
        ["Uploaded", format_bytes(bytes_sent)],
        ["Downloaded", format_bytes(bytes_received)],
        ["Total", format_bytes(total)],
    ]
    
    click.echo("\n📊 Today's Usage\n")
    click.echo(tabulate(table, headers=["Type", "Amount"], tablefmt="fancy_grid"))


@cli.command()
@click.argument("month", required=False)
def month(month: str = None):
    """Show monthly usage breakdown."""
    if month is None:
        month = datetime.utcnow().strftime("%Y-%m")
    
    daily_data = storage.get_month_usage(month)
    
    if not daily_data:
        click.echo(f"\n❌ No data for {month}")
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
    
    click.echo(f"\n📅 Usage for {month}\n")
    click.echo(tabulate(table, headers=["Date", "Uploaded", "Downloaded", "Total"], tablefmt="fancy_grid"))
    
    click.echo(f"\n📈 Month Summary:")
    click.echo(f"   Total Uploaded: {format_bytes(total_sent)}")
    click.echo(f"   Total Downloaded: {format_bytes(total_received)}")
    click.echo(f"   Total: {format_bytes(total_sent + total_received)}\n")


@cli.command()
def summary():
    """Show lifetime usage summary."""
    bytes_sent, bytes_received = storage.get_lifetime_usage()
    total = bytes_sent + bytes_received
    
    table = [
        ["Total Uploaded", format_bytes(bytes_sent)],
        ["Total Downloaded", format_bytes(bytes_received)],
        ["Grand Total", format_bytes(total)],
    ]
    
    click.echo("\n🌐 Lifetime Usage Summary\n")
    click.echo(tabulate(table, headers=["Metric", "Amount"], tablefmt="fancy_grid"))


@cli.command()
@click.option("--format", type=click.Choice(["json", "csv"]), default="json", help="Export format")
@click.option("--output", type=click.Path(), help="Output file path")
def export(format: str, output: str = None):
    """Export all usage data."""
    import json
    import csv
    
    logs = storage.get_all_usage_logs()
    
    if not logs:
        click.echo("❌ No data to export")
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
    
    click.echo(f"✅ Exported {len(logs)} records to {output}")


@cli.command()
def serve():
    """Start the API server and dashboard."""
    run_server()


@cli.command()
@click.option("--check-only", is_flag=True, help="Only check for updates, don't apply")
def update(check_only: bool):
    """Check for and apply updates from GitHub."""
    from ..utils.updater import check_for_updates, perform_update, restart_service
    
    click.echo("\n🔍 Checking for updates...")
    
    has_update, current, latest = check_for_updates()
    
    if not has_update:
        if current and latest:
            click.echo(f"✅ You're already on the latest version ({current[:7]})")
        else:
            click.echo("ℹ️  Auto-update not available (not a git repository)")
        return
    
    click.echo(f"\n📦 Update available!")
    click.echo(f"   Current: {current[:7]}")
    click.echo(f"   Latest:  {latest[:7]}")
    
    if check_only:
        click.echo("\nℹ️  Run 'pb update' to apply the update")
        return
    
    if click.confirm("\n🚀 Apply update now?", default=True):
        click.echo("\n⏳ Updating...")
        
        if perform_update():
            click.echo("✅ Update completed successfully!")
            click.echo("\nℹ️  Your data is safe - nothing was deleted")
            
            if click.confirm("\n🔄 Restart service now?", default=True):
                click.echo("♻️  Restarting service...")
                restart_service()
                click.echo("✅ Service restarted!")
                click.echo("\n🎉 All done! PacketBuddy is now up to date.\n")
            else:
                click.echo("\nℹ️  Please restart the service manually:")
                click.echo("   macOS: launchctl kickstart -k gui/$(id -u)/com.packetbuddy.daemon")
                click.echo("   Windows: schtasks /run /tn PacketBuddy")
                click.echo("   Linux: systemctl --user restart packetbuddy.service\n")
        else:
            click.echo("❌ Update failed. Check logs for details.\n")


@cli.group()
def service():
    """Manage the background monitoring service."""
    pass


@service.command(name="start")
def service_start():
    """Start the background service."""
    from ..utils.updater import start_service
    click.echo("🚀 Starting PacketBuddy background service...")
    start_service()
    click.echo("✅ Done. You can close this window now.")


@service.command(name="stop")
def service_stop():
    """Stop the background service."""
    from ..utils.updater import stop_service
    click.echo("🛑 Stopping PacketBuddy background service...")
    stop_service()
    click.echo("✅ Done.")


@service.command(name="restart")
def service_restart():
    """Restart the background service."""
    from ..utils.updater import restart_service
    click.echo("♻️  Restarting PacketBuddy background service...")
    restart_service()
    click.echo("✅ Done.")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
