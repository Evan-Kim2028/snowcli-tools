"""Tests for LLMAnalyzer."""

from unittest.mock import Mock

import pytest

from snowcli_tools.discovery.llm_analyzer import LLMAnalyzer
from snowcli_tools.discovery.models import (
    ColumnProfile,
    LLMAnalysis,
    TableCategory,
    TableProfile,
)


@pytest.fixture
def mock_snow_cli():
    """Create a mock SnowCLI instance."""
    return Mock()


@pytest.fixture
def analyzer(mock_snow_cli):
    """Create an LLMAnalyzer instance with mock SnowCLI."""
    return LLMAnalyzer(snow_cli=mock_snow_cli)


@pytest.fixture
def sample_customer_profile():
    """Sample customer dimension table profile."""
    return TableProfile(
        database="DB",
        schema="PUBLIC",
        table_name="CUSTOMERS",
        row_count=1000,
        columns=[
            ColumnProfile(
                name="CUSTOMER_ID",
                data_type="NUMBER(38,0)",
                null_percentage=0.0,
                cardinality=1000,
                pattern="uuid",
            ),
            ColumnProfile(
                name="EMAIL",
                data_type="VARCHAR(255)",
                null_percentage=2.0,
                cardinality=980,
                pattern="email",
            ),
            ColumnProfile(
                name="NAME",
                data_type="VARCHAR(100)",
                null_percentage=0.0,
                cardinality=950,
                pattern=None,
            ),
        ],
        sample_rows=[
            {"CUSTOMER_ID": 1, "EMAIL": "alice@example.com", "NAME": "Alice"},
            {"CUSTOMER_ID": 2, "EMAIL": "bob@test.org", "NAME": "Bob"},
        ],
        profiling_time_seconds=1.5,
        last_ddl="2025-01-01T00:00:00",
    )


