"""
Discovery Assistant - AI-powered table profiling and documentation.

This module provides tools for discovering and documenting poorly-documented
Snowflake tables using statistical analysis and AI inference.

Main components:
- TableProfiler: SQL-based table profiling
- LLMAnalyzer: Cortex Complete business purpose inference
- RelationshipDiscoverer: Foreign key relationship detection
- DocumentationGenerator: Output formatting
"""

from snowcli_tools.discovery.models import (
    CachePolicy,
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

__all__ = [
    "CachePolicy",
    "ColumnMeaning",
    "ColumnProfile",
    "ConfidenceLevel",
    "DepthMode",
    "DiscoveryMetadata",
    "DiscoveryResult",
    "LLMAnalysis",
    "OutputFormat",
    "Relationship",
    "TableCategory",
    "TableProfile",
]
