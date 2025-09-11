"""Compatibility shim for the old package name `snowflake_connector`.

Please import from `snowcli_tools` going forward.
"""

from warnings import warn

from snowcli_tools import (
    Config,
    ParallelQueryConfig,
    ParallelQueryExecutor,
    SnowCLI,
    get_config,
    query_multiple_objects,
    set_config,
)

warn(
    "`snowflake_connector` is deprecated; use `snowcli_tools` instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "SnowCLI",
    "ParallelQueryConfig",
    "ParallelQueryExecutor",
    "query_multiple_objects",
    "Config",
    "get_config",
    "set_config",
]
