"""NeonDB sync module for cloud data replication."""

import asyncio
import logging
import time
import asyncpg
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

from ..utils.config import config
from .storage import storage


class NeonSync:
    """Async NeonDB synchronization manager."""
    
    def __init__(self):
        self.running = False
        self.pool: Optional[asyncpg.Pool] = None
        self.sync_interval = config.get("sync", "interval", default=300)
        self.retry_delay = config.get("sync", "retry_delay", default=5)
        self.max_retries = config.get("sync", "max_retries", default=3)
        self.enabled = config.sync_enabled
        # Local TTL cache for remote queries — avoids burning CU-hours on hot API paths
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = config.get("sync", "cache_ttl", default=300)

    def _cache_get(self, key: str):
        """Get cached value if not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.monotonic() < expiry:
                return value
        return None

    def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value with TTL in seconds (defaults to self._cache_ttl)."""
        self._cache[key] = (value, time.monotonic() + (ttl or self._cache_ttl))
    
    async def start(self):
        """Start sync service."""
        if not self.enabled:
            logger.info("Sync disabled (no NEON_DB_URL configured)")
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
            logger.error("Sync service error: %s", e)
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
                logger.error("Sync error: %s", e)
    
    async def _sync_data(self):
        """Sync aggregates to NeonDB with retry.
        
        Free-tier optimization: Only syncs aggregates (daily + monthly),
        NOT raw usage_logs. Raw per-second logs consume ~90%+ of storage
        but provide zero value for multi-device cross-device views.
        Aggregates are ~0.01% the size and contain all information needed.
        """
        daily = storage.get_all_daily_aggregates()
        monthly = storage.get_all_monthly_aggregates()
        
        if not daily and not monthly:
            return
        
        for attempt in range(self.max_retries):
            try:
                async with self.pool.acquire() as conn:
                    async with conn.transaction():
                        for day in daily:
                            await conn.execute("""
                                INSERT INTO daily_aggregates (device_id, date, bytes_sent, bytes_received)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (device_id, date) DO UPDATE SET
                                    bytes_sent = daily_aggregates.bytes_sent + EXCLUDED.bytes_sent,
                                    bytes_received = daily_aggregates.bytes_received + EXCLUDED.bytes_received
                            """, day["device_id"], day["date"], day["bytes_sent"], day["bytes_received"])
                        
                        for m in monthly:
                            await conn.execute("""
                                INSERT INTO monthly_aggregates (device_id, month, bytes_sent, bytes_received)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (device_id, month) DO UPDATE SET
                                    bytes_sent = monthly_aggregates.bytes_sent + EXCLUDED.bytes_sent,
                                    bytes_received = monthly_aggregates.bytes_received + EXCLUDED.bytes_received
                            """, m["device_id"], m["month"], m["bytes_sent"], m["bytes_received"])
                
                logger.info("Synced %d daily + %d monthly aggregates to NeonDB", len(daily), len(monthly))
                break
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

    async def get_global_today_usage(self) -> Tuple[int, int]:
        """Fetch today's total usage across all devices from NeonDB.
        
        Free-tier optimization: Results cached locally for {self._cache_ttl}s.
        """
        cached = self._cache_get("global_today")
        if cached is not None:
            return cached
        
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
                    result = (int(row["total_sent"]), int(row["total_received"]))
                    self._cache_set("global_today", result)
                    return result
        except Exception as e:
            logger.error("Failed to fetch global today usage: %s", e)
        return 0, 0

    async def get_global_lifetime_usage(self) -> Tuple[int, int]:
        """Fetch lifetime total usage across all devices from NeonDB.
        
        Free-tier optimization: Results cached locally for {self._cache_ttl}s.
        """
        cached = self._cache_get("global_lifetime")
        if cached is not None:
            return cached
        
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
                    result = (int(row["total_sent"]), int(row["total_received"]))
                    self._cache_set("global_lifetime", result)
                    return result
        except Exception as e:
            logger.error("Failed to fetch global lifetime usage: %s", e)
        return 0, 0

    async def get_device_count(self) -> int:
        """Get the count of distinct devices in the network.
        
        Free-tier optimization: Results cached locally for {self._cache_ttl}s
        to avoid burning CU-hours on every dashboard poll.
        """
        cached = self._cache_get("device_count")
        if cached is not None:
            return cached
        
        if not self.enabled or not self.pool:
            return 1
            
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM devices")
                result = count or 1
                self._cache_set("device_count", result)
                return result
        except Exception as e:
            logger.error("Failed to fetch device count: %s", e)
        return 1
    
    async def vacuum_database(self) -> bool:
        """Run VACUUM ANALYZE on NeonDB to reclaim space after deletions.
        
        Free-tier optimization: Only vacuums aggregate tables — raw usage_logs
        are no longer synced to NeonDB.
        """
        if not self.enabled or not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("VACUUM ANALYZE daily_aggregates")
                await conn.execute("VACUUM ANALYZE monthly_aggregates")
                await conn.execute("VACUUM ANALYZE devices")
                return True
        except Exception as e:
            logger.error("Failed to vacuum NeonDB: %s", e)
        return False

    async def get_storage_usage_percent(self) -> float:
        """Get storage usage as percentage of 512MB NeonDB free tier limit."""
        storage_info = await self.get_storage_usage()
        total_mb = storage_info.get("total_mb", 0)
        return round((total_mb / 512) * 100, 1)

    async def aggressive_cleanup(self) -> dict:
        """Aggressive cleanup when storage is critically high.
        
        Free-tier optimization: Only cleans aggregates — raw logs are no
        longer synced to NeonDB. Reduces retention to minimal levels.
        """
        if not self.enabled or not self.pool:
            return {"aggregates_deleted": {}, "vacuum_run": False}
        
        results = {"aggregates_deleted": {}, "vacuum_run": False}
        
        try:
            async with self.pool.acquire() as conn:
                daily_deleted = await conn.fetchval("""
                    WITH deleted AS (
                        DELETE FROM daily_aggregates
                        WHERE date < CURRENT_DATE - INTERVAL '1 month'
                        RETURNING 1
                    )
                    SELECT COUNT(*) FROM deleted
                """)
                
                monthly_deleted = await conn.fetchval("""
                    WITH deleted AS (
                        DELETE FROM monthly_aggregates
                        WHERE month < TO_CHAR(CURRENT_DATE - INTERVAL '2 months', 'YYYY-MM')
                        RETURNING 1
                    )
                    SELECT COUNT(*) FROM deleted
                """)
                
                results["aggregates_deleted"] = {
                    "daily": daily_deleted or 0,
                    "monthly": monthly_deleted or 0
                }
            
            results["vacuum_run"] = await self.vacuum_database()
            
        except Exception as e:
            logger.error("Aggressive cleanup failed: %s", e)
        
        return results

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Deprecated: Raw logs are no longer synced to NeonDB.
        
        Kept for API backward compatibility. Returns 0 immediately.
        Use cleanup_old_aggregates() instead.
        """
        return 0

    async def cleanup_old_aggregates(self, months_to_keep: int = 12) -> dict:
        if not self.enabled or not self.pool:
            return {"daily_deleted": 0, "monthly_deleted": 0}
        
        try:
            async with self.pool.acquire() as conn:
                daily_deleted = await conn.fetchval("""
                    WITH deleted AS (
                        DELETE FROM daily_aggregates
                        WHERE date < CURRENT_DATE - INTERVAL '1 month' * $1
                        RETURNING 1
                    )
                    SELECT COUNT(*) FROM deleted
                """, months_to_keep)
                
                monthly_deleted = await conn.fetchval("""
                    WITH deleted AS (
                        DELETE FROM monthly_aggregates
                        WHERE month < TO_CHAR(CURRENT_DATE - INTERVAL '1 month' * $1, 'YYYY-MM')
                        RETURNING 1
                    )
                    SELECT COUNT(*) FROM deleted
                """, months_to_keep)
                
                return {
                    "daily_deleted": daily_deleted or 0,
                    "monthly_deleted": monthly_deleted or 0
                }
        except Exception as e:
            logger.error("Failed to cleanup old aggregates: %s", e)
        return {"daily_deleted": 0, "monthly_deleted": 0}

    async def get_remote_stats(self) -> dict:
        """Get remote statistics.
        
        Free-tier optimization: Only queries aggregate tables and devices.
        Raw usage_logs are no longer synced to NeonDB.
        """
        if not self.enabled or not self.pool:
            return {
                "device_count": 0,
                "daily_count": 0,
                "monthly_count": 0,
                "table_sizes": {}
            }
        
        try:
            async with self.pool.acquire() as conn:
                device_count = await conn.fetchval("SELECT COUNT(*) FROM devices")
                daily_count = await conn.fetchval("SELECT COUNT(*) FROM daily_aggregates")
                monthly_count = await conn.fetchval("SELECT COUNT(*) FROM monthly_aggregates")
                
                table_sizes = await conn.fetch("""
                    SELECT 
                        tablename,
                        pg_relation_size(schemaname || '.' || tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                
                return {
                    "device_count": device_count or 0,
                    "daily_count": daily_count or 0,
                    "monthly_count": monthly_count or 0,
                    "table_sizes": {
                        row["tablename"]: row["size_bytes"] or 0
                        for row in table_sizes
                    }
                }
        except Exception as e:
            logger.error("Failed to get remote stats: %s", e)
        return {
            "device_count": 0,
            "daily_count": 0,
            "monthly_count": 0,
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
            logger.error("Failed to get storage usage: %s", e)
        return {"total_mb": 0.0, "tables": {}}

    async def stop(self):
        """Stop sync service gracefully."""
        self.running = False
        
        # Final sync attempt
        if self.enabled and self.pool:
            try:
                await self._sync_data()
            except Exception as e:
                logger.error("Final sync error: %s", e)
        
        if self.pool:
            await self.pool.close()


# Global sync instance
sync = NeonSync()
