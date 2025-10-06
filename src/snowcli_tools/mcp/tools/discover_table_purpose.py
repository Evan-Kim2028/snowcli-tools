"""Profile Table MCP Tool - SQL-based Snowflake table profiling.

Part of v1.10.0 Discovery Assistant - automatically profiles and documents
Snowflake tables using SQL-based analysis for fast, reliable metadata discovery.

This tool profiles Snowflake database tables (NOT business entities or packages),
providing schema information, statistics, and sample data.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

from ...discovery.cache import get_cache_manager
from ...discovery.documentation_generator import DocumentationGenerator
from ...discovery.llm_analyzer import LLMAnalyzer
from ...discovery.models import (
    ConfidenceLevel,
    DepthMode,
    DiscoveryMetadata,
    DiscoveryResult,
    OutputFormat,
    TableProfile,
)
from ...discovery.profiler import TableProfiler
from ...discovery.relationship_discoverer import RelationshipDiscoverer
from ...discovery.utils import parse_table_name
from ...snow_cli import SnowCLI
from .base import MCPTool

# Constants
MAX_TIMEOUT_SECONDS = 600  # 10 minutes
MIN_TIMEOUT_SECONDS = 5
MAX_BATCH_SIZE = 50  # Prevent runaway costs
MAX_COST_PER_DISCOVERY = 1.0  # $1.00 per discovery
DEFAULT_TIMEOUT = 60


class DiscoverTablePurposeTool(MCPTool):
    """MCP tool for profiling and documenting Snowflake tables using SQL-based analysis."""

    def __init__(self, snow_cli: SnowCLI):
        """Initialize discover table purpose tool.

        Args:
            snow_cli: SnowCLI instance for executing queries
        """
        self.snow_cli = snow_cli

    @property
    def name(self) -> str:
        return "profile_table"

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": ["string", "array"],
                    "description": (
                        "Table name or list of tables for batch discovery. "
                        "Supports fully-qualified names (DB.SCHEMA.TABLE)."
                    ),
                    "items": {"type": "string"},
                    "examples": [
                        "CUSTOMERS",
                        "PROD_DB.PUBLIC.ORDERS",
                        ["CUSTOMERS", "ORDERS", "PRODUCTS"],
                    ],
                },
                "database": {
                    "type": "string",
                    "description": "Database name (optional, uses session default)",
                },
                "schema": {
                    "type": "string",
                    "description": "Schema name (optional, uses session default)",
                },
                "include_relationships": {
                    "type": "boolean",
                    "description": (
                        "Discover foreign key relationships between tables. "
                        "Adds ~$0.03 and ~10s per table. "
                        "Useful when planning JOINs or understanding schema."
                    ),
                    "default": False,
                },
                "output_format": {
                    "type": "string",
                    "enum": ["markdown", "json"],
                    "description": (
                        "Output format for documentation. 'markdown' for human-readable docs, "
                        "'json' for structured programmatic access."
                    ),
                    "default": "markdown",
                },
                "include_ai_analysis": {
                    "type": "boolean",
                    "description": (
                        "Use AI to infer business context and column meanings. "
                        "When false, returns only SQL profiling ($0.01, fast). "
                        "When true, adds semantic analysis ($0.05, slower but insightful)."
                    ),
                    "default": True,
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": (
                        "Maximum execution time in seconds for entire operation. "
                        "For large tables (>100 columns), consider 120s. "
                        "For batch operations, scale accordingly."
                    ),
                    "default": 60,
                    "minimum": 5,
                    "maximum": 600,
                },
                "force_refresh": {
                    "type": "boolean",
                    "description": (
                        "Bypass cache and force fresh analysis. "
                        "Useful for debugging or when table metadata is stale. "
                        "Note: Results are normally cached for 1 hour."
                    ),
                    "default": False,
                },
            },
            "required": ["table_name"],
        }

    @property
    def description(self) -> str:
        return """Profile Snowflake database tables with SQL-based analysis.

Automatically profiles tables with column statistics, data types, cardinality,
null rates, and sample values. Fast and reliable for data catalog documentation.

