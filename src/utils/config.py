"""Configuration management for PacketBuddy."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import tomli


@dataclass
class NeonStorageConfig:
    """NeonDB-specific storage configuration for free tier limits.

    Free tier hard limits: 0.5 GB storage, 100 CU-hours/month, 5 GB egress.
    Raw usage_logs are no longer synced to NeonDB (saves 90%+ storage).
    Only aggregates (daily + monthly) are stored remotely — ~0.01% the data volume.
    """
    neon_log_retention_days: int = 1
    neon_aggregate_retention_months: int = 6
    neon_max_storage_mb: int = 450
    neon_storage_warning_threshold: int = 70
    neon_cleanup_on_sync: bool = False


@dataclass
class StorageConfig:
    """Storage retention configuration."""
    log_retention_days: int = 30
    aggregate_retention_months: int = 12
    cleanup_interval_hours: int = 24
    vacuum_after_cleanup: bool = True
    max_storage_mb: int = 400
    neon: NeonStorageConfig = field(default_factory=NeonStorageConfig)


class Config:
    """Global configuration manager."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.app_dir = Path.home() / ".packetbuddy"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = config_path or self.app_dir / "config.toml"
        self.db_path = self.app_dir / "packetbuddy.db"
        self.device_id_path = self.app_dir / "device_id"
        
        self.config = self._load_config()
        self.storage = self._load_storage_config()
        
    def _load_config(self) -> dict:
        """Load configuration from TOML file or use defaults."""
        default_config = {
            "monitoring": {
                "poll_interval": 1,  # seconds
                "batch_write_interval": 30,  # seconds (optimized for resource efficiency)
                "max_delta_bytes": 1_000_000_000,  # 1GB/s threshold for anomaly detection
            },
            "sync": {
                "enabled": True,
                "interval": 300,  # seconds (5 mins for Neon DB scaling)
                "retry_delay": 5,  # seconds
                "max_retries": 3,
            },
            "api": {
                "host": "127.0.0.1",
                "port": 7373,
                "cors_enabled": True,
            },
            "database": {
                "neon_url": os.getenv("NEON_DB_URL", ""),
                "pool_size": 5,
            },
            "auto_update": {
                "enabled": True,
                "check_on_startup": True,
                "auto_apply": True,
                "auto_restart": True,
            },
            "storage": {
                "log_retention_days": 7,
                "aggregate_retention_months": 12,
                "cleanup_interval_hours": 24,
                "vacuum_after_cleanup": True,
                "max_storage_mb": 400,
                "neon": {
                    "log_retention_days": 1,
                    "aggregate_retention_months": 6,
                    "max_storage_mb": 450,
                    "warning_threshold_percent": 70,
                    "cleanup_on_sync": False,
                },
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                user_config = tomli.load(f)
                # Merge user config with defaults
                self._deep_merge(default_config, user_config)
        
        return default_config
    
    def _load_storage_config(self) -> StorageConfig:
        """Load storage configuration from config dict.

        Uses dataclass defaults as the SSOT, then overrides from config file.
        This ensures free-tier-optimized defaults are always in effect.
        """
        storage_cfg = self.config.get("storage", {})
        neon_cfg = storage_cfg.get("neon", {})

        neon_config = NeonStorageConfig()
        for field in ("log_retention_days", "aggregate_retention_months", "max_storage_mb", "warning_threshold_percent", "cleanup_on_sync"):
            if field in neon_cfg:
                setattr(neon_config, f"neon_{field}", neon_cfg[field])

        storage_config = StorageConfig()
        for field in ("log_retention_days", "aggregate_retention_months", "cleanup_interval_hours", "vacuum_after_cleanup", "max_storage_mb"):
            if field in storage_cfg:
                setattr(storage_config, field, storage_cfg[field])
        storage_config.neon = neon_config
        return storage_config
    
    def _deep_merge(self, base: dict, overlay: dict) -> None:
        """Deep merge overlay into base dict."""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys, default=None):
        """Get nested config value using dot notation."""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    @property
    def neon_db_url(self) -> str:
        """Get NeonDB URL from config or environment."""
        return os.getenv("NEON_DB_URL") or self.get("database", "neon_url", default="")
    
    @property
    def sync_enabled(self) -> bool:
        """Check if cloud sync is enabled."""
        return self.get("sync", "enabled", default=True) and bool(self.neon_db_url)


# Global config instance
config = Config()
