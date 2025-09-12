"""Configuration management for SNOWCLI-TOOLS.

This module does not handle authentication or secrets. It simply tracks the
profile name and optional context (warehouse, database, schema, role) used
when shelling out to the official `snow` CLI (`snow`).

Notes:
- Profiles are created and managed by the `snow` CLI and stored in the
  Snowflake CLI config (location varies by OS; e.g., on macOS:
  `~/Library/Application Support/snowflake/config.toml`).
- Profile selection follows typical precedence: explicit CLI flag, then
  `SNOWFLAKE_PROFILE` env var, then the default profile in the `snow` config.
"""

import os
from dataclasses import dataclass
from typing import Optional

import yaml  # type: ignore[import-untyped]


@dataclass
class SnowflakeConfig:
    """Snowflake connection context driven by Snowflake CLI.

    - `profile` should match a profile configured in the Snowflake CLI config.
    - Optional context overrides are passed to `snow sql` (warehouse, database,
      schema, role).
    """

    profile: str = "default"
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None


@dataclass
class Config:
    """Main configuration class for snowflake-cli-tools-py."""

    snowflake: SnowflakeConfig
    max_concurrent_queries: int = 5
    connection_pool_size: int = 10
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 300
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        snowflake_config = SnowflakeConfig(
            profile=os.getenv("SNOWFLAKE_PROFILE", "default"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE") or None,
            database=os.getenv("SNOWFLAKE_DATABASE") or None,
            schema=os.getenv("SNOWFLAKE_SCHEMA") or None,
            role=os.getenv("SNOWFLAKE_ROLE") or None,
        )

        return cls(
            snowflake=snowflake_config,
            max_concurrent_queries=int(os.getenv("MAX_CONCURRENT_QUERIES", "5")),
            connection_pool_size=int(os.getenv("CONNECTION_POOL_SIZE", "10")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "300")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """Create configuration from YAML file."""
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        snowflake_data = data.get("snowflake", {})
        snowflake_config = SnowflakeConfig(
            profile=snowflake_data.get("profile", "default"),
            warehouse=snowflake_data.get("warehouse"),
            database=snowflake_data.get("database"),
            schema=snowflake_data.get("schema"),
            role=snowflake_data.get("role"),
        )

        return cls(
            snowflake=snowflake_config,
            max_concurrent_queries=data.get("max_concurrent_queries", 5),
            connection_pool_size=data.get("connection_pool_size", 10),
            retry_attempts=data.get("retry_attempts", 3),
            retry_delay=data.get("retry_delay", 1.0),
            timeout_seconds=data.get("timeout_seconds", 300),
            log_level=data.get("log_level", "INFO"),
        )

    def save_to_yaml(self, config_path: str) -> None:
        """Save configuration to YAML file."""
        config_dict = {
            "snowflake": {
                "profile": self.snowflake.profile,
                "warehouse": self.snowflake.warehouse,
                "database": self.snowflake.database,
                "schema": self.snowflake.schema,
                "role": self.snowflake.role,
            },
            "max_concurrent_queries": self.max_concurrent_queries,
            "connection_pool_size": self.connection_pool_size,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "timeout_seconds": self.timeout_seconds,
            "log_level": self.log_level,
        }

        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
