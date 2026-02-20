"""NeonDB sync module for cloud data replication."""

import asyncio
import asyncpg
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any

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
    
    async def vacuum_database(self) -> bool:
        """Run VACUUM ANALYZE on NeonDB to reclaim space after deletions."""
        if not self.enabled or not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("VACUUM ANALYZE usage_logs")
                await conn.execute("VACUUM ANALYZE daily_aggregates")
                await conn.execute("VACUUM ANALYZE monthly_aggregates")
                await conn.execute("VACUUM ANALYZE devices")
                return True
        except Exception as e:
            print(f"Failed to vacuum NeonDB: {e}")
        return False

    async def get_storage_usage_percent(self) -> float:
        """Get storage usage as percentage of 512MB NeonDB free tier limit."""
        storage_info = await self.get_storage_usage()
        total_mb = storage_info.get("total_mb", 0)
        return round((total_mb / 512) * 100, 1)

    async def aggressive_cleanup(self) -> dict:
        """Aggressive cleanup when storage is critically high.
        Reduces retention to minimal levels to free space quickly."""
        if not self.enabled or not self.pool:
            return {"logs_deleted": 0, "aggregates_deleted": {}, "vacuum_run": False}
        
        results = {"logs_deleted": 0, "aggregates_deleted": {}, "vacuum_run": False}
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM usage_logs
                    WHERE timestamp < NOW() - INTERVAL '3 days'
                """)
                results["logs_deleted"] = int(result.split()[-1]) if result else 0
                
                daily_result = await conn.execute("""
                    DELETE FROM daily_aggregates
                    WHERE date < CURRENT_DATE - INTERVAL '1 month'
                """)
                
                monthly_result = await conn.execute("""
                    DELETE FROM monthly_aggregates
                    WHERE month < TO_CHAR(CURRENT_DATE - INTERVAL '2 months', 'YYYY-MM')
                """)
                
                results["aggregates_deleted"] = {
                    "daily": int(daily_result.split()[-1]) if daily_result else 0,
                    "monthly": int(monthly_result.split()[-1]) if monthly_result else 0
                }
            
            results["vacuum_run"] = await self.vacuum_database()
            
        except Exception as e:
            print(f"Aggressive cleanup failed: {e}")
        
        return results

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        if not self.enabled or not self.pool:
            return 0
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM usage_logs
                    WHERE timestamp < NOW() - INTERVAL '1 day' * $1
                """, days_to_keep)
                
                deleted = int(result.split()[-1]) if result else 0
            
            if deleted > 0 and config.storage.vacuum_after_cleanup:
                await self.vacuum_database()
            
            return deleted
        except Exception as e:
            print(f"Failed to cleanup old logs: {e}")
        return 0

    async def cleanup_old_aggregates(self, months_to_keep: int = 12) -> dict:
        if not self.enabled or not self.pool:
            return {"daily_deleted": 0, "monthly_deleted": 0}
        
        try:
            async with self.pool.acquire() as conn:
                daily_result = await conn.execute("""
                    DELETE FROM daily_aggregates
                    WHERE date < CURRENT_DATE - INTERVAL '1 month' * $1
                """, months_to_keep)
                
                monthly_result = await conn.execute("""
                    DELETE FROM monthly_aggregates
                    WHERE month < TO_CHAR(CURRENT_DATE - INTERVAL '1 month' * $1, 'YYYY-MM')
                """, months_to_keep)
                
                daily_deleted = int(daily_result.split()[-1]) if daily_result else 0
                monthly_deleted = int(monthly_result.split()[-1]) if monthly_result else 0
                
                return {
                    "daily_deleted": daily_deleted,
                    "monthly_deleted": monthly_deleted
                }
        except Exception as e:
            print(f"Failed to cleanup old aggregates: {e}")
        return {"daily_deleted": 0, "monthly_deleted": 0}

    async def get_remote_stats(self) -> dict:
        if not self.enabled or not self.pool:
            return {
                "device_count": 0,
                "log_count": 0,
                "logs_per_device": [],
                "oldest_log": None,
                "newest_log": None,
                "table_sizes": {}
            }
        
        try:
            async with self.pool.acquire() as conn:
                device_count = await conn.fetchval("SELECT COUNT(*) FROM devices")
                
                log_count = await conn.fetchval("SELECT COUNT(*) FROM usage_logs")
                
                logs_per_device = await conn.fetch("""
                    SELECT device_id, COUNT(*) as log_count
                    FROM usage_logs
                    GROUP BY device_id
                    ORDER BY log_count DESC
                """)
                
                oldest_log = await conn.fetchval("""
                    SELECT MIN(timestamp) FROM usage_logs
                """)
                
                newest_log = await conn.fetchval("""
                    SELECT MAX(timestamp) FROM usage_logs
                """)
                
                table_sizes = await conn.fetch("""
                    SELECT 
                        tablename,
                        pg_relation_size(schemaname || '.' || tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                
                return {
                    "device_count": device_count or 0,
                    "log_count": log_count or 0,
                    "logs_per_device": [
                        {"device_id": row["device_id"], "log_count": row["log_count"]}
                        for row in logs_per_device
                    ],
                    "oldest_log": oldest_log.isoformat() if oldest_log else None,
                    "newest_log": newest_log.isoformat() if newest_log else None,
                    "table_sizes": {
                        row["tablename"]: row["size_bytes"] or 0
                        for row in table_sizes
                    }
                }
        except Exception as e:
            print(f"Failed to get remote stats: {e}")
        return {
            "device_count": 0,
            "log_count": 0,
            "logs_per_device": [],
            "oldest_log": None,
            "newest_log": None,
            "table_sizes": {}
        }

    async def get_storage_usage(self) -> dict:
        if not self.enabled or not self.pool:
            return {"total_mb": 0.0, "tables": {}}
        
        try:
            async with self.pool.acquire() as conn:
                table_sizes = await conn.fetch("""
                    SELECT 
                        tablename,
                        pg_relation_size(schemaname || '.' || tablename) as size_bytes,
                        pg_total_relation_size(schemaname || '.' || tablename) as total_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY total_bytes DESC
                """)
                
                total_bytes = 0
                tables = {}
                
                for row in table_sizes:
                    size_bytes = row["size_bytes"] or 0
                    total_bytes_table = row["total_bytes"] or 0
                    total_bytes += total_bytes_table
                    
                    tables[row["tablename"]] = {
                        "table_size_mb": round(size_bytes / (1024 * 1024), 2),
                        "total_size_mb": round(total_bytes_table / (1024 * 1024), 2)
                    }
                
                return {
                    "total_mb": round(total_bytes / (1024 * 1024), 2),
                    "tables": tables
                }
        except Exception as e:
            print(f"Failed to get storage usage: {e}")
        return {"total_mb": 0.0, "tables": {}}

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
