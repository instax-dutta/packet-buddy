"""Configuration management for PacketBuddy."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import tomli


@dataclass
class NeonStorageConfig:
    """NeonDB-specific storage configuration for free tier limits."""
    neon_log_retention_days: int = 7
    neon_aggregate_retention_months: int = 3
    neon_max_storage_mb: int = 450
    neon_storage_warning_threshold: int = 80
    neon_cleanup_on_sync: bool = True


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
                "log_retention_days": 30,
                "aggregate_retention_months": 12,
                "cleanup_interval_hours": 24,
                "vacuum_after_cleanup": True,
                "max_storage_mb": 400,
                "neon": {
                    "log_retention_days": 7,
                    "aggregate_retention_months": 3,
                    "max_storage_mb": 450,
                    "warning_threshold_percent": 80,
                    "cleanup_on_sync": True,
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
        """Load storage configuration from config dict."""
        storage_cfg = self.config.get("storage", {})
        neon_cfg = storage_cfg.get("neon", {})
        neon_config = NeonStorageConfig(
            neon_log_retention_days=neon_cfg.get("log_retention_days", 7),
            neon_aggregate_retention_months=neon_cfg.get("aggregate_retention_months", 3),
            neon_max_storage_mb=neon_cfg.get("max_storage_mb", 450),
            neon_storage_warning_threshold=neon_cfg.get("warning_threshold_percent", 80),
            neon_cleanup_on_sync=neon_cfg.get("cleanup_on_sync", True),
        )
        return StorageConfig(
            log_retention_days=storage_cfg.get("log_retention_days", 30),
            aggregate_retention_months=storage_cfg.get("aggregate_retention_months", 12),
            cleanup_interval_hours=storage_cfg.get("cleanup_interval_hours", 24),
            vacuum_after_cleanup=storage_cfg.get("vacuum_after_cleanup", True),
            max_storage_mb=storage_cfg.get("max_storage_mb", 400),
            neon=neon_config,
        )
    
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
