"""Tests for DocumentationGenerator."""

from datetime import datetime

import pytest

from snowcli_tools.discovery.documentation_generator import DocumentationGenerator
from snowcli_tools.discovery.models import (
    ColumnMeaning,
    ColumnProfile,
    ConfidenceLevel,
    DepthMode,
    DiscoveryMetadata,
    DiscoveryResult,
    LLMAnalysis,
    OutputFormat,
    Relationship,
    TableCategory,
    TableProfile,
)


@pytest.fixture
def sample_profile():
    """Create a sample TableProfile."""
    return TableProfile(
        database="TEST_DB",
        schema="PUBLIC",
        table_name="CUSTOMERS",
        row_count=10000,
        columns=[
            ColumnProfile(
                name="ID",
                data_type="NUMBER",
                null_percentage=0.0,
                cardinality=10000,
                pattern=None,
                sample_values=[1, 2, 3],
            ),
            ColumnProfile(
                name="EMAIL",
                data_type="VARCHAR",
                null_percentage=0.5,
                cardinality=9950,
                pattern="email",
                sample_values=["user1@test.com", "user2@test.com"],
            ),
            ColumnProfile(
                name="CREATED_AT",
                data_type="TIMESTAMP",
                null_percentage=0.0,
                cardinality=9500,
                pattern=None,
                sample_values=["2024-01-01", "2024-01-02"],
            ),
        ],
        sample_rows=[
            {"ID": 1, "EMAIL": "user1@test.com", "CREATED_AT": "2024-01-01"},
            {"ID": 2, "EMAIL": "user2@test.com", "CREATED_AT": "2024-01-02"},
        ],
        profiling_time_seconds=2.5,
        last_ddl="2024-01-01T00:00:00",
    )


@pytest.fixture
def sample_analysis():
    """Create a sample LLMAnalysis."""
    return LLMAnalysis(
        table_purpose="Customer master data",
        category=TableCategory.DIMENSION,
        confidence=0.85,
        column_meanings={
            "ID": ColumnMeaning(
                purpose="Primary key identifier",
                category="id",
                is_pii=False,
                confidence=0.95,
            ),
            "EMAIL": ColumnMeaning(
                purpose="Customer email address",
                category="contact",
                is_pii=True,
                confidence=0.90,
            ),
            "CREATED_AT": ColumnMeaning(
                purpose="Account creation timestamp",
                category="timestamp",
                is_pii=False,
                confidence=0.88,
            ),
        },
        pii_columns=["EMAIL"],
        suggested_description=(
            "This table contains customer master data including "
            "contact information and account metadata."
        ),
        analysis_time_seconds=12.3,
        token_usage={"prompt": 500, "response": 300},
    )


@pytest.fixture
def sample_relationships():
    """Create sample relationships."""
    return [
        Relationship(
            from_table="ORDERS",
            from_column="CUSTOMER_ID",
            to_table="CUSTOMERS",
            to_column="ID",
            confidence=0.85,
            evidence=["Pattern match: customer_id → CUSTOMERS.ID"],
            strategy="name_pattern",
        )
    ]


