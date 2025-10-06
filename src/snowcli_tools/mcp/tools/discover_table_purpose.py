"""Discover Table Purpose MCP Tool - AI-powered table discovery.

Part of v1.10.0 Discovery Assistant - automatically profiles, analyzes,
and documents poorly-documented Snowflake tables using Cortex Complete.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

from ...discovery.documentation_generator import DocumentationGenerator
from ...discovery.llm_analyzer import LLMAnalyzer
from ...discovery.models import (
    CachePolicy,
    ConfidenceLevel,
    DepthMode,
    DiscoveryMetadata,
    DiscoveryResult,
    OutputFormat,
)
from ...discovery.profiler import TableProfiler
from ...discovery.relationship_discoverer import RelationshipDiscoverer
from ...snow_cli import SnowCLI
from .base import MCPTool

# Constants
MAX_TIMEOUT_SECONDS = 600  # 10 minutes
MIN_TIMEOUT_SECONDS = 5
MAX_BATCH_SIZE = 50  # Prevent runaway costs
MAX_COST_PER_DISCOVERY = 1.0  # $1.00 per discovery
DEFAULT_TIMEOUT = 60


class DiscoverTablePurposeTool(MCPTool):
    """MCP tool for discovering and documenting Snowflake tables using AI."""

    def __init__(self, snow_cli: SnowCLI):
        """Initialize discover table purpose tool.

        Args:
            snow_cli: SnowCLI instance for executing queries
        """
        self.snow_cli = snow_cli

    @property
    def name(self) -> str:
        return "discover_table_purpose"

    @property
    def description(self) -> str:
        return """Discover and document Snowflake tables using AI-powered analysis.

Automatically profiles tables, infers business purpose using Cortex Complete,
discovers relationships, and generates comprehensive documentation.

Use this when:
- Encountering unfamiliar or poorly-documented tables
- Need to understand table structure and purpose quickly
- Want to discover foreign key relationships
- Generating data catalog documentation

Supports three depth modes:
- quick: SQL profiling only (~5s, $0.01) - fast stats and patterns
- standard: + AI analysis (~15s, $0.05) - includes business purpose [DEFAULT]
- deep: + Relationship discovery (~25s, $0.08) - includes FK relationships

