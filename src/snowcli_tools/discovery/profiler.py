"""
TableProfiler - SQL-based table profiling.

Profiles Snowflake tables using pure SQL queries to extract:
- Column statistics (null%, cardinality, min/max, avg_length)
- Pattern detection (email, UUID, phone, URL, dates)
- Sample data (configurable limit)
- Large table optimizations (sampling, APPROX_COUNT_DISTINCT)
"""

import re
from datetime import datetime
from typing import Any, Optional

from snowcli_tools.discovery.models import ColumnProfile, TableProfile
from snowcli_tools.discovery.utils import build_qualified_table_name, parse_table_name
from snowcli_tools.snow_cli import SnowCLI


def _validate_snowflake_identifier(
    identifier: str, identifier_type: str = "identifier"
) -> None:
    """
    Validate Snowflake identifier against SQL injection.

    Snowflake identifiers must:
    - Start with letter or underscore
    - Contain only letters, digits, underscores, and dollar signs
    - Be 1-255 characters long

    Args:
        identifier: The identifier to validate
        identifier_type: Type description for error messages (e.g., "database", "table")

    Raises:
        ValueError: If identifier is invalid or potentially malicious
    """
    if not identifier:
        raise ValueError(f"Empty {identifier_type} name")

    # Snowflake unquoted identifier pattern
    # Allows: A-Z, a-z, 0-9, _, $ (but cannot start with digit)
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}$", identifier):
        raise ValueError(
            f"Invalid Snowflake {identifier_type}: '{identifier}'. "
            f"Must start with letter/underscore and contain only alphanumeric, _, or $"
        )


