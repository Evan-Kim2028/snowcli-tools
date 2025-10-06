"""
Data models for Discovery Assistant.

This module defines all data structures used by the Discovery Assistant.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DepthMode(str, Enum):
    """Discovery depth modes.

    NOTE: This enum is kept for backward compatibility with DiscoveryMetadata only.
    New code should use boolean parameters (include_ai_analysis, include_relationships).
    """

    QUICK = "quick"  # SQL profiling only
    STANDARD = "standard"  # + LLM analysis
    DEEP = "deep"  # + Relationship discovery


class OutputFormat(str, Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"


class CachePolicy(str, Enum):
    """Cache behavior policies.

    NOTE: This enum is kept for backward compatibility only.
    New code uses automatic caching with force_refresh parameter.
    """

    ALWAYS = "always"  # Always use cache if available
    IF_FRESH = "if_fresh"  # Use cache if table hasn't changed (LAST_DDL check)
    NEVER = "never"  # Always re-discover


class ConfidenceLevel(str, Enum):
    """Confidence interpretation levels."""

    HIGH = "high"  # 80-100%
    MEDIUM = "medium"  # 60-79%
    LOW = "low"  # <60%


class TableCategory(str, Enum):
    """Table category classifications."""

    DIMENSION = "dimension_table"
    FACT = "fact_table"
    EVENT_LOG = "event_log"
    REFERENCE = "reference_data"
    UNKNOWN = "unknown"


@dataclass
class ColumnProfile:
    """Statistical profile for a single column."""

    name: str
    data_type: str
    null_percentage: float
    cardinality: int
    pattern: Optional[str] = None  # "email", "uuid", "phone", "url", etc.
    sample_values: list[Any] = field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_length: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "null_percentage": self.null_percentage,
            "cardinality": self.cardinality,
            "pattern": self.pattern,
            "sample_values": self.sample_values[:5],  # Limit sample values
            "min_value": str(self.min_value) if self.min_value is not None else None,
            "max_value": str(self.max_value) if self.max_value is not None else None,
            "avg_length": self.avg_length,
        }


@dataclass
class TableProfile:
    """Complete statistical profile of a table."""

    database: str
    schema: str
    table_name: str
    row_count: int
    columns: list[ColumnProfile]
    sample_rows: list[dict[str, Any]]
    profiling_time_seconds: float
    last_ddl: Optional[str] = None  # ISO timestamp

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "database": self.database,
            "schema": self.schema,
            "table_name": self.table_name,
            "row_count": self.row_count,
            "columns": [col.to_dict() for col in self.columns],
            "sample_rows": self.sample_rows[:3],  # Limit sample rows
            "profiling_time_seconds": self.profiling_time_seconds,
            "last_ddl": self.last_ddl,
        }


@dataclass
class ColumnMeaning:
    """AI-inferred meaning of a column."""

    purpose: str
    category: str  # "id", "name", "contact", "timestamp", etc.
    is_pii: bool
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class LLMAnalysis:
    """AI inference results from Cortex Complete."""

    table_purpose: str
    category: TableCategory
    confidence: float  # 0.0-1.0
    column_meanings: dict[str, ColumnMeaning]
    pii_columns: list[str]
    suggested_description: str
    analysis_time_seconds: float
    token_usage: Optional[dict[str, int]] = None  # {"prompt": X, "response": Y}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "table_purpose": self.table_purpose,
            "category": self.category.value,
            "confidence": self.confidence,
            "column_meanings": {
                k: v.to_dict() for k, v in self.column_meanings.items()
            },
            "pii_columns": self.pii_columns,
            "suggested_description": self.suggested_description,
            "analysis_time_seconds": self.analysis_time_seconds,
            "token_usage": self.token_usage,
        }


@dataclass
class Relationship:
    """Discovered foreign key relationship."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    confidence: float
    evidence: list[str]
    strategy: str  # "name_pattern", "value_overlap", "combined"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class DiscoveryMetadata:
    """Enhanced metadata for discovery results."""

    execution_time_ms: int
    estimated_cost_usd: float
    cache_hit: bool
    table_last_modified: str  # ISO timestamp
    discovery_version: str  # "1.10.0"
    confidence_level: ConfidenceLevel
    depth_mode: DepthMode
    timestamp: str  # ISO timestamp of discovery

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "execution_time_ms": self.execution_time_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "cache_hit": self.cache_hit,
            "table_last_modified": self.table_last_modified,
            "discovery_version": self.discovery_version,
            "confidence_level": self.confidence_level.value,
            "depth_mode": self.depth_mode.value,
            "timestamp": self.timestamp,
        }


@dataclass
class DiscoveryResult:
    """Complete discovery output."""

    profile: TableProfile
    analysis: Optional[LLMAnalysis] = None  # None for quick mode
    relationships: list[Relationship] = field(default_factory=list)
    documentation: str = ""  # Markdown or JSON formatted
    metadata: Optional[DiscoveryMetadata] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "profile": self.profile.to_dict(),
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }


@dataclass
class ExecutionMetadata:
    """Metadata about discovery execution."""

    total_cost_usd: float
    execution_time_ms: int
    cache_hits: int
    cache_misses: int
    tables_analyzed: int
    components_run: list[str]  # ["profiler", "llm_analyzer", "relationship_discoverer"]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_cost_usd": round(self.total_cost_usd, 4),
            "execution_time_ms": self.execution_time_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "tables_analyzed": self.tables_analyzed,
            "components_run": self.components_run,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DiscoveryResults:
    """
    Wrapper for discovery results with consistent return type.

    This class ensures type safety and consistent MCP serialization
    for both single-table and batch discovery operations.
    """

    results: list[DiscoveryResult]
    is_batch: bool
    metadata: ExecutionMetadata

    def first(self) -> Optional[DiscoveryResult]:
        """
        Get the first result (convenience method for single-table queries).

        Returns:
            The first DiscoveryResult if available, None otherwise.
        """
        return self.results[0] if self.results else None

    def __len__(self) -> int:
        """Return number of results."""
        return len(self.results)

    def __iter__(self):
        """Allow iteration over results."""
        return iter(self.results)

    def __getitem__(self, index: int) -> DiscoveryResult:
        """Allow indexing into results."""
        return self.results[index]

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize for MCP JSON response.

        Format depends on whether this is a batch or single-table query.
        """
        base = {"metadata": self.metadata.to_dict(), "is_batch": self.is_batch}

        if self.is_batch:
            return {**base, "results": [r.to_dict() for r in self.results]}
        else:
            # Single table: unwrap for simpler response
            return {
                **base,
                "result": self.results[0].to_dict() if self.results else None,
            }

    def to_markdown(self) -> str:
        """
        Generate markdown documentation for all results.

        Returns:
            Markdown string with all table documentation.
        """
        if not self.results:
            return "# No Results\n\nNo tables were discovered."

        sections = []

        # Add summary header for batch queries
        if self.is_batch:
            sections.append(f"# Discovery Results ({len(self.results)} tables)\n")
            sections.append(f"**Total Cost**: ${self.metadata.total_cost_usd:.4f}")
            sections.append(f"**Execution Time**: {self.metadata.execution_time_ms}ms")
            sections.append(
                f"**Cache Hits**: {self.metadata.cache_hits}/{len(self.results)}\n"
            )

        # Add each table's documentation
        for result in self.results:
            sections.append(result.documentation)

        return "\n\n".join(sections)


# Type alias for backward compatibility
DiscoveryOutput = DiscoveryResults
