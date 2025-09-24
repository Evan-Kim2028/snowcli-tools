"""Lineage package exposes helpers to build and query Snowflake lineage graphs."""

from .builder import LineageBuilder
from .column_parser import ColumnLineageExtractor, ColumnLineageGraph, ColumnTransformation
from .cross_db import CrossDatabaseLineageBuilder, UnifiedLineageGraph
from .external import ExternalSourceMapper, ExternalLineage
from .graph import LineageGraph
from .history import LineageHistoryManager, LineageSnapshot, LineageDiff
from .impact import ImpactAnalyzer, ImpactReport, ChangeType
from .loader import CatalogLoader, CatalogObject
from .queries import LineageQueryService
from .transformations import TransformationTracker, TransformationMetadata

__all__ = [
    "CatalogLoader",
    "CatalogObject",
    "LineageBuilder",
    "LineageGraph",
    "LineageQueryService",
    # New Advanced Lineage Features
    "ColumnLineageExtractor",
    "ColumnLineageGraph",
    "ColumnTransformation",
    "TransformationTracker",
    "TransformationMetadata",
    "CrossDatabaseLineageBuilder",
    "UnifiedLineageGraph",
    "ExternalSourceMapper",
    "ExternalLineage",
    "ImpactAnalyzer",
    "ImpactReport",
    "ChangeType",
    "LineageHistoryManager",
    "LineageSnapshot",
    "LineageDiff",
]
