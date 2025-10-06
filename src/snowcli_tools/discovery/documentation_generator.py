"""
DocumentationGenerator - Format discovery results.

Generates documentation in multiple formats:
- Markdown data dictionary (agent-optimized)
- JSON export (machine-readable)
- Mermaid ER diagrams (relationship visualization)
"""

import json

from snowcli_tools.discovery.models import DiscoveryResult, OutputFormat


class DocumentationGenerator:
    """Generate documentation from discovery results."""

    @staticmethod
    def _map_confidence_to_qualifier(confidence: float) -> str:
        """
        Map numeric confidence score to qualitative qualifier.

        Internal confidence scores are still calculated for analysis,
        but presented qualitatively to users for clarity.

        Args:
            confidence: Numeric confidence score (0.0 to 1.0)

        Returns:
            Qualitative descriptor: "confirmed", "likely", "possibly", or "uncertain"
        """
        if confidence >= 0.85:
            return "confirmed"
        elif confidence >= 0.70:
            return "likely"
        elif confidence >= 0.50:
            return "possibly"
        else:
            return "uncertain"

    def generate(
        self,
        result: DiscoveryResult,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """
        Generate documentation in specified format.

        Args:
            result: DiscoveryResult to document
            output_format: Format (markdown or json)

        Returns:
            Formatted documentation string
        """
        if output_format == OutputFormat.MARKDOWN:
            return self._generate_markdown(result)
        elif output_format == OutputFormat.JSON:
            return self._generate_json(result)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_markdown(self, result: DiscoveryResult) -> str:
        """
        Generate Markdown data dictionary.

        Optimized for agent consumption with clear structure.
        """
        profile = result.profile
        analysis = result.analysis
        relationships = result.relationships
        metadata = result.metadata

        lines = []

        # Title
        lines.append(f"# {profile.table_name} - Data Dictionary")
        lines.append("")

        # Metadata
        lines.append(
            f"**Database**: `{profile.database}.{profile.schema}.{profile.table_name}`"
        )
        lines.append(f"**Rows**: {profile.row_count:,}")
        lines.append(f"**Last Modified**: {profile.last_ddl or 'Unknown'}")
        lines.append("")

        # Purpose (if analyzed)
        if analysis:
            # Map confidence to qualifier
            purpose_qualifier = self._map_confidence_to_qualifier(analysis.confidence)

            lines.append("## Purpose")
            lines.append("")
            lines.append(f"{analysis.suggested_description} ({purpose_qualifier})")
            lines.append("")
            lines.append(f"**Category**: {analysis.category.value}")
            lines.append("")

        # Schema
        lines.append("## Schema")
        lines.append("")
        lines.append("| Column | Type | Purpose | Null% | Cardinality | PII |")
        lines.append("|--------|------|---------|-------|-------------|-----|")

        for col in profile.columns:
            col_purpose = ""
            is_pii = ""

            if analysis and col.name in analysis.column_meanings:
                meaning = analysis.column_meanings[col.name]
                col_purpose = meaning.purpose
                is_pii = "⚠️ Yes" if meaning.is_pii else "No"

            lines.append(
                f"| `{col.name}` | {col.data_type} | {col_purpose} | "
                f"{col.null_percentage:.1f}% | {col.cardinality:,} | {is_pii} |"
            )

        lines.append("")

        # Relationships (if discovered)
        if relationships:
            lines.append("## Relationships")
            lines.append("")

            # Mermaid diagram
            lines.append("```mermaid")
            lines.append("erDiagram")

            for rel in relationships:
                lines.append(
                    f'    {rel.from_table} ||--o{{ {rel.to_table} : "{rel.from_column}"'
                )

            lines.append("```")
            lines.append("")

            # Table
            lines.append(
                "| From Column | To Table | To Column | Confidence | Evidence |"
            )
            lines.append(
                "|-------------|----------|-----------|------------|----------|"
            )

            for rel in relationships:
                evidence_str = rel.evidence[0] if rel.evidence else ""
                lines.append(
                    f"| `{rel.from_column}` | `{rel.to_table}` | `{rel.to_column}` | "
                    f"{rel.confidence*100:.0f}% | {evidence_str} |"
                )

            lines.append("")

        # Sample Data
        if profile.sample_rows:
            lines.append("## Sample Data")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(profile.sample_rows[:3], indent=2, default=str))
            lines.append("```")
            lines.append("")

        # Discovery Metadata
        lines.append("## Discovery Metadata")
        lines.append("")
        lines.append(f"- **Discovery Mode**: {metadata.depth_mode.value}")
        lines.append(f"- **Execution Time**: {metadata.execution_time_ms}ms")
        lines.append(f"- **Estimated Cost**: ${metadata.estimated_cost_usd:.4f}")
        lines.append(f"- **Cache Hit**: {metadata.cache_hit}")
        lines.append(f"- **Discovery Version**: {metadata.discovery_version}")
        lines.append(f"- **Timestamp**: {metadata.timestamp}")

        return "\n".join(lines)

    def _generate_json(self, result: DiscoveryResult) -> str:
        """Generate JSON export."""
        return json.dumps(result.to_dict(), indent=2, default=str)

    def format_summary(self, result: DiscoveryResult) -> str:
        """
        Generate a concise summary for quick reference.

        Useful for batch discovery results or quick previews.
        """
        profile = result.profile
        analysis = result.analysis
        metadata = result.metadata

        lines = []
        lines.append(f"📊 {profile.table_name}")
        lines.append(
            f"   Rows: {profile.row_count:,} | Columns: {len(profile.columns)}"
        )

        if analysis:
            lines.append(f"   Purpose: {analysis.table_purpose}")
            lines.append(
                f"   Category: {analysis.category.value} ({analysis.confidence*100:.0f}% confidence)"
            )

            if analysis.pii_columns:
                lines.append(f"   ⚠️  PII Columns: {', '.join(analysis.pii_columns)}")

        if result.relationships:
            lines.append(f"   🔗 Relationships: {len(result.relationships)} discovered")

        lines.append(
            f"   ⏱️  {metadata.execution_time_ms}ms | ${metadata.estimated_cost_usd:.4f}"
        )

        return "\n".join(lines)

    def format_error(self, table_name: str, error: Exception) -> str:
        """
        Format an error message for failed discoveries.

        Args:
            table_name: Name of table that failed
            error: Exception that was raised

        Returns:
            Formatted error message
        """
        lines = []
        lines.append(f"# ❌ Discovery Failed: {table_name}")
        lines.append("")
        lines.append(f"**Error Type**: {type(error).__name__}")
        lines.append(f"**Error Message**: {str(error)}")
        lines.append("")
        lines.append("## Troubleshooting")
        lines.append("")

        if "does not exist" in str(error).lower():
            lines.append(
                "- Verify the table name is correct and includes schema if needed"
            )
            lines.append(
                "- Check that you have access to the specified database/schema"
            )
        elif "permission" in str(error).lower() or isinstance(error, PermissionError):
            lines.append("- Verify you have SELECT permissions on the table")
            lines.append("- Check your Snowflake role has necessary grants")
        elif "timeout" in str(error).lower() or isinstance(error, TimeoutError):
            lines.append(
                "- The table may be very large - try using include_ai_analysis=False for faster profiling"
            )
            lines.append("- Increase the timeout_seconds parameter")
        else:
            lines.append("- Check the error message above for specific details")
            lines.append("- Verify your Snowflake connection is active")

        return "\n".join(lines)