Supports batch discovery of multiple tables."""

    async def execute(
        self,
        table_name: str | list[str],
        database: Optional[str] = None,
        schema: Optional[str] = None,
        depth: str = "standard",
        output_format: str = "markdown",
        cache_policy: str = "if_fresh",
        timeout_seconds: int = DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute table discovery.

        Args:
            table_name: Table name(s) to discover (string or list)
            database: Database name (optional, uses session default)
            schema: Schema name (optional, uses session default)
            depth: Discovery depth (quick/standard/deep, default: standard)
            output_format: Output format (markdown/json, default: markdown)
            cache_policy: Cache behavior (always/if_fresh/never, default: if_fresh)
            timeout_seconds: Maximum execution time (default: 60)
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

        # Parse enums
        depth_mode = DepthMode(depth)
        out_format = OutputFormat(output_format)
        cache_pol = CachePolicy(cache_policy)

        # Handle batch discovery
        if isinstance(table_name, list):
            return await self._batch_discover(
                table_name,
                database,
                schema,
                depth_mode,
                out_format,
                cache_pol,
                timeout_seconds,
            )
        else:
            return await self._discover_single(
                table_name,
                database,
                schema,
                depth_mode,
                out_format,
                cache_pol,
                timeout_seconds,
            )

    async def _discover_single(
        self,
        table_name: str,
        database: Optional[str],
        schema: Optional[str],
        depth: DepthMode,
        output_format: OutputFormat,
        cache_policy: CachePolicy,
        timeout: int,
    ) -> Dict[str, Any]:
        """Discover single table.

        Args:
            table_name: Table name
            database: Database name (optional)
            schema: Schema name (optional)
            depth: Discovery depth mode
            output_format: Output format
            cache_policy: Cache policy
            timeout: Timeout in seconds

        Returns:
            Discovery result dictionary
        """
        start_time = time.time()

        try:
            # Check cache (if enabled)
            if cache_policy != CachePolicy.NEVER:
                cached = self._check_cache(table_name, database, schema, cache_policy)
                if cached:
                    return {
                        "success": True,
                        "documentation": cached,
                        "cache_hit": True,
                        "table_name": table_name,
                    }

            # Initialize components
            profiler = TableProfiler(self.snow_cli)

            # Step 1: Profile table (always)
            profile = profiler.profile_table(table_name, database, schema)

            # Step 2: Analyze with LLM (if depth >= standard)
            analysis = None
            if depth in [DepthMode.STANDARD, DepthMode.DEEP]:
                analyzer = LLMAnalyzer(self.snow_cli)
                analysis = analyzer.analyze_table(profile)

            # Step 3: Discover relationships (if depth = deep)
            relationships = []
            if depth == DepthMode.DEEP:
                discoverer = RelationshipDiscoverer(
                    self.snow_cli,
                    database or profile.database,
                    schema or profile.schema,
                )
                # Discover relationships for all columns
                for col in profile.columns:
                    col_rels = discoverer.discover_relationships(
                        profile.table_name, [col.name]
                    )
                    relationships.extend(col_rels)

            # Build metadata
            end_time = time.time()
            execution_ms = int((end_time - start_time) * 1000)

            # Estimate cost
            cost = self._estimate_cost(depth, len(profile.columns))

            # Determine confidence level
            confidence_level = ConfidenceLevel.LOW
            if analysis:
                if analysis.confidence >= 0.8:
                    confidence_level = ConfidenceLevel.HIGH
                elif analysis.confidence >= 0.6:
                    confidence_level = ConfidenceLevel.MEDIUM

            metadata = DiscoveryMetadata(
                execution_time_ms=execution_ms,
                estimated_cost_usd=cost,
                cache_hit=False,
                table_last_modified=profile.last_ddl or "",
                discovery_version="1.10.0",
                confidence_level=confidence_level,
                depth_mode=depth,
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

            # Cache result
            self._cache_result(table_name, database, schema, documentation, metadata)

            return {
                "success": True,
                "documentation": documentation,
                "cache_hit": False,
                "table_name": table_name,
                "execution_time_ms": execution_ms,
                "estimated_cost_usd": cost,
                "confidence_level": confidence_level.value,
                "depth_mode": depth.value,
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
        depth: DepthMode,
        output_format: OutputFormat,
        cache_policy: CachePolicy,
        timeout: int,
    ) -> Dict[str, Any]:
        """Batch discovery of multiple tables.

        Processes tables sequentially with error handling per table.

        Args:
            table_names: List of table names
            database: Database name (optional)
            schema: Schema name (optional)
            depth: Discovery depth mode
            output_format: Output format
            cache_policy: Cache policy
            timeout: Timeout in seconds

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
                    depth,
                    output_format,
                    cache_policy,
                    timeout,
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
            combined_docs.append(f"## Table {i+1}: {result['table_name']}")
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

    def _estimate_cost(self, depth: DepthMode, column_count: int) -> float:
        """Estimate discovery cost in USD.

        Based on Snowflake compute usage and Cortex Complete costs.

        Args:
            depth: Discovery depth mode
            column_count: Number of columns in table

        Returns:
            Estimated cost in USD

        Raises:
            ValueError: If estimated cost exceeds MAX_COST_PER_DISCOVERY
        """
        if depth == DepthMode.QUICK:
            cost = 0.01
        elif depth == DepthMode.STANDARD:
            # Base cost + per-column LLM cost
            cost = 0.05 + (column_count * 0.001)
        else:  # DEEP
            # Base cost + LLM + relationship discovery
            cost = 0.08 + (column_count * 0.002)

        # Cost limit check
        if cost > MAX_COST_PER_DISCOVERY:
            raise ValueError(
                f"Estimated cost ${cost:.2f} exceeds maximum ${MAX_COST_PER_DISCOVERY:.2f}. "
                f"Table has {column_count} columns. Consider using 'quick' or 'standard' depth mode."
            )

        return cost

    def _check_cache(
        self,
        table_name: str,
        database: Optional[str],
        schema: Optional[str],
        cache_policy: CachePolicy,
    ) -> Optional[str]:
        """Check discovery cache.

        Args:
            table_name: Table name
            database: Database name (optional)
            schema: Schema name (optional)
            cache_policy: Cache policy

        Returns:
            Cached documentation or None
        """
        # TODO: Implement cache checking logic in Milestone 5.2
        return None

    def _cache_result(
        self,
        table_name: str,
        database: Optional[str],
        schema: Optional[str],
        documentation: str,
        metadata: DiscoveryMetadata,
    ) -> None:
        """Cache discovery result.

        Args:
            table_name: Table name
            database: Database name (optional)
            schema: Schema name (optional)
            documentation: Generated documentation
            metadata: Discovery metadata
        """
        # TODO: Implement caching logic in Milestone 5.2
        pass
