"""Lineage package exposes helpers to build and query Snowflake lineage graphs."""

from .builder import LineageBuilder
from .column_parser import (
    ColumnLineageExtractor,
    ColumnLineageGraph,
    ColumnTransformation,
)

# New additions for code quality
from .constants import Formats, Limits, Patterns, Thresholds, Timeouts
from .cross_db import CrossDatabaseLineageBuilder, UnifiedLineageGraph
from .exceptions import LineageException, LineageParseError, ObjectNotFoundException
from .external import ExternalLineage, ExternalSourceMapper
from .factory import ConfigFactory, LineageFactory, ObjectFactory
from .graph import LineageGraph
from .history import LineageDiff, LineageHistoryManager, LineageSnapshot
from .impact import ChangeType, ImpactAnalyzer, ImpactReport
from .loader import CatalogLoader, CatalogObject
from .logging_config import get_logger, setup_logging
from .queries import LineageQueryService
from .transformations import TransformationMetadata, TransformationTracker

# Setup default logging
setup_logging(level="INFO")

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
    # New additions for code quality
    "Limits",
    "Timeouts",
    "Thresholds",
    "Patterns",
    "Formats",
    "LineageException",
    "LineageParseError",
    "ObjectNotFoundException",
    "LineageFactory",
    "ObjectFactory",
    "ConfigFactory",
    "setup_logging",
    "get_logger",
]
