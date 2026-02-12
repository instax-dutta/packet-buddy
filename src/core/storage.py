"""SQLite storage layer for local data persistence."""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from contextlib import contextmanager

from ..utils.config import config
from .device import get_device_info


class Storage:
    """Local SQLite storage manager."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self.device_id, self.os_type, self.hostname = get_device_info()
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    os_type TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Usage logs (raw per-second data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    bytes_sent INTEGER NOT NULL,
                    bytes_received INTEGER NOT NULL,
                    synced BOOLEAN DEFAULT 0,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Create index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp 
                ON usage_logs(device_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_usage_logs_synced 
                ON usage_logs(synced) WHERE synced = 0
            """)
            
            # Daily aggregates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_aggregates (
                    device_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    bytes_sent INTEGER NOT NULL,
                    bytes_received INTEGER NOT NULL,
                    peak_speed INTEGER DEFAULT 0,
                    PRIMARY KEY (device_id, date),
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)

            # Migration: Add peak_speed if it doesn't exist (for existing databases)
            try:
                cursor.execute("ALTER TABLE daily_aggregates ADD COLUMN peak_speed INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # Already exists
            
            # Monthly aggregates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_aggregates (
                    device_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    bytes_sent INTEGER NOT NULL,
                    bytes_received INTEGER NOT NULL,
                    PRIMARY KEY (device_id, month),
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Sync cursor
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_cursor (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)

            # System state (for tracking absolute counters across restarts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value_text TEXT,
                    value_int INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Register this device
            cursor.execute("""
                INSERT OR REPLACE INTO devices (device_id, os_type, hostname)
                VALUES (?, ?, ?)
            """, (self.device_id, self.os_type, self.hostname))
    
    def insert_usage(self, bytes_sent: int, bytes_received: int, timestamp: Optional[datetime] = None, speed: int = 0):
        """Insert a usage log entry."""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usage_logs (device_id, timestamp, bytes_sent, bytes_received)
                VALUES (?, ?, ?, ?)
            """, (self.device_id, timestamp, bytes_sent, bytes_received))
            
            # Update daily aggregate
            today = timestamp.date()
            cursor.execute("""
                INSERT INTO daily_aggregates (device_id, date, bytes_sent, bytes_received, peak_speed)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(device_id, date) DO UPDATE SET
                    bytes_sent = bytes_sent + excluded.bytes_sent,
                    bytes_received = bytes_received + excluded.bytes_received,
                    peak_speed = MAX(peak_speed, excluded.peak_speed)
            """, (self.device_id, today, bytes_sent, bytes_received, speed))
            
            # Update monthly aggregate
            month = timestamp.strftime("%Y-%m")
            cursor.execute("""
                INSERT INTO monthly_aggregates (device_id, month, bytes_sent, bytes_received)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_id, month) DO UPDATE SET
                    bytes_sent = bytes_sent + excluded.bytes_sent,
                    bytes_received = bytes_received + excluded.bytes_received
            """, (self.device_id, month, bytes_sent, bytes_received))
    
    def get_unsynced_logs(self, limit: int = 1000) -> List[Dict]:
        """Get unsynced usage logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, device_id, timestamp, bytes_sent, bytes_received
                FROM usage_logs
                WHERE synced = 0
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_logs_synced(self, log_ids: List[int]):
        """Mark logs as synced."""
        if not log_ids:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(log_ids))
            cursor.execute(f"""
                UPDATE usage_logs
                SET synced = 1
                WHERE id IN ({placeholders})
            """, log_ids)
    
    def get_today_usage(self) -> Tuple[int, int, int]:
        """Get today's total usage and peak speed (sent, received, peak)."""
        today = date.today()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bytes_sent, bytes_received, peak_speed
                FROM daily_aggregates
                WHERE device_id = ? AND date = ?
            """, (self.device_id, today))
            
            row = cursor.fetchone()
            if row:
                return row["bytes_sent"], row["bytes_received"], row["peak_speed"]
            return 0, 0, 0
    
    def get_month_usage(self, month: str) -> List[Dict]:
        """Get daily breakdown for a specific month (YYYY-MM)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, bytes_sent, bytes_received
                FROM daily_aggregates
                WHERE device_id = ? AND strftime('%Y-%m', date) = ?
                ORDER BY date ASC
            """, (self.device_id, month))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_range_usage(self, from_date: date, to_date: date) -> List[Dict]:
        """Get usage for a date range."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, bytes_sent, bytes_received
                FROM daily_aggregates
                WHERE device_id = ? AND date BETWEEN ? AND ?
                ORDER BY date ASC
            """, (self.device_id, from_date, to_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_lifetime_usage(self) -> Tuple[int, int]:
        """Get total lifetime usage."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(bytes_sent), 0) as total_sent,
                    COALESCE(SUM(bytes_received), 0) as total_received
                FROM daily_aggregates
                WHERE device_id = ?
            """, (self.device_id,))
            
            row = cursor.fetchone()
            return row["total_sent"], row["total_received"]
    
    def get_all_usage_logs(self) -> List[Dict]:
        """Get all usage logs for export."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, bytes_sent, bytes_received
                FROM usage_logs
                WHERE device_id = ?
                ORDER BY timestamp ASC
            """, (self.device_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_daily_aggregates(self) -> List[Dict]:
        """Get all daily aggregates with peak speeds for comprehensive exports."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, bytes_sent, bytes_received, peak_speed
                FROM daily_aggregates
                WHERE device_id = ?
                ORDER BY date ASC
            """, (self.device_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_summaries(self) -> List[Dict]:
        """Get monthly summaries for year wrap-up."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', date) as month,
                    SUM(bytes_sent) as bytes_sent,
                    SUM(bytes_received) as bytes_received,
                    MAX(peak_speed) as peak_speed,
                    COUNT(*) as days_tracked
                FROM daily_aggregates
                WHERE device_id = ?
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month ASC
            """, (self.device_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_overall_peak_speed(self) -> int:
        """Get the highest peak speed ever recorded."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(peak_speed) as max_peak
                FROM daily_aggregates
                WHERE device_id = ?
            """, (self.device_id,))
            
            row = cursor.fetchone()
            return row["max_peak"] if row and row["max_peak"] else 0
    
    def get_tracking_stats(self) -> Dict:
        """Get overall tracking statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    MIN(date) as first_tracked_date,
                    MAX(date) as last_tracked_date,
                    COUNT(DISTINCT date) as total_days_tracked
                FROM daily_aggregates
                WHERE device_id = ?
            """, (self.device_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_state(self, key: str) -> Dict:
        """Get a value from system_state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value_text, value_int FROM system_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def set_state(self, key: str, value_text: Optional[str] = None, value_int: Optional[int] = None):
        """Set a value in system_state."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_state (key, value_text, value_int, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value_text, value_int))


# Global storage instance
storage = Storage()
