"""Session management helpers for Snowflake connections."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional, Protocol, Union

_LOCK_ATTR = "_snowcli_session_lock"


class SnowflakeServiceProtocol(Protocol):
    """Protocol for objects that can have session locks attached."""

    pass


class CursorProtocol(Protocol):
    """Protocol for Snowflake cursor objects."""

    def execute(self, query: str) -> None: ...
    def fetchone(self) -> Union[Dict[str, Any], tuple, None]: ...


def ensure_session_lock(service: SnowflakeServiceProtocol) -> threading.Lock:
    """Return a lock attached to the Snowflake service instance."""
    lock = getattr(service, _LOCK_ATTR, None)
    if lock is None:
        lock = threading.Lock()
        setattr(service, _LOCK_ATTR, lock)
    return lock


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def snapshot_session(cursor: CursorProtocol) -> Dict[str, Optional[str]]:
    cursor.execute(
        "SELECT CURRENT_ROLE() AS ROLE, CURRENT_WAREHOUSE() AS WAREHOUSE, "
        "CURRENT_DATABASE() AS DATABASE, CURRENT_SCHEMA() AS SCHEMA"
    )
    row = cursor.fetchone()
    if isinstance(row, dict):
        return {
            "role": row.get("ROLE"),
            "warehouse": row.get("WAREHOUSE"),
            "database": row.get("DATABASE"),
            "schema": row.get("SCHEMA"),
        }
    return {
        "role": row[0] if len(row) > 0 else None,
        "warehouse": row[1] if len(row) > 1 else None,
        "database": row[2] if len(row) > 2 else None,
        "schema": row[3] if len(row) > 3 else None,
    }


def apply_session_context(cursor: CursorProtocol, overrides: Dict[str, str]) -> None:
    if role := overrides.get("role"):
        cursor.execute(f"USE ROLE {quote_identifier(role)}")
    if warehouse := overrides.get("warehouse"):
        cursor.execute(f"USE WAREHOUSE {quote_identifier(warehouse)}")
    if database := overrides.get("database"):
        cursor.execute(f"USE DATABASE {quote_identifier(database)}")
    if schema := overrides.get("schema"):
        cursor.execute(f"USE SCHEMA {quote_identifier(schema)}")


def restore_session_context(
    cursor: CursorProtocol, session: Dict[str, Optional[str]]
) -> None:
    role = session.get("role")
    warehouse = session.get("warehouse")
    database = session.get("database")
    schema = session.get("schema")

    if role:
        cursor.execute(f"USE ROLE {quote_identifier(role)}")
    if warehouse:
        cursor.execute(f"USE WAREHOUSE {quote_identifier(warehouse)}")
    if database:
        cursor.execute(f"USE DATABASE {quote_identifier(database)}")
    if schema:
        cursor.execute(f"USE SCHEMA {quote_identifier(schema)}")
