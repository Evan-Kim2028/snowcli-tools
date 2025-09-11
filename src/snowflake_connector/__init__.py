"""Snowflake Connector - Efficient database operations with parallel execution.

A Python package providing CLI tools and APIs for Snowflake database operations,
featuring connection pooling, parallel query execution, and comprehensive error handling.
"""

from .config import Config
from .connection import execute_query_to_dataframe, get_snowflake_connection
from .parallel import ParallelQueryExecutor, query_multiple_objects

__version__ = "0.1.0"
__all__ = [
    "get_snowflake_connection",
    "execute_query_to_dataframe",
    "ParallelQueryExecutor",
    "query_multiple_objects",
    "Config",
]
