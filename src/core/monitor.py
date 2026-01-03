import asyncio
import psutil
import subprocess
import platform
from datetime import datetime
from typing import Optional

from ..utils.config import config
from .storage import storage


class NetworkMonitor:
    """Async network usage monitor."""
    
    def __init__(self):
        self.running = False
        self.last_sent = 0
        self.last_received = 0
        self.current_speed_sent = 0.0
        self.current_speed_received = 0.0
        self.poll_interval = config.get("monitoring", "poll_interval", default=1)
        self.max_delta = config.get("monitoring", "max_delta_bytes", default=1_000_000_000)
        
        # Buffer for batched writes
        self.pending_writes = []
        self.batch_interval = config.get("monitoring", "batch_write_interval", default=5)
        
        # Battery-aware settings
        self.is_on_battery = False
        self.base_poll_interval = self.poll_interval
        self.base_batch_interval = self.batch_interval
    
    def _get_primary_interface(self) -> Optional[str]:
        """Try to detect the primary network interface with a default gateway."""
        try:
            sys_platform = platform.system()
            if sys_platform == "Darwin":
                # On macOS
                result = subprocess.run(
                    ["route", "-n", "get", "default"], 
                    capture_output=True, text=True, timeout=2
                )
                for line in result.stdout.splitlines():
                    if "interface:" in line:
                        return line.split(":")[1].strip()
            elif sys_platform == "Windows":
                # On Windows
                cmd = "Get-NetRoute -DestinationPrefix 0.0.0.0/0 | Sort-Object RouteMetric | Select-Object -First 1 -ExpandProperty InterfaceAlias"
                result = subprocess.run(
                    ["powershell", "-Command", cmd],
                    capture_output=True, text=True, timeout=3, shell=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            elif sys_platform == "Linux":
                # On Linux
                result = subprocess.run(
                    ["ip", "route", "show", "default"],
                    capture_output=True, text=True, timeout=2
                )
                for line in result.stdout.splitlines():
                    if "default via" in line:
                        parts = line.split()
                        if "dev" in parts:
                            return parts[parts.index("dev") + 1]
        except Exception as e:
            print(f"Error detecting primary interface: {e}")
        return None

    def _get_network_counters(self) -> tuple:
        """Get current network I/O counters, focusing on primary interface to avoid inflation."""
        all_counters = psutil.net_io_counters(pernic=True)
        primary = self._get_primary_interface()
        
        if primary and primary in all_counters:
            counters = all_counters[primary]
            return counters.bytes_sent, counters.bytes_recv
            
        # Fallback: Sum physical-looking interfaces
        total_sent = 0
        total_received = 0
        ignore_prefixes = ('lo', 'utun', 'awdl', 'llw', 'anpi', 'gif', 'stf', 'bridge', 'ap')
        
        for name, counters in all_counters.items():
            if any(name.lower().startswith(prefix) for prefix in ignore_prefixes):
                continue
            total_sent += counters.bytes_sent
            total_received += counters.bytes_recv
            
        return total_sent, total_received
        
    def _check_battery_status(self):
        """Check if we are on battery and adjust intervals."""
        battery = psutil.sensors_battery()
        if battery is not None:
            on_battery = not battery.power_plugged
            
            if on_battery != self.is_on_battery:
                self.is_on_battery = on_battery
                if on_battery:
                    # Save power: poll less often, batch more data
                    self.poll_interval = self.base_poll_interval * 2
                    self.batch_interval = self.base_batch_interval * 6
                else:
                    # Regain real-time performance on AC power
                    self.poll_interval = self.base_poll_interval
                    self.batch_interval = self.base_batch_interval
    
    async def start(self):
        """Start monitoring network usage."""
        self.running = True
        
        # Initialize counters
        primary = self._get_primary_interface()
        if primary:
            print(f"Monitoring primary interface: {primary}")
        else:
            print("No primary interface detected, falling back to all non-loopback interfaces")
            
        self.last_sent, self.last_received = self._get_network_counters()
        
        # Start monitoring and batch writing tasks
        try:
            await asyncio.gather(
                self._monitor_loop(),
                self._batch_write_loop(),
                self._battery_check_loop(),
            )
        except Exception as e:
            print(f"Monitor service crash: {e}")
            self.running = False

    async def _battery_check_loop(self):
        """Periodically check battery status."""
        while self.running:
            try:
                self._check_battery_status()
            except Exception as e:
                print(f"Battery check error: {e}")
            await asyncio.sleep(30)  # Check battery every 30s
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Get current counters
                current_sent, current_received = self._get_network_counters()
                
                # Calculate deltas
                delta_sent = current_sent - self.last_sent
                delta_received = current_received - self.last_received
                
                # Detect counter reset (system sleep/resume or counter overflow)
                if delta_sent < 0 or delta_received < 0:
                    # Counter reset detected, skip this sample
                    self.last_sent = current_sent
                    self.last_received = current_received
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                # Anomaly detection: skip unreasonably large deltas
                if delta_sent > self.max_delta or delta_received > self.max_delta:
                    # Likely a system issue, skip
                    self.last_sent = current_sent
                    self.last_received = current_received
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                # Update current speed (bytes per second)
                self.current_speed_sent = delta_sent / self.poll_interval
                self.current_speed_received = delta_received / self.poll_interval
                
                # Add to pending writes buffer
                if delta_sent > 0 or delta_received > 0:
                    self.pending_writes.append({
                        "bytes_sent": delta_sent,
                        "bytes_received": delta_received,
                        "timestamp": datetime.now()
                    })
                
                # Update last values
                self.last_sent = current_sent
                self.last_received = current_received
                
            except Exception as e:
                print(f"Monitor loop error: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    async def _batch_write_loop(self):
        """Batch write pending data to SQLite."""
        while self.running:
            await asyncio.sleep(self.batch_interval)
            
            if not self.pending_writes:
                continue
            
            try:
                # Flush pending writes to database
                for entry in self.pending_writes:
                    storage.insert_usage(
                        bytes_sent=entry["bytes_sent"],
                        bytes_received=entry["bytes_received"],
                        timestamp=entry["timestamp"]
                    )
                
                # Clear buffer
                self.pending_writes.clear()
                
            except Exception as e:
                print(f"Batch write error: {e}")
    
    async def stop(self):
        """Stop monitoring gracefully."""
        self.running = False
        
        # Flush any remaining writes
        if self.pending_writes:
            for entry in self.pending_writes:
                try:
                    storage.insert_usage(
                        bytes_sent=entry["bytes_sent"],
                        bytes_received=entry["bytes_received"],
                        timestamp=entry["timestamp"]
                    )
                except Exception as e:
                    print(f"Final flush error: {e}")
        
        self.pending_writes.clear()
    
    def get_current_speed(self) -> tuple:
        """Get current upload/download speed."""
        return self.current_speed_sent, self.current_speed_received


# Global monitor instance
monitor = NetworkMonitor()
