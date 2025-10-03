"""Unified catalog module for Snowflake data cataloging.

This module consolidates catalog functionality that was previously spread across:
- catalog.py (core implementation)
- catalog_service.py (service layer classes)
- service_layer/catalog.py (wrapper service)

Part of v1.8.0 refactoring to reduce code duplication and improve maintainability.
"""

from __future__ import annotations

from .models import CatalogBuildResult, CatalogBuildTotals, CatalogMetadata
from .service import CatalogService, build_catalog, export_sql_from_catalog

__all__ = [
    "CatalogService",
    "build_catalog",
    "export_sql_from_catalog",
    "CatalogBuildResult",
    "CatalogBuildTotals",
    "CatalogMetadata",
]
