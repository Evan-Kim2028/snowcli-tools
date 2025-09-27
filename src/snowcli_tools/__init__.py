"""snowcli-tools — Snowflake CLI-based tools with parallel execution."""

from .catalog import build_catalog
from .config import Config, get_config, set_config
from .parallel import ParallelQueryConfig, ParallelQueryExecutor, query_multiple_objects
from .snow_cli import SnowCLI

__version__ = "1.4.4"
__all__ = [
    "SnowCLI",
    "ParallelQueryConfig",
    "ParallelQueryExecutor",
    "query_multiple_objects",
    "build_catalog",
    "Config",
    "get_config",
    "set_config",
]