class TestLLMAnalyzerCore:
    """Test core LLMAnalyzer functionality."""

    def test_analyze_table_dimension(
        self, analyzer, mock_snow_cli, sample_customer_profile
    ):
        """Test analysis of dimension table."""
        # Mock Cortex Complete response
        mock_response = """
        {
            "table_purpose": "Customer master dimension table",
            "category": "dimension_table",
            "confidence": 92,
            "suggested_description": "Contains customer account information including contact details.",
            "columns": {
                "CUSTOMER_ID": {
                    "purpose": "Unique customer identifier",
                    "category": "id",
                    "is_pii": false,
                    "confidence": 95,
                },
                "EMAIL": {
                    "purpose": "Customer email address",
                    "category": "contact",
                    "is_pii": true,
                    "confidence": 98,
                },
                "NAME": {"purpose": "Customer name", "category": "name", "is_pii": true, "confidence": 90}
            },
            "reasoning": "Table name and columns suggest customer data"
        }
        """

        mock_snow_cli.run_query.return_value = Mock(rows=[{"RESPONSE": mock_response}])

        result = analyzer.analyze_table(sample_customer_profile)

        assert isinstance(result, LLMAnalysis)
        assert result.table_purpose == "Customer master dimension table"
        assert result.category == TableCategory.DIMENSION
        assert result.confidence == 0.92
        assert "EMAIL" in result.pii_columns
        assert "NAME" in result.pii_columns
        assert len(result.column_meanings) == 3

    def test_analyze_table_fact(self, analyzer, mock_snow_cli):
        """Test analysis of fact table."""
        fact_profile = TableProfile(
            database="DB",
            schema="PUBLIC",
            table_name="TRANSACTIONS",
            row_count=50000,
            columns=[
                ColumnProfile(
                    name="TRANSACTION_ID",
                    data_type="NUMBER(38,0)",
                    null_percentage=0.0,
                    cardinality=50000,
                ),
                ColumnProfile(
                    name="AMOUNT",
                    data_type="NUMBER(10,2)",
                    null_percentage=0.0,
                    cardinality=5000,
                ),
            ],
            sample_rows=[{"TRANSACTION_ID": 1, "AMOUNT": 99.99}],
            profiling_time_seconds=2.0,
        )

        mock_response = """
        {
            "table_purpose": "Transaction fact table",
            "category": "fact_table",
            "confidence": 88,
            "suggested_description": "Records all financial transactions.",
            "columns": {
                "TRANSACTION_ID": {
                    "purpose": "Unique transaction ID",
                    "category": "id",
                    "is_pii": false,
                    "confidence": 95,
                },
                "AMOUNT": {
                    "purpose": "Transaction amount",
                    "category": "amount",
                    "is_pii": false,
                    "confidence": 90,
                }
            }
        }
        """

        mock_snow_cli.run_query.return_value = Mock(rows=[{"RESPONSE": mock_response}])

        result = analyzer.analyze_table(fact_profile)

        assert result.category == TableCategory.FACT
        assert result.confidence == 0.88

    def test_analyze_table_event_log(self, analyzer, mock_snow_cli):
        """Test analysis of event log table."""
        event_profile = TableProfile(
            database="DB",
            schema="PUBLIC",
            table_name="EVENT_LOG",
            row_count=100000,
            columns=[
                ColumnProfile(
                    name="EVENT_ID",
                    data_type="NUMBER(38,0)",
                    null_percentage=0.0,
                    cardinality=100000,
                ),
                ColumnProfile(
                    name="TIMESTAMP",
                    data_type="TIMESTAMP_LTZ",
                    null_percentage=0.0,
                    cardinality=100000,
                ),
            ],
            sample_rows=[],
            profiling_time_seconds=2.5,
        )

        mock_response = """
        {
            "table_purpose": "System event log",
            "category": "event_log",
            "confidence": 85,
            "suggested_description": "Tracks system events and user actions.",
            "columns": {}
        }
        """

        mock_snow_cli.run_query.return_value = Mock(rows=[{"RESPONSE": mock_response}])

        result = analyzer.analyze_table(event_profile)

        assert result.category == TableCategory.EVENT_LOG


class TestPromptEngineering:
    """Test prompt building logic."""

    def test_build_analysis_prompt_structure(self, analyzer, sample_customer_profile):
        """Test that prompt has all required sections."""
        prompt = analyzer._build_analysis_prompt(sample_customer_profile)

        assert "TABLE: DB.PUBLIC.CUSTOMERS" in prompt
        assert "ROWS: 1,000" in prompt
        assert "COLUMNS (3):" in prompt
        assert "CUSTOMER_ID" in prompt
        assert "EMAIL" in prompt
        assert "SAMPLE ROWS" in prompt

    def test_build_analysis_prompt_includes_patterns(
        self, analyzer, sample_customer_profile
    ):
        """Test that detected patterns are included in prompt."""
        prompt = analyzer._build_analysis_prompt(sample_customer_profile)

        assert "pattern=uuid" in prompt
        assert "pattern=email" in prompt


class TestResponseParsing:
    """Test JSON response parsing."""

    def test_parse_valid_json_response(self, analyzer):
        """Test parsing of well-formed JSON response."""
        response = '{"table_purpose": "Test", "category": "dimension_table", "confidence": 80, "columns": {}}'

        data = analyzer._parse_llm_response(response)

        assert data["table_purpose"] == "Test"
        assert data["category"] == "dimension_table"
        assert data["confidence"] == 80

    def test_parse_json_in_markdown_code_block(self, analyzer):
        """Test handling of JSON wrapped in ```json ... ``` blocks."""
        response = """
        ```json
        {"table_purpose": "Test", "category": "fact_table", "confidence": 75, "columns": {}}
        ```
        """

        data = analyzer._parse_llm_response(response)

        assert data["table_purpose"] == "Test"

    def test_parse_malformed_json_raises(self, analyzer):
        """Test that malformed JSON raises ValueError."""
        response = "This is not JSON at all"

        with pytest.raises(ValueError, match="Could not parse JSON"):
            analyzer._parse_llm_response(response)