class TableProfiler:
    """Profile Snowflake tables using SQL queries."""

    # Constants
    DEFAULT_SAMPLE_SIZE = 100  # Default number of sample rows to extract
    MAX_SAMPLE_SIZE_FOR_PATTERN = 100  # Max sample size for pattern detection
    PATTERN_MATCH_THRESHOLD = 0.8  # 80%+ match rate to consider a pattern
    LARGE_TABLE_THRESHOLD = 100_000  # Use APPROX_COUNT_DISTINCT for tables > this size
    MAX_SAMPLE_VALUES = 10  # Max sample values to store per column

    # Pattern detection regexes
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        "phone": r"^\+?[\d\s\-\(\)]{10,}$",
        "url": r"^https?://[^\s]+$",
    }

    def __init__(
        self,
        snow_cli: SnowCLI,
        sample_size: int = 100,
        use_approx_count: bool = True,
        timeout_seconds: int = 30,
    ):
        """
        Initialize TableProfiler.

        Args:
            snow_cli: SnowCLI instance for executing queries
            sample_size: Number of sample rows to extract (default: 100)
            use_approx_count: Use APPROX_COUNT_DISTINCT for large tables (default: True)
            timeout_seconds: Query timeout in seconds (default: 30)
        """
        self.snow_cli = snow_cli
        self.sample_size = sample_size
        self.use_approx_count = use_approx_count
        self.timeout_seconds = timeout_seconds

    def _execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute SQL query and return results as list of dictionaries.

        Wrapper around SnowCLI.run_query that handles parsing.
        """
        result = self.snow_cli.run_query(sql, output_format="json")
        if result.rows:
            return result.rows
        return []

    def profile_table(
        self,
        table_name: str,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> TableProfile:
        """
        Profile a Snowflake table.

        Args:
            table_name: Table name
            database: Database name (optional, uses session default)
            schema: Schema name (optional, uses session default)

        Returns:
            TableProfile with complete statistical analysis

        Raises:
            ValueError: If table doesn't exist or invalid identifiers
        """
        start_time = datetime.now()

        # Parse table name (SQL injection prevention)
        db, sch, tbl = parse_table_name(table_name, database, schema)

        # Validate all identifiers against SQL injection
        if db:
            _validate_snowflake_identifier(db, "database")
        if sch:
            _validate_snowflake_identifier(sch, "schema")
        _validate_snowflake_identifier(tbl, "table")

        # Build qualified table name with proper quoting
        full_table = build_qualified_table_name(db, sch, tbl)

        # Get table metadata
        row_count = self._get_row_count(full_table)
        last_ddl = self._get_last_ddl(db, sch, tbl) if db and sch else None

        # Get column information from INFORMATION_SCHEMA
        columns_info = self._get_columns_info(db, sch, tbl)

        if not columns_info:
            raise ValueError(f"Table not found or no columns: {table_name}")

        # Profile each column (CRITICAL: avoid CROSS JOIN)
        column_profiles = self._profile_columns(full_table, columns_info, row_count)

        # Get sample rows
        sample_rows = self._get_sample_rows(full_table)

        end_time = datetime.now()
        profiling_time = (end_time - start_time).total_seconds()

        return TableProfile(
            database=db,
            schema=sch,
            table_name=tbl,
            row_count=row_count,
            columns=column_profiles,
            sample_rows=sample_rows,
            profiling_time_seconds=profiling_time,
            last_ddl=last_ddl,
        )

    def _get_row_count(self, full_table: str) -> int:
        """Get approximate row count."""
        sql = f"SELECT COUNT(*) as cnt FROM {full_table}"
        result = self._execute_query(sql)
        return int(result[0]["CNT"])

    def _get_last_ddl(self, database: str, schema: str, table: str) -> Optional[str]:
        """Get LAST_DDL timestamp from INFORMATION_SCHEMA."""
        if not database or not schema:
            return None

        # Escape single quotes for SQL injection prevention
        safe_schema = schema.replace("'", "''")
        safe_table = table.replace("'", "''")

        sql = f"""
            SELECT LAST_DDL
            FROM "{database}".INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{safe_schema}'
              AND TABLE_NAME = '{safe_table}'
        """
        result = self._execute_query(sql)
        if result and result[0].get("LAST_DDL"):
            last_ddl = result[0]["LAST_DDL"]
            # Handle datetime object
            if isinstance(last_ddl, datetime):
                return last_ddl.isoformat()
            return str(last_ddl)
        return None

    def _get_columns_info(self, database: str, schema: str, table: str) -> list[dict]:
        """Get column metadata from INFORMATION_SCHEMA."""
        # Escape single quotes for SQL injection prevention
        safe_table = table.replace("'", "''")

        # Need to handle case where database/schema might not be provided
        if database and schema:
            safe_schema = schema.replace("'", "''")
            sql = f"""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    ORDINAL_POSITION
                FROM "{database}".INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{safe_schema}'
                  AND TABLE_NAME = '{safe_table}'
                ORDER BY ORDINAL_POSITION
            """
        else:
            # Use CURRENT_DATABASE() and CURRENT_SCHEMA()
            # First check if session defaults are set
            try:
                check_sql = (
                    "SELECT CURRENT_SCHEMA() as schema, CURRENT_DATABASE() as db"
                )
                check_result = self._execute_query(check_sql)
                if not check_result or not check_result[0].get("SCHEMA"):
                    raise ValueError(
                        "No schema specified and CURRENT_SCHEMA() is NULL. "
                        "Please specify database and schema explicitly or set session defaults."
                    )
            except Exception as e:
                raise ValueError(
                    f"Failed to check session defaults: {e}. Please specify database and schema explicitly."
                )

            sql = f"""
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
                  AND TABLE_NAME = '{safe_table}'
                ORDER BY ORDINAL_POSITION
            """

        return self._execute_query(sql)

    def _profile_columns(
        self, full_table: str, columns_info: list[dict], row_count: int
    ) -> list[ColumnProfile]:
        """
        Profile all columns efficiently.

        CRITICAL FIX: Use per-column queries with UNION instead of CROSS JOIN.

        Original (WRONG):
            SELECT column_name, COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS c
            CROSS JOIN {table}  # Creates cartesian product!

        Fixed (CORRECT):
            Use UNION of per-column queries
        """
        if not columns_info:
            return []

        # Get sample data first for pattern detection
        sample_sql = f"SELECT * FROM {full_table} LIMIT {min(self.sample_size, self.MAX_SAMPLE_SIZE_FOR_PATTERN)}"
        try:
            sample_data = self._execute_query(sample_sql)
        except Exception:
            sample_data = []

        column_profiles = []

        # Build per-column statistics queries
        for col_info in columns_info:
            col_name = col_info["COLUMN_NAME"]
            data_type = col_info["DATA_TYPE"]

            # Use APPROX_COUNT_DISTINCT for large tables
            if self.use_approx_count and row_count > self.LARGE_TABLE_THRESHOLD:
                cardinality_fn = "APPROX_COUNT_DISTINCT"
            else:
                cardinality_fn = "COUNT(DISTINCT"

            # Build query for this column
            # Note: We need to handle different data types appropriately
            if "VARCHAR" in data_type or "TEXT" in data_type or "STRING" in data_type:
                # String columns - can calculate length
                stats_query = f"""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT("{col_name}") as non_null_count,
                        {cardinality_fn}("{col_name}") as cardinality,
                        MIN(LENGTH("{col_name}")) as min_len,
                        MAX(LENGTH("{col_name}")) as max_len,
                        AVG(LENGTH("{col_name}")) as avg_len
                    FROM {full_table}
                """
            else:
                # Non-string columns - no length calculation
                stats_query = f"""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT("{col_name}") as non_null_count,
                        {cardinality_fn}("{col_name}") as cardinality,
                        NULL as min_len,
                        NULL as max_len,
                        NULL as avg_len
                    FROM {full_table}
                """

            try:
                stats_result = self._execute_query(stats_query)
                stats = stats_result[0] if stats_result else {}
            except Exception:
                # If query fails, use defaults
                stats = {
                    "TOTAL_ROWS": row_count,
                    "NON_NULL_COUNT": 0,
                    "CARDINALITY": 0,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }

            total_rows = int(stats.get("TOTAL_ROWS", row_count))
            non_null = int(stats.get("NON_NULL_COUNT", 0))
            cardinality = int(stats.get("CARDINALITY", 0))
            avg_len = (
                float(stats.get("AVG_LEN"))
                if stats.get("AVG_LEN") is not None
                else None
            )

            # Calculate null percentage
            null_pct = (
                ((total_rows - non_null) / total_rows * 100) if total_rows > 0 else 0
            )

            # Extract sample values from sample data
            sample_values = [
                row.get(col_name)
                for row in sample_data
                if row.get(col_name) is not None
            ][: self.MAX_SAMPLE_VALUES]

            # Detect patterns
            pattern = self._detect_pattern(sample_values, data_type)

            column_profiles.append(
                ColumnProfile(
                    name=col_name,
                    data_type=data_type,
                    null_percentage=round(null_pct, 2),
                    cardinality=cardinality,
                    pattern=pattern,
                    sample_values=sample_values,
                    avg_length=round(avg_len, 2) if avg_len is not None else None,
                )
            )

        return column_profiles

    def _detect_pattern(
        self, sample_values: list[Any], data_type: str
    ) -> Optional[str]:
        """
        Detect common patterns in column values.

        Returns:
            Pattern name ("email", "uuid", "phone", "url") or None
        """
        if not sample_values or not any(
            dtype in data_type.upper()
            for dtype in ["VARCHAR", "TEXT", "STRING", "CHAR"]
        ):
            return None

        # Convert to strings
        str_values = [str(v) for v in sample_values if v is not None]
        if not str_values:
            return None

        # Check each pattern
        for pattern_name, pattern_regex in self.PATTERNS.items():
            matches = sum(
                1 for v in str_values if re.match(pattern_regex, v, re.IGNORECASE)
            )
            match_rate = matches / len(str_values)

            # If threshold match rate met, consider it that pattern
            if match_rate >= self.PATTERN_MATCH_THRESHOLD:
                return pattern_name

        return None

    def _get_sample_rows(self, full_table: str) -> list[dict[str, Any]]:
        """Get sample rows from table."""
        sql = f"SELECT * FROM {full_table} LIMIT {self.sample_size}"
        try:
            return self._execute_query(sql)
        except Exception:
            return []
