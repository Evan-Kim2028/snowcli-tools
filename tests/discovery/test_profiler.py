"""Tests for TableProfiler."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from snowcli_tools.discovery.models import TableProfile
from snowcli_tools.discovery.profiler import TableProfiler


@pytest.fixture
def mock_snow_cli():
    """Create a mock SnowCLI instance."""
    return Mock()


@pytest.fixture
def profiler(mock_snow_cli):
    """Create a TableProfiler instance with mock SnowCLI."""
    return TableProfiler(snow_cli=mock_snow_cli, sample_size=100)


class TestTableProfilerBasic:
    """Test basic TableProfiler functionality."""

    def test_profile_table_basic(self, profiler, mock_snow_cli):
        """Test basic table profiling."""
        # Mock responses
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 1000}],  # Row count
            None,  # LAST_DDL (optional, will return None)
            [  # Column info
                {
                    "COLUMN_NAME": "ID",
                    "DATA_TYPE": "NUMBER(38,0)",
                    "ORDINAL_POSITION": 1,
                },
                {
                    "COLUMN_NAME": "NAME",
                    "DATA_TYPE": "VARCHAR(255)",
                    "ORDINAL_POSITION": 2,
                },
            ],
            [{"ID": 1, "NAME": "Alice"}, {"ID": 2, "NAME": "Bob"}],  # Sample data
            [
                {
                    "TOTAL_ROWS": 1000,
                    "NON_NULL_COUNT": 1000,
                    "CARDINALITY": 1000,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],  # ID stats
            [
                {
                    "TOTAL_ROWS": 1000,
                    "NON_NULL_COUNT": 950,
                    "CARDINALITY": 950,
                    "MIN_LEN": 3,
                    "MAX_LEN": 10,
                    "AVG_LEN": 5.5,
                }
            ],  # NAME stats
        ]

        profile = profiler.profile_table("CUSTOMERS", database="DB", schema="PUBLIC")

        assert isinstance(profile, TableProfile)
        assert profile.database == "DB"
        assert profile.schema == "PUBLIC"
        assert profile.table_name == "CUSTOMERS"
        assert profile.row_count == 1000
        assert len(profile.columns) == 2
        assert profile.columns[0].name == "ID"
        assert profile.columns[1].name == "NAME"

    def test_profile_table_with_explicit_database_schema(self, profiler, mock_snow_cli):
        """Test profiling with explicit database and schema."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 500}],
            None,
            [
                {
                    "COLUMN_NAME": "COL1",
                    "DATA_TYPE": "NUMBER(38,0)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [],
            [
                {
                    "TOTAL_ROWS": 500,
                    "NON_NULL_COUNT": 500,
                    "CARDINALITY": 500,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        profile = profiler.profile_table(
            "TABLE1", database="TESTDB", schema="TESTSCHEMA"
        )

        assert profile.database == "TESTDB"
        assert profile.schema == "TESTSCHEMA"


class TestPatternDetection:
    """Test pattern detection functionality."""

    def test_detect_email_pattern(self, profiler, mock_snow_cli):
        """Test email pattern detection (95%+ accuracy)."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "EMAIL",
                    "DATA_TYPE": "VARCHAR(255)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [
                {"EMAIL": "alice@example.com"},
                {"EMAIL": "bob@test.org"},
                {"EMAIL": "charlie@domain.co.uk"},
                {"EMAIL": "david@company.com"},
            ],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 95,
                    "CARDINALITY": 95,
                    "MIN_LEN": 10,
                    "MAX_LEN": 30,
                    "AVG_LEN": 20.5,
                }
            ],
        ]

        profile = profiler.profile_table("USERS", database="DB", schema="PUBLIC")

        assert profile.columns[0].pattern == "email"

    def test_detect_uuid_pattern(self, profiler, mock_snow_cli):
        """Test UUID pattern detection."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "UUID",
                    "DATA_TYPE": "VARCHAR(36)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [
                {"UUID": "123e4567-e89b-12d3-a456-426614174000"},
                {"UUID": "223e4567-e89b-12d3-a456-426614174001"},
                {"UUID": "323e4567-e89b-12d3-a456-426614174002"},
                {"UUID": "423e4567-e89b-12d3-a456-426614174003"},
            ],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 100,
                    "CARDINALITY": 100,
                    "MIN_LEN": 36,
                    "MAX_LEN": 36,
                    "AVG_LEN": 36.0,
                }
            ],
        ]

        profile = profiler.profile_table("EVENTS", database="DB", schema="PUBLIC")

        assert profile.columns[0].pattern == "uuid"

    def test_detect_phone_pattern(self, profiler, mock_snow_cli):
        """Test phone number pattern detection."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "PHONE",
                    "DATA_TYPE": "VARCHAR(20)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [
                {"PHONE": "+1-555-123-4567"},
                {"PHONE": "+1-555-234-5678"},
                {"PHONE": "+1-555-345-6789"},
                {"PHONE": "+1-555-456-7890"},
            ],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 90,
                    "CARDINALITY": 90,
                    "MIN_LEN": 15,
                    "MAX_LEN": 17,
                    "AVG_LEN": 16.0,
                }
            ],
        ]

        profile = profiler.profile_table("CONTACTS", database="DB", schema="PUBLIC")

        assert profile.columns[0].pattern == "phone"

    def test_detect_url_pattern(self, profiler, mock_snow_cli):
        """Test URL pattern detection."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "WEBSITE",
                    "DATA_TYPE": "VARCHAR(500)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [
                {"WEBSITE": "https://example.com"},
                {"WEBSITE": "https://test.org"},
                {"WEBSITE": "https://domain.co"},
                {"WEBSITE": "http://site.net"},
            ],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 80,
                    "CARDINALITY": 80,
                    "MIN_LEN": 15,
                    "MAX_LEN": 100,
                    "AVG_LEN": 40.0,
                }
            ],
        ]

        profile = profiler.profile_table("COMPANIES", database="DB", schema="PUBLIC")

        assert profile.columns[0].pattern == "url"

    def test_no_pattern_for_non_string_columns(self, profiler, mock_snow_cli):
        """Test that pattern detection skips non-string columns."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "AMOUNT",
                    "DATA_TYPE": "NUMBER(10,2)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [{"AMOUNT": 123.45}, {"AMOUNT": 234.56}],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 100,
                    "CARDINALITY": 95,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        profile = profiler.profile_table("TRANSACTIONS", database="DB", schema="PUBLIC")

        assert profile.columns[0].pattern is None


class TestPerformanceAndScalability:
    """Test performance and scalability features."""

    def test_large_table_uses_approx_count(self, mock_snow_cli):
        """Test APPROX_COUNT_DISTINCT for tables >100K rows."""
        profiler = TableProfiler(snow_cli=mock_snow_cli, use_approx_count=True)

        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 200000}],  # Large table
            None,
            [{"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER(38,0)", "ORDINAL_POSITION": 1}],
            [],
            [
                {
                    "TOTAL_ROWS": 200000,
                    "NON_NULL_COUNT": 200000,
                    "CARDINALITY": 200000,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        _ = profiler.profile_table("LARGE_TABLE", database="DB", schema="PUBLIC")

        # Check that APPROX_COUNT_DISTINCT was used
        calls = [str(call) for call in mock_snow_cli.execute_query.call_args_list]
        assert any("APPROX_COUNT_DISTINCT" in str(call) for call in calls)

    def test_performance_target(self, profiler, mock_snow_cli):
        """Test that profiling completes in reasonable time."""
        # Simple mock setup
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 1000000}],
            None,
            [{"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER(38,0)", "ORDINAL_POSITION": 1}],
            [],
            [
                {
                    "TOTAL_ROWS": 1000000,
                    "NON_NULL_COUNT": 1000000,
                    "CARDINALITY": 1000000,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        start = datetime.now()
        profile = profiler.profile_table("BIG_TABLE", database="DB", schema="PUBLIC")
        duration = (datetime.now() - start).total_seconds()

        # Mock execution should be nearly instant
        assert duration < 1.0
        assert profile.profiling_time_seconds < 1.0


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_sql_injection_prevention_table_name(self, profiler, mock_snow_cli):
        """Test that SQL injection is prevented via identifier quoting."""
        # Valid table names should work
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 10}],
            None,
            [{"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER(38,0)", "ORDINAL_POSITION": 1}],
            [],
            [
                {
                    "TOTAL_ROWS": 10,
                    "NON_NULL_COUNT": 10,
                    "CARDINALITY": 10,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        # Should work without error
        profile = profiler.profile_table("SAFE_TABLE", database="DB", schema="PUBLIC")
        assert profile is not None

    def test_invalid_identifier_raises_error(self, profiler, mock_snow_cli):
        """Test that invalid identifiers are rejected."""
        # Table name with SQL injection attempt
        with pytest.raises(ValueError, match="Invalid identifier"):
            profiler.profile_table(
                "TABLE'; DROP TABLE USERS--", database="DB", schema="PUBLIC"
            )

        # Database with special characters
        with pytest.raises(ValueError, match="Invalid identifier"):
            profiler.profile_table("TABLE", database="DB'; DROP--", schema="PUBLIC")


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_table(self, profiler, mock_snow_cli):
        """Test profiling empty table (0 rows)."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 0}],
            None,
            [{"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER(38,0)", "ORDINAL_POSITION": 1}],
            [],
            [
                {
                    "TOTAL_ROWS": 0,
                    "NON_NULL_COUNT": 0,
                    "CARDINALITY": 0,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        profile = profiler.profile_table("EMPTY_TABLE", database="DB", schema="PUBLIC")

        assert profile.row_count == 0
        assert len(profile.columns) == 1
        assert profile.columns[0].null_percentage == 0.0

    def test_single_column_table(self, profiler, mock_snow_cli):
        """Test profiling table with single column."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "VALUE",
                    "DATA_TYPE": "VARCHAR(100)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [{"VALUE": "test"}],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 100,
                    "CARDINALITY": 50,
                    "MIN_LEN": 4,
                    "MAX_LEN": 10,
                    "AVG_LEN": 7.0,
                }
            ],
        ]

        profile = profiler.profile_table("SINGLE_COL", database="DB", schema="PUBLIC")

        assert len(profile.columns) == 1
        assert profile.columns[0].name == "VALUE"

    def test_table_with_all_null_column(self, profiler, mock_snow_cli):
        """Test handling of columns with 100% null values."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 100}],
            None,
            [
                {
                    "COLUMN_NAME": "NULL_COL",
                    "DATA_TYPE": "VARCHAR(100)",
                    "ORDINAL_POSITION": 1,
                }
            ],
            [{"NULL_COL": None}, {"NULL_COL": None}],
            [
                {
                    "TOTAL_ROWS": 100,
                    "NON_NULL_COUNT": 0,
                    "CARDINALITY": 0,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        profile = profiler.profile_table("NULL_TABLE", database="DB", schema="PUBLIC")

        assert profile.columns[0].null_percentage == 100.0
        assert profile.columns[0].cardinality == 0


class TestErrorHandling:
    """Test error handling."""

    def test_table_not_found_raises_error(self, profiler, mock_snow_cli):
        """Test that non-existent table raises appropriate error."""
        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 0}],
            None,
            [],  # No columns found
        ]

        with pytest.raises(ValueError, match="Table not found or no columns"):
            profiler.profile_table("NONEXISTENT", database="DB", schema="PUBLIC")

    def test_sample_rows_respects_limit(self, profiler, mock_snow_cli):
        """Test that sample rows respects configured limit."""
        sample_size = 50
        profiler_custom = TableProfiler(snow_cli=mock_snow_cli, sample_size=sample_size)

        mock_snow_cli.execute_query.side_effect = [
            [{"CNT": 1000}],
            None,
            [{"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER(38,0)", "ORDINAL_POSITION": 1}],
            [{"ID": i} for i in range(50)],  # Sample data (limited)
            [
                {
                    "TOTAL_ROWS": 1000,
                    "NON_NULL_COUNT": 1000,
                    "CARDINALITY": 1000,
                    "MIN_LEN": None,
                    "MAX_LEN": None,
                    "AVG_LEN": None,
                }
            ],
        ]

        _ = profiler_custom.profile_table("TABLE1", database="DB", schema="PUBLIC")

        # Verify sample query was called with correct limit
        calls = [str(call) for call in mock_snow_cli.execute_query.call_args_list]
        assert any(f"LIMIT {sample_size}" in str(call) for call in calls)