class TestPIIDetection:
    """Test PII detection functionality."""

    def test_pii_detection_email(self, analyzer, mock_snow_cli):
        """Test PII detection for email columns (95%+ accuracy)."""
        profile = TableProfile(
            database="DB",
            schema="PUBLIC",
            table_name="USERS",
            row_count=100,
            columns=[
                ColumnProfile(
                    name="EMAIL",
                    data_type="VARCHAR(255)",
                    null_percentage=0.0,
                    cardinality=100,
                )
            ],
            sample_rows=[],
            profiling_time_seconds=1.0,
        )

        mock_response = """
        {
            "table_purpose": "User table",
            "category": "dimension_table",
            "confidence": 80,
            "columns": {
                "EMAIL": {"purpose": "User email", "category": "contact", "is_pii": true, "confidence": 95}
            }
        }
        """

        mock_snow_cli.run_query.return_value = Mock(rows=[{"RESPONSE": mock_response}])

        result = analyzer.analyze_table(profile)

        assert "EMAIL" in result.pii_columns
        assert result.column_meanings["EMAIL"].is_pii is True


class TestErrorHandling:
    """Test error handling."""

    def test_cortex_failure_uses_fallback(
        self, analyzer, mock_snow_cli, sample_customer_profile
    ):
        """Test fallback when LLM returns malformed JSON."""
        mock_snow_cli.run_query.return_value = Mock(
            rows=[{"RESPONSE": "Invalid JSON!!!"}]
        )

        result = analyzer.analyze_table(sample_customer_profile)

        # Should use fallback
        assert result.confidence < 0.5
        assert "fallback" in result.suggested_description.lower()

    def test_empty_cortex_response_uses_fallback(
        self, analyzer, mock_snow_cli, sample_customer_profile
    ):
        """Test that empty Cortex response uses fallback."""
        mock_snow_cli.run_query.return_value = Mock(rows=[])

        result = analyzer.analyze_table(sample_customer_profile)

        # Should use fallback
        assert result.confidence < 0.5
        assert (
            result.category == TableCategory.DIMENSION
        )  # Based on table name "CUSTOMERS"


class TestFallbackAnalysis:
    """Test fallback analysis logic."""

    def test_fallback_detects_dimension_by_name(self, analyzer):
        """Test fallback correctly identifies dimension tables by name."""
        profile = TableProfile(
            database="DB",
            schema="PUBLIC",
            table_name="DIM_CUSTOMERS",
            row_count=100,
            columns=[],
            sample_rows=[],
            profiling_time_seconds=1.0,
        )

        result = analyzer._create_fallback_analysis(profile, "Test error")

        assert result.category == TableCategory.DIMENSION

    def test_fallback_detects_pii_by_column_name(self, analyzer):
        """Test fallback detects PII by column name patterns."""
        profile = TableProfile(
            database="DB",
            schema="PUBLIC",
            table_name="TEST_TABLE",
            row_count=100,
            columns=[
                ColumnProfile(
                    name="EMAIL",
                    data_type="VARCHAR(255)",
                    null_percentage=0.0,
                    cardinality=100,
                ),
                ColumnProfile(
                    name="PHONE",
                    data_type="VARCHAR(20)",
                    null_percentage=0.0,
                    cardinality=100,
                ),
                ColumnProfile(
                    name="ID",
                    data_type="NUMBER(38,0)",
                    null_percentage=0.0,
                    cardinality=100,
                ),
            ],
            sample_rows=[],
            profiling_time_seconds=1.0,
        )

        result = analyzer._create_fallback_analysis(profile, "Test error")

        assert "EMAIL" in result.pii_columns
        assert "PHONE" in result.pii_columns
        assert "ID" not in result.pii_columns