NOTE: This tool profiles Snowflake TABLE STRUCTURES (schema, stats, samples),
NOT business entities, packages, or domain objects. Use this to understand
what columns exist in a table, not to discover business logic or purpose.

Use this when:
- Encountering unfamiliar or poorly-documented Snowflake tables
- Need to understand table schema quickly
- Generating data catalog documentation
- Analyzing table metadata and statistics

Cost Model:
- SQL profiling: ~$0.01 per table

Performance:
- Profiling: ~2-5s per table

Supports batch profiling of multiple tables with automatic caching."""

    async def execute(
        self,
        table_name: str | list[str],
        database: Optional[str] = None,
        schema: Optional[str] = None,
        include_relationships: bool = False,
        output_format: str = "markdown",
        include_ai_analysis: bool = True,
        timeout_seconds: int = DEFAULT_TIMEOUT,
        force_refresh: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute table discovery.

        Args:
            table_name: Table name(s) to discover (string or list).
                       Supports fully-qualified names (DB.SCHEMA.TABLE).
            database: Database name (optional, uses session default)
            schema: Schema name (optional, uses session default)
            include_relationships: Discover foreign key relationships between tables.
                                  Adds ~$0.03 and ~10s per table. (default: False)
            output_format: Output format (markdown/json, default: markdown)
            include_ai_analysis: Use AI to infer business context and column meanings.
                               When False, returns SQL profiling only (fast, $0.01).
                               When True, adds AI analysis ($0.05). (default: True)
            timeout_seconds: Maximum execution time in seconds (default: 60)
            force_refresh: Bypass cache and force fresh analysis. (default: False)
            **kwargs: Additional arguments

        Returns:
            Discovery results with documentation

        Raises:
            ValueError: If input validation fails
        """
        # Input validation
        if (
            timeout_seconds < MIN_TIMEOUT_SECONDS
            or timeout_seconds > MAX_TIMEOUT_SECONDS
        ):
            raise ValueError(
                f"timeout_seconds must be between {MIN_TIMEOUT_SECONDS} and "
                f"{MAX_TIMEOUT_SECONDS}, got {timeout_seconds}"
            )

        if isinstance(table_name, list):
            if len(table_name) == 0:
                raise ValueError("table_name list cannot be empty")
            if len(table_name) > MAX_BATCH_SIZE:
                raise ValueError(
                    f"Batch size limited to {MAX_BATCH_SIZE} tables, got {len(table_name)}"
                )

        # Parse output format enum
        out_format = OutputFormat(output_format)

        # Handle batch discovery
        if isinstance(table_name, list):
            return await self._batch_discover(
                table_name,
                database,
                schema,
                include_relationships,
                include_ai_analysis,
                out_format,
                timeout_seconds,
                force_refresh,
            )
        else:
            return await self._discover_single(
                table_name,
                database,
                schema,
                include_relationships,
                include_ai_analysis,
                out_format,
                timeout_seconds,
                force_refresh,
            )

    async def _discover_single(
        self,
        table_name: str,
        database: Optional[str],
        schema: Optional[str],
        include_relationships: bool,
        include_ai_analysis: bool,
        output_format: OutputFormat,
        timeout: int,
        force_refresh: bool,
    ) -> Dict[str, Any]:
        """Discover single table.

        Args:
            table_name: Table name
            database: Database name (optional)
            schema: Schema name (optional)
            include_relationships: Whether to discover relationships
            include_ai_analysis: Whether to run AI analysis
            output_format: Output format
            timeout: Timeout in seconds
            force_refresh: Whether to bypass cache

        Returns:
            Discovery result dictionary
        """
        start_time = time.time()
        components_run = []

        try:
            # Initialize components
            profiler = TableProfiler(self.snow_cli)
            cache_manager = get_cache_manager()

            # Resolve identifiers without running a full profile when possible
            profile: Optional[TableProfile] = None
            resolved_db, resolved_schema, resolved_table = parse_table_name(
                table_name, database, schema
            )

            fq_table_parts = [
                part for part in [resolved_db, resolved_schema, resolved_table] if part
            ]
            fq_table_name = ".".join(fq_table_parts) if fq_table_parts else table_name

            # Helper to lazily load the full profile only once
            def get_profile() -> TableProfile:
                nonlocal profile, resolved_db, resolved_schema, resolved_table, fq_table_name
                if profile is None:
                    profile = profiler.profile_table(table_name, database, schema)
                    resolved_db = profile.database
                    resolved_schema = profile.schema
                    resolved_table = profile.table_name
                    fq_table_name = (
                        f"{resolved_db}.{resolved_schema}.{resolved_table}"
                        if resolved_db and resolved_schema
                        else profile.table_name
                    )
                return profile

            # If we still lack a fully-qualified name, resolve via profiling once
            if not (resolved_db and resolved_schema):
                profile = get_profile()

            # Helper function to get current DDL timestamp
            def get_current_ddl() -> str:
                nonlocal resolved_db, resolved_schema, resolved_table
                if resolved_db and resolved_schema:
                    ddl = profiler._get_last_ddl(
                        resolved_db, resolved_schema, resolved_table
                    )
                    if ddl:
                        return ddl
                current_profile = get_profile()
                return current_profile.last_ddl or ""

            # Try cache first
            cached_result = cache_manager.get_cached_result(
                table_name=fq_table_name,
                include_relationships=include_relationships,
                include_ai_analysis=include_ai_analysis,
                current_ddl_getter=get_current_ddl,
                force_refresh=force_refresh,
            )

            if cached_result:
                # Cache hit - return cached result
                return {
                    "success": True,
                    "documentation": cached_result.documentation,
                    "cache_hit": True,
                    "table_name": table_name,
                    "execution_time_ms": 0,
                    "estimated_cost_usd": 0.0,
                }

            # Step 1: Profile table (always)
            profile = get_profile()
            components_run.append("profiler")

            # Step 2: Analyze with LLM (if include_ai_analysis=True)
            analysis = None
            if include_ai_analysis:
                analyzer = LLMAnalyzer(self.snow_cli)
                analysis = analyzer.analyze_table(profile)
                components_run.append("llm_analyzer")

            # Step 3: Discover relationships (if include_relationships=True)
            relationships = []
            if include_relationships:
                discoverer = RelationshipDiscoverer(
                    self.snow_cli,
                    resolved_db or profile.database,
                    resolved_schema or profile.schema,
                )
                # Discover relationships for all columns
                for col in profile.columns:
                    col_rels = discoverer.discover_relationships(
                        profile.table_name, [col.name]
                    )
                    relationships.extend(col_rels)
                components_run.append("relationship_discoverer")

            # Build metadata
            end_time = time.time()
            execution_ms = int((end_time - start_time) * 1000)

            # Estimate cost
            cost = self._estimate_cost_new(
                include_ai_analysis, include_relationships, len(profile.columns)
            )

            # Determine confidence level (for backward compat with DiscoveryMetadata)
            confidence_level = ConfidenceLevel.LOW
            if analysis:
                if analysis.confidence >= 0.8:
                    confidence_level = ConfidenceLevel.HIGH
                elif analysis.confidence >= 0.6:
                    confidence_level = ConfidenceLevel.MEDIUM

            # Map to old DepthMode for backward compatibility
            depth_mode = DepthMode.QUICK
            if include_ai_analysis and include_relationships:
                depth_mode = DepthMode.DEEP
            elif include_ai_analysis:
                depth_mode = DepthMode.STANDARD

            metadata = DiscoveryMetadata(
                execution_time_ms=execution_ms,
                estimated_cost_usd=cost,
                cache_hit=False,
                table_last_modified=profile.last_ddl or "",
                discovery_version="1.10.0",
                confidence_level=confidence_level,
                depth_mode=depth_mode,
                timestamp=datetime.now().isoformat(),
            )

            # Build result
            result = DiscoveryResult(
                profile=profile,
                analysis=analysis,
                relationships=relationships,
                documentation="",
                metadata=metadata,
            )

            # Generate documentation
            generator = DocumentationGenerator()
            documentation = generator.generate(result, output_format)
            result.documentation = documentation

            # Cache result
            cache_manager.cache_result(
                table_name=fq_table_name,
                result=result,
                include_relationships=include_relationships,
                include_ai_analysis=include_ai_analysis,
                table_last_ddl=profile.last_ddl or "",
            )

            return {
                "success": True,
                "documentation": documentation,
                "cache_hit": False,
                "table_name": table_name,
                "execution_time_ms": execution_ms,
                "estimated_cost_usd": cost,
                "confidence_level": confidence_level.value,
                "components_run": components_run,
            }

        except Exception as e:
            # Generate error documentation
            generator = DocumentationGenerator()
            error_doc = generator.format_error(table_name, e)

            return {
                "success": False,
                "documentation": error_doc,
                "error": str(e),
                "table_name": table_name,
            }

    async def _batch_discover(
        self,
        table_names: list[str],
        database: Optional[str],
        schema: Optional[str],
        include_relationships: bool,
        include_ai_analysis: bool,
        output_format: OutputFormat,
        timeout: int,
        force_refresh: bool,
    ) -> Dict[str, Any]:
        """Batch discovery of multiple tables.

        Processes tables sequentially with error handling per table.

        Args:
            table_names: List of table names
            database: Database name (optional)
            schema: Schema name (optional)
            include_relationships: Whether to discover relationships
            include_ai_analysis: Whether to run AI analysis
            output_format: Output format
            timeout: Timeout in seconds
            force_refresh: Whether to bypass cache

        Returns:
            Combined results for all tables
        """
        results = []
        successful = 0
        failed = 0

        for table_name in table_names:
            try:
                result = await self._discover_single(
                    table_name,
                    database,
                    schema,
                    include_relationships,
                    include_ai_analysis,
                    output_format,
                    timeout,
                    force_refresh,
                )
                results.append(result)
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                # Include error in results (don't fail entire batch)
                generator = DocumentationGenerator()
                error_doc = generator.format_error(table_name, e)
                results.append(
                    {
                        "success": False,
                        "documentation": error_doc,
                        "error": str(e),
                        "table_name": table_name,
                    }
                )
                failed += 1

        # Combine documentation
        combined_docs = []
        for i, result in enumerate(results):
            combined_docs.append(f"## Table {i + 1}: {result['table_name']}")
            combined_docs.append("")
            combined_docs.append(result["documentation"])
            combined_docs.append("")
            combined_docs.append("---")
            combined_docs.append("")

        return {
            "success": successful > 0,
            "documentation": "\n".join(combined_docs),
            "batch_summary": {
                "total": len(table_names),
                "successful": successful,
                "failed": failed,
            },
            "results": results,
        }

    def _estimate_cost_new(
        self, include_ai_analysis: bool, include_relationships: bool, column_count: int
    ) -> float:
        """Estimate discovery cost in USD (new simplified interface).

        Based on Snowflake compute usage and Cortex Complete costs.

        Args:
            include_ai_analysis: Whether AI analysis is included
            include_relationships: Whether relationship discovery is included
            column_count: Number of columns in table

        Returns:
            Estimated cost in USD

        Raises:
            ValueError: If estimated cost exceeds MAX_COST_PER_DISCOVERY
        """
        # Base profiling cost
        cost = 0.01

        # Add AI analysis cost
        if include_ai_analysis:
            cost += 0.04 + (column_count * 0.001)

        # Add relationship discovery cost
        if include_relationships:
            cost += 0.03 + (column_count * 0.002)

        # Cost limit check
        if cost > MAX_COST_PER_DISCOVERY:
            raise ValueError(
                f"Estimated cost ${cost:.2f} exceeds maximum ${MAX_COST_PER_DISCOVERY:.2f}. "
                f"Table has {column_count} columns. Consider using include_ai_analysis=False "
                f"or include_relationships=False to reduce cost."
            )

        return cost

    def _estimate_cost(self, depth: DepthMode, column_count: int) -> float:
        """Estimate discovery cost in USD (deprecated - for backward compatibility).

        Args:
            depth: Discovery depth mode
            column_count: Number of columns in table

        Returns:
            Estimated cost in USD
        """
        # Map old depth mode to new parameters
        if depth == DepthMode.QUICK:
            return self._estimate_cost_new(False, False, column_count)
        elif depth == DepthMode.STANDARD:
            return self._estimate_cost_new(True, False, column_count)
        else:  # DEEP
            return self._estimate_cost_new(True, True, column_count)
