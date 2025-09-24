"""Utility functions and fixes for advanced lineage features."""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Set

import networkx as nx


def validate_object_name(name: str) -> bool:
    """Validate Snowflake object name format."""
    if not name:
        return False

    # Basic validation for Snowflake naming
    pattern = r'^[A-Za-z_][A-Za-z0-9_$.]*$'
    parts = name.split('.')

    for part in parts:
        if not re.match(pattern, part.strip('"')):
            return False

    return True


def validate_path(path: Path, must_exist: bool = False, create_if_missing: bool = False) -> bool:
    """Validate file system path with optional creation."""
    try:
        path = Path(path)

        if must_exist and not path.exists():
            if create_if_missing and path.suffix == '':  # It's a directory
                path.mkdir(parents=True, exist_ok=True)
                return True
            return False

        # Check write permissions for parent directory
        parent = path.parent
        if not parent.exists() and create_if_missing:
            parent.mkdir(parents=True, exist_ok=True)

        if parent.exists():
            # Test write permission
            test_file = parent / '.write_test'
            try:
                test_file.touch()
                test_file.unlink()
                return True
            except (OSError, PermissionError):
                return False

        return True

    except (OSError, ValueError):
        return False


def safe_file_write(path: Path, content: str | bytes, mode: str = 'w') -> bool:
    """Safely write to file with atomic operations."""
    try:
        path = Path(path)
        temp_path = path.with_suffix(path.suffix + '.tmp')

        # Write to temporary file
        if isinstance(content, bytes):
            temp_path.write_bytes(content)
        else:
            temp_path.write_text(content)

        # Atomic rename
        temp_path.replace(path)
        return True

    except (OSError, IOError) as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        return False


@contextmanager
def safe_db_connection(db_path: Path) -> Generator:
    """Context manager for safe SQLite connections."""
    import sqlite3

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def networkx_descendants_at_distance(graph: nx.DiGraph, source: str, distance: int) -> Set[str]:
    """Get all descendants at a specific distance or less from source node."""
    if source not in graph:
        return set()

    descendants = set()
    current_level = {source}

    for d in range(1, distance + 1):
        next_level = set()
        for node in current_level:
            for successor in graph.successors(node):
                next_level.add(successor)
                descendants.add(successor)
        current_level = next_level

        if not current_level:  # No more descendants at this level
            break

    return descendants


def safe_sql_parse(sql: str, dialect: str = "snowflake") -> Optional[Any]:
    """Safely parse SQL with better error handling."""
    import sqlglot
    from sqlglot.errors import ParseError, ErrorLevel

    if not sql or not sql.strip():
        return None

    try:
        # Handle multi-statement SQL
        statements = sqlglot.parse(sql, read=dialect, error_level=ErrorLevel.WARN)

        # Filter out None results
        valid_statements = [stmt for stmt in statements if stmt is not None]

        if not valid_statements:
            return None

        # Return first statement for single-statement expectation
        # Or return all for multi-statement handling
        return valid_statements[0] if len(valid_statements) == 1 else valid_statements

    except ParseError as e:
        # Log the parse error but don't raise
        import logging
        logging.warning(f"SQL parse error: {e}")
        return None
    except Exception as e:
        # Unexpected error - log but don't crash
        import logging
        logging.error(f"Unexpected error parsing SQL: {e}")
        return None


def clean_old_snapshots(storage_path: Path, keep_count: int = 100, keep_days: int = 90):
    """Clean up old snapshot files to prevent unbounded growth."""
    from datetime import datetime, timedelta
    import json

    storage_path = Path(storage_path)
    if not storage_path.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=keep_days)
    graph_files = list(storage_path.glob("graph_*.json"))

    # Sort by modification time
    graph_files.sort(key=lambda f: f.stat().st_mtime)

    # Keep minimum number of files
    if len(graph_files) <= keep_count:
        return

    # Remove old files
    for graph_file in graph_files[:-keep_count]:
        try:
            # Check if it's older than cutoff
            mtime = datetime.fromtimestamp(graph_file.stat().st_mtime)
            if mtime < cutoff_date:
                graph_file.unlink()
        except (OSError, IOError):
            pass


def validate_sql_injection(value: str) -> bool:
    """Basic SQL injection prevention check."""
    dangerous_patterns = [
        r';\s*(DROP|DELETE|TRUNCATE|ALTER|CREATE)\s+',
        r'--[^\n]*$',
        r'/\*.*\*/',
        r'(UNION\s+ALL|UNION\s+SELECT)',
        r'(OR\s+1\s*=\s*1|AND\s+1\s*=\s*1)',
    ]

    value_upper = value.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_upper):
            return False

    return True


def get_cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    import hashlib

    key_parts = []
    for arg in args:
        if arg is None:
            key_parts.append("None")
        elif isinstance(arg, (list, tuple)):
            key_parts.append(str(sorted(arg)))
        elif isinstance(arg, dict):
            key_parts.append(str(sorted(arg.items())))
        else:
            key_parts.append(str(arg))

    combined = "|".join(key_parts)
    return hashlib.md5(combined.encode()).hexdigest()


class LRUCache:
    """Simple LRU cache implementation for SQL parsing results."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: list = []

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def put(self, key: str, value: Any):
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]

        self.cache[key] = value
        self.access_order.append(key)

    def clear(self):
        self.cache.clear()
        self.access_order.clear()


# Global SQL parse cache
_sql_parse_cache = LRUCache(max_size=500)


def cached_sql_parse(sql: str, dialect: str = "snowflake") -> Optional[Any]:
    """Parse SQL with caching."""
    cache_key = get_cache_key(sql, dialect)

    cached_result = _sql_parse_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = safe_sql_parse(sql, dialect)
    if result is not None:
        _sql_parse_cache.put(cache_key, result)

    return result