"""
Shared utilities for Discovery Assistant.

Common functions used across discovery components.
"""

import re
from typing import Optional


def parse_and_quote_identifier(identifier: str) -> str:
    """
    Parse and quote a Snowflake identifier for safe SQL usage.

    Args:
        identifier: Snowflake identifier (table, column, database, schema name)

    Returns:
        Quoted identifier safe for SQL interpolation

    Raises:
        ValueError: If identifier contains invalid characters

    Examples:
        >>> parse_and_quote_identifier("CUSTOMERS")
        '"CUSTOMERS"'
        >>> parse_and_quote_identifier("my_table")
        '"my_table"'
    """
    # Validate identifier (alphanumeric, underscore only)
    if not identifier or not re.match(r"^[A-Za-z0-9_]+$", identifier):
        raise ValueError(f"Invalid Snowflake identifier: {identifier}")

    return f'"{identifier}"'


def parse_table_name(
    table_name: str, database: Optional[str] = None, schema: Optional[str] = None
) -> tuple[str, str, str]:
    """
    Parse table name and return (database, schema, table) tuple.

    Handles:
    - Fully qualified: "DATABASE.SCHEMA.TABLE"
    - Schema qualified: "SCHEMA.TABLE"
    - Simple: "TABLE"

    Args:
        table_name: Table name (may include database/schema)
        database: Explicit database (overrides parsed value)
        schema: Explicit schema (overrides parsed value)

    Returns:
        Tuple of (database, schema, table) all uppercase

    Raises:
        ValueError: If table_name is invalid or ambiguous

    Examples:
        >>> parse_table_name("CUSTOMERS")
        ('', '', 'CUSTOMERS')
        >>> parse_table_name("PUBLIC.CUSTOMERS")
        ('', 'PUBLIC', 'CUSTOMERS')
        >>> parse_table_name("DB.PUBLIC.CUSTOMERS")
        ('DB', 'PUBLIC', 'CUSTOMERS')
    """
    parts = table_name.upper().split(".")

    if len(parts) == 1:
        # Simple name: TABLE
        db = database.upper() if database else ""
        sch = schema.upper() if schema else ""
        tbl = parts[0]
    elif len(parts) == 2:
        # Schema qualified: SCHEMA.TABLE
        db = database.upper() if database else ""
        sch = schema.upper() if schema else parts[0]
        tbl = parts[1]
    elif len(parts) == 3:
        # Fully qualified: DATABASE.SCHEMA.TABLE
        db = database.upper() if database else parts[0]
        sch = schema.upper() if schema else parts[1]
        tbl = parts[2]
    else:
        raise ValueError(f"Invalid table name format: {table_name}")

    # Validate each part
    for part in [db, sch, tbl]:
        if part and not re.match(r"^[A-Za-z0-9_]+$", part):
            raise ValueError(f"Invalid identifier in table name: {part}")

    return db, sch, tbl


def build_qualified_table_name(database: str, schema: str, table: str) -> str:
    """
    Build fully qualified quoted table name for SQL.

    Args:
        database: Database name
        schema: Schema name
        table: Table name

    Returns:
        Quoted table identifier: "DATABASE"."SCHEMA"."TABLE"

    Examples:
        >>> build_qualified_table_name("DB", "PUBLIC", "CUSTOMERS")
        '"DB"."PUBLIC"."CUSTOMERS"'
    """
    quoted_db = parse_and_quote_identifier(database) if database else None
    quoted_schema = parse_and_quote_identifier(schema) if schema else None
    quoted_table = parse_and_quote_identifier(table)

    if quoted_db and quoted_schema:
        return f"{quoted_db}.{quoted_schema}.{quoted_table}"
    elif quoted_schema:
        return f"{quoted_schema}.{quoted_table}"
    else:
        return quoted_table


def detect_pii_by_name(column_name: str) -> bool:
    """
    Detect if column name suggests PII content.

    Uses common PII indicator keywords.

    Args:
        column_name: Column name to check

    Returns:
        True if column name suggests PII

    Examples:
        >>> detect_pii_by_name("EMAIL")
        True
        >>> detect_pii_by_name("CUSTOMER_NAME")
        True
        >>> detect_pii_by_name("PRODUCT_ID")
        False
    """
    pii_keywords = [
        "email",
        "phone",
        "ssn",
        "name",
        "address",
        "passport",
        "license",
        "credit_card",
        "dob",
        "birth",
        "patient",
        "medical",
        "salary",
        "wage",
    ]

    column_lower = column_name.lower()
    return any(keyword in column_lower for keyword in pii_keywords)


def calculate_confidence_level(confidence: float) -> str:
    """
    Map confidence score (0-1) to level (high/medium/low).

    Args:
        confidence: Confidence score between 0.0 and 1.0

    Returns:
        Confidence level: "high", "medium", or "low"

    Examples:
        >>> calculate_confidence_level(0.95)
        'high'
        >>> calculate_confidence_level(0.75)
        'medium'
        >>> calculate_confidence_level(0.45)
        'low'
    """
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.6:
        return "medium"
    else:
        return "low"
