"""NeonDB sync module for cloud data replication."""

import asyncio
import asyncpg
from datetime import datetime, date
from typing import Optional

from ..utils.config import config
from .storage import storage


class NeonSync:
    """Async NeonDB synchronization manager."""
    
    def __init__(self):
        self.running = False
        self.pool: Optional[asyncpg.Pool] = None
        self.sync_interval = config.get("sync", "interval", default=30)
        self.retry_delay = config.get("sync", "retry_delay", default=5)
        self.max_retries = config.get("sync", "max_retries", default=3)
        self.enabled = config.sync_enabled
    
    async def start(self):
        """Start sync service."""
        if not self.enabled:
            print("Sync disabled (no NEON_DB_URL configured)")
            return
        
        self.running = True
        
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                config.neon_db_url,
                min_size=1,
                max_size=config.get("database", "pool_size", default=5),
            )
            
            # Initialize remote schema
            await self._init_remote_schema()
            
            # Start sync loop
            await self._sync_loop()
            
        except Exception as e:
            print(f"Sync service error: {e}")
            self.enabled = False
    
    async def _init_remote_schema(self):
        """Initialize NeonDB schema."""
        async with self.pool.acquire() as conn:
            # Devices table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    os_type TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Usage logs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id SERIAL PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    bytes_sent BIGINT NOT NULL,
                    bytes_received BIGINT NOT NULL,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_logs_device_timestamp 
                ON usage_logs(device_id, timestamp)
            """)
            
            # Daily aggregates
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_aggregates (
                    device_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    bytes_sent BIGINT NOT NULL,
                    bytes_received BIGINT NOT NULL,
                    PRIMARY KEY (device_id, date),
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Monthly aggregates
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monthly_aggregates (
                    device_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    bytes_sent BIGINT NOT NULL,
                    bytes_received BIGINT NOT NULL,
                    PRIMARY KEY (device_id, month),
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Register device
            await conn.execute("""
                INSERT INTO devices (device_id, os_type, hostname)
                VALUES ($1, $2, $3)
                ON CONFLICT (device_id) DO UPDATE SET
                    os_type = EXCLUDED.os_type,
                    hostname = EXCLUDED.hostname
            """, storage.device_id, storage.os_type, storage.hostname)
    
    async def _sync_loop(self):
        """Main sync loop."""
        while self.running:
            await asyncio.sleep(self.sync_interval)
            
            if not self.enabled:
                continue
            
            try:
                await self._sync_data()
            except Exception as e:
                print(f"Sync error: {e}")
    
    async def _sync_data(self):
        """Sync unsynced logs to NeonDB with retry."""
        logs = storage.get_unsynced_logs(limit=1000)
        
        if not logs:
            return
        
        for attempt in range(self.max_retries):
            try:
                async with self.pool.acquire() as conn:
                    async with conn.transaction():
                        # Batch insert usage logs
                        # Batch insert usage logs
                        sync_data = []
                        daily_aggs = {}
                        monthly_aggs = {}

                        for log in logs:
                            ts = datetime.fromisoformat(log["timestamp"])
                            sync_data.append((log["device_id"], ts, log["bytes_sent"], log["bytes_received"]))
                            
                            # Aggregate for daily stats
                            log_date = ts.date()
                            d_key = (log["device_id"], log_date)
                            if d_key not in daily_aggs:
                                daily_aggs[d_key] = {"sent": 0, "received": 0}
                            daily_aggs[d_key]["sent"] += log["bytes_sent"]
                            daily_aggs[d_key]["received"] += log["bytes_received"]

                            # Aggregate for monthly stats
                            month_str = log_date.strftime("%Y-%m")
                            m_key = (log["device_id"], month_str)
                            if m_key not in monthly_aggs:
                                monthly_aggs[m_key] = {"sent": 0, "received": 0}
                            monthly_aggs[m_key]["sent"] += log["bytes_sent"]
                            monthly_aggs[m_key]["received"] += log["bytes_received"]

                        await conn.executemany("""
                            INSERT INTO usage_logs (device_id, timestamp, bytes_sent, bytes_received)
                            VALUES ($1, $2, $3, $4)
                        """, sync_data)
                        
                        # Update daily aggregates (Batch)
                        for (device_id, log_date), stats in daily_aggs.items():
                            await conn.execute("""
                                INSERT INTO daily_aggregates (device_id, date, bytes_sent, bytes_received)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (device_id, date) DO UPDATE SET
                                    bytes_sent = daily_aggregates.bytes_sent + EXCLUDED.bytes_sent,
                                    bytes_received = daily_aggregates.bytes_received + EXCLUDED.bytes_received
                            """, device_id, log_date, stats["sent"], stats["received"])
                            
                        # Update monthly aggregates (Batch)
                        for (device_id, month_str), stats in monthly_aggs.items():
                            await conn.execute("""
                                INSERT INTO monthly_aggregates (device_id, month, bytes_sent, bytes_received)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (device_id, month) DO UPDATE SET
                                    bytes_sent = monthly_aggregates.bytes_sent + EXCLUDED.bytes_sent,
                                    bytes_received = monthly_aggregates.bytes_received + EXCLUDED.bytes_received
                            """, device_id, month_str, stats["sent"], stats["received"])
                
                # Mark as synced
                log_ids = [log["id"] for log in logs]
                storage.mark_logs_synced(log_ids)
                
                print(f"Synced {len(logs)} logs to NeonDB")
                break
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

    async def get_global_today_usage(self) -> Tuple[int, int]:
        """Fetch today's total usage across all devices from NeonDB."""
        if not self.enabled or not self.pool:
            return 0, 0
            
        try:
            today_date = date.today()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        SUM(bytes_sent) as total_sent,
                        SUM(bytes_received) as total_received
                    FROM daily_aggregates
                    WHERE date = $1
                """, today_date)
                
                if row and row["total_sent"] is not None:
                    return int(row["total_sent"]), int(row["total_received"])
        except Exception as e:
            print(f"Failed to fetch global today usage: {e}")
        return 0, 0

    async def get_global_lifetime_usage(self) -> Tuple[int, int]:
        """Fetch lifetime total usage across all devices from NeonDB."""
        if not self.enabled or not self.pool:
            return 0, 0
            
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT 
                        SUM(bytes_sent) as total_sent,
                        SUM(bytes_received) as total_received
                    FROM monthly_aggregates
                """)
                
                if row and row["total_sent"] is not None:
                    return int(row["total_sent"]), int(row["total_received"])
        except Exception as e:
            print(f"Failed to fetch global lifetime usage: {e}")
        return 0, 0

    async def get_device_count(self) -> int:
        """Get the count of distinct devices in the network."""
        if not self.enabled or not self.pool:
            return 1
            
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM devices")
                return count or 1
        except Exception as e:
            print(f"Failed to fetch device count: {e}")
        return 1
    
    async def stop(self):
        """Stop sync service gracefully."""
        self.running = False
        
        # Final sync attempt
        if self.enabled and self.pool:
            try:
                await self._sync_data()
            except Exception as e:
                print(f"Final sync error: {e}")
        
        if self.pool:
            await self.pool.close()


# Global sync instance
sync = NeonSync()