@pytest.fixture
def sample_metadata():
    """Create sample DiscoveryMetadata."""
    return DiscoveryMetadata(
        execution_time_ms=15000,
        estimated_cost_usd=0.05,
        cache_hit=False,
        table_last_modified="2024-01-01T00:00:00",
        discovery_version="1.10.0",
        confidence_level=ConfidenceLevel.HIGH,
        depth_mode=DepthMode.STANDARD,
        timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def generator():
    """Create DocumentationGenerator instance."""
    return DocumentationGenerator()


class TestMarkdownGeneration:
    """Test Markdown generation."""

    def test_markdown_basic_structure(self, generator, sample_profile, sample_metadata):
        """Test basic markdown structure without analysis."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=None, metadata=sample_metadata
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        # Check title
        assert "# CUSTOMERS - Data Dictionary" in markdown

        # Check metadata section
        assert "**Database**: `TEST_DB.PUBLIC.CUSTOMERS`" in markdown
        assert "**Rows**: 10,000" in markdown

        # Check schema table
        assert "| Column | Type | Purpose | Null% | Cardinality | PII |" in markdown
        assert "| `ID` | NUMBER |" in markdown
        assert "| `EMAIL` | VARCHAR |" in markdown

        # Check discovery metadata
        assert "## Discovery Metadata" in markdown
        assert "**Discovery Mode**: standard" in markdown
        assert "**Estimated Cost**: $0.0500" in markdown

    def test_markdown_with_analysis(
        self, generator, sample_profile, sample_analysis, sample_metadata
    ):
        """Test markdown with LLM analysis included."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=sample_analysis, metadata=sample_metadata
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        # Check purpose section
        assert "## Purpose" in markdown
        assert "Customer master data" in markdown
        assert "**Category**: dimension_table" in markdown
        assert "**Confidence**: 85% (high)" in markdown

        # Check PII warnings
        assert "⚠️ Yes" in markdown
        assert "Primary key identifier" in markdown
        assert "Customer email address" in markdown

    def test_markdown_with_relationships(
        self,
        generator,
        sample_profile,
        sample_analysis,
        sample_relationships,
        sample_metadata,
    ):
        """Test markdown with relationships."""
        result = DiscoveryResult(
            profile=sample_profile,
            analysis=sample_analysis,
            relationships=sample_relationships,
            metadata=sample_metadata,
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        # Check relationships section
        assert "## Relationships" in markdown

        # Check Mermaid diagram
        assert "```mermaid" in markdown
        assert "erDiagram" in markdown
        assert "ORDERS ||--o{ CUSTOMERS" in markdown

        # Check relationships table
        assert (
            "| From Column | To Table | To Column | Confidence | Evidence |" in markdown
        )
        assert "| `CUSTOMER_ID` | `CUSTOMERS` | `ID` |" in markdown
        assert "85%" in markdown

    def test_markdown_sample_data(self, generator, sample_profile, sample_metadata):
        """Test sample data section in markdown."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=None, metadata=sample_metadata
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        # Check sample data section
        assert "## Sample Data" in markdown
        assert "```json" in markdown
        assert '"EMAIL": "user1@test.com"' in markdown

    def test_markdown_empty_relationships(
        self, generator, sample_profile, sample_analysis, sample_metadata
    ):
        """Test markdown when no relationships discovered."""
        result = DiscoveryResult(
            profile=sample_profile,
            analysis=sample_analysis,
            relationships=[],
            metadata=sample_metadata,
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        # Should not have relationships section
        assert "## Relationships" not in markdown
        assert "```mermaid" not in markdown


class TestJSONGeneration:
    """Test JSON generation."""

    def test_json_structure(
        self, generator, sample_profile, sample_analysis, sample_metadata
    ):
        """Test JSON output structure."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=sample_analysis, metadata=sample_metadata
        )

        json_output = generator.generate(result, OutputFormat.JSON)

        # Should be valid JSON
        import json

        data = json.loads(json_output)

        # Check top-level keys
        assert "profile" in data
        assert "analysis" in data
        assert "relationships" in data
        assert "metadata" in data

        # Check profile structure
        assert data["profile"]["table_name"] == "CUSTOMERS"
        assert data["profile"]["row_count"] == 10000
        assert len(data["profile"]["columns"]) == 3

        # Check analysis structure
        assert data["analysis"]["table_purpose"] == "Customer master data"
        assert data["analysis"]["confidence"] == 0.85
        assert "EMAIL" in data["analysis"]["pii_columns"]

    def test_json_without_analysis(self, generator, sample_profile, sample_metadata):
        """Test JSON output without analysis (quick mode)."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=None, metadata=sample_metadata
        )

        json_output = generator.generate(result, OutputFormat.JSON)

        import json

        data = json.loads(json_output)

        assert data["analysis"] is None
        assert "profile" in data


class TestSummaryFormat:
    """Test summary format for batch results."""

    def test_summary_basic(
        self, generator, sample_profile, sample_analysis, sample_metadata
    ):
        """Test basic summary format."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=sample_analysis, metadata=sample_metadata
        )

        summary = generator.format_summary(result)

        assert "📊 CUSTOMERS" in summary
        assert "Rows: 10,000" in summary
        assert "Columns: 3" in summary
        assert "Customer master data" in summary
        assert "85% confidence" in summary

    def test_summary_with_pii(
        self, generator, sample_profile, sample_analysis, sample_metadata
    ):
        """Test summary includes PII warning."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=sample_analysis, metadata=sample_metadata
        )

        summary = generator.format_summary(result)

        assert "⚠️  PII Columns: EMAIL" in summary

    def test_summary_with_relationships(
        self,
        generator,
        sample_profile,
        sample_analysis,
        sample_relationships,
        sample_metadata,
    ):
        """Test summary includes relationship count."""
        result = DiscoveryResult(
            profile=sample_profile,
            analysis=sample_analysis,
            relationships=sample_relationships,
            metadata=sample_metadata,
        )

        summary = generator.format_summary(result)

        assert "🔗 Relationships: 1 discovered" in summary


class TestErrorFormatting:
    """Test error formatting."""

    def test_error_table_not_found(self, generator):
        """Test error formatting for table not found."""
        error = ValueError("Table 'MISSING_TABLE' does not exist")

        error_msg = generator.format_error("MISSING_TABLE", error)

        assert "❌ Discovery Failed: MISSING_TABLE" in error_msg
        assert "ValueError" in error_msg
        assert "does not exist" in error_msg
        assert "Troubleshooting" in error_msg
        assert "Verify the table name is correct" in error_msg

    def test_error_permission_denied(self, generator):
        """Test error formatting for permission errors."""
        error = PermissionError("Insufficient privileges to access table")

        error_msg = generator.format_error("SECRET_TABLE", error)

        assert "❌ Discovery Failed: SECRET_TABLE" in error_msg
        assert "PermissionError" in error_msg
        assert "SELECT permissions" in error_msg

    def test_error_timeout(self, generator):
        """Test error formatting for timeout."""
        error = TimeoutError("Discovery timed out after 60 seconds")

        error_msg = generator.format_error("HUGE_TABLE", error)

        assert "❌ Discovery Failed: HUGE_TABLE" in error_msg
        assert "TimeoutError" in error_msg
        assert "quick' depth mode" in error_msg


class TestEdgeCases:
    """Test edge cases."""

    def test_unsupported_format_raises_error(
        self, generator, sample_profile, sample_metadata
    ):
        """Test unsupported format raises ValueError."""
        result = DiscoveryResult(
            profile=sample_profile, analysis=None, metadata=sample_metadata
        )

        with pytest.raises(ValueError, match="Unsupported output format"):
            generator.generate(result, "xml")  # Invalid format

    def test_empty_sample_rows(self, generator, sample_metadata):
        """Test handling of empty sample rows."""
        profile = TableProfile(
            database="DB",
            schema="SCH",
            table_name="EMPTY",
            row_count=0,
            columns=[],
            sample_rows=[],
            profiling_time_seconds=0.1,
        )

        result = DiscoveryResult(
            profile=profile, analysis=None, metadata=sample_metadata
        )

        markdown = generator.generate(result, OutputFormat.MARKDOWN)

        assert "# EMPTY - Data Dictionary" in markdown
        assert "**Rows**: 0" in markdown
