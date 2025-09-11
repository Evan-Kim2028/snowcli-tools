"""Configuration management for Snowflake Connector."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SnowflakeConfig:
    """Configuration for Snowflake connection parameters."""

    account: str
    user: str
    private_key_path: str
    warehouse: str
    database: str
    schema: str
    role: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert config to dictionary for Snowflake connector."""
        from .connection import load_private_key

        return {
            "account": self.account,
            "user": self.user,
            "private_key": load_private_key(self.private_key_path),
            "warehouse": self.warehouse,
            "database": self.database,
            "schema": self.schema,
            "role": self.role,
        }


@dataclass
class Config:
    """Main configuration class for Snowflake Connector."""

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
        # Get private key path from env or use default
        private_key_path = os.getenv(
            "SNOWFLAKE_PRIVATE_KEY_PATH",
            str(Path.home() / "Documents" / "snowflake_keys" / "rsa_key.p8"),
        )

        # Expand ~ and relative paths
        private_key_path = os.path.expanduser(private_key_path)
        private_key_path = os.path.abspath(private_key_path)

        snowflake_config = SnowflakeConfig(
            account=os.getenv("SNOWFLAKE_ACCOUNT", "HKB47976.us-west-2"),
            user=os.getenv("SNOWFLAKE_USER", "readonly_ai_user"),
            private_key_path=private_key_path,
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "EVANS_AI_WH"),
            database=os.getenv("SNOWFLAKE_DATABASE", "PIPELINE_V2_GROOT_DB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "PIPELINE_V2_GROOT_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE"),
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
            account=snowflake_data.get("account", "HKB47976.us-west-2"),
            user=snowflake_data.get("user", "readonly_ai_user"),
            private_key_path=snowflake_data.get(
                "private_key_path",
                str(Path.home() / "Documents" / "snowflake_keys" / "rsa_key.p8"),
            ),
            warehouse=snowflake_data.get("warehouse", "EVANS_AI_WH"),
            database=snowflake_data.get("database", "PIPELINE_V2_GROOT_DB"),
            schema=snowflake_data.get("schema", "PIPELINE_V2_GROOT_SCHEMA"),
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
                "account": self.snowflake.account,
                "user": self.snowflake.user,
                "private_key_path": self.snowflake.private_key_path,
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
