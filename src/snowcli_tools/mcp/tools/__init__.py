"""MCP tools package - individual tool implementations.

This package contains all MCP tool implementations extracted from the monolithic
mcp_server.py file as part of v1.8.0 Phase 2.2 refactoring.

Each tool is self-contained in its own file and follows the command pattern
using the MCPTool base class.

Part of v1.8.0 Phase 2.2 - MCP Server Simplification
"""

from __future__ import annotations

from .base import MCPTool, MCPToolSchema
from .build_catalog import BuildCatalogTool
from .build_dependency_graph import BuildDependencyGraphTool
from .check_profile_config import CheckProfileConfigTool
from .check_resource_dependencies import CheckResourceDependenciesTool
from .execute_query import ExecuteQueryTool
from .get_catalog_summary import GetCatalogSummaryTool
from .get_resource_status import GetResourceStatusTool
from .health_check import HealthCheckTool
from .preview_table import PreviewTableTool
from .query_lineage import QueryLineageTool
from .test_connection import ConnectionTestTool

__all__ = [
    "MCPTool",
    "MCPToolSchema",
    "BuildCatalogTool",
    "BuildDependencyGraphTool",
    "CheckProfileConfigTool",
    "CheckResourceDependenciesTool",
    "ExecuteQueryTool",
    "GetCatalogSummaryTool",
    "GetResourceStatusTool",
    "HealthCheckTool",
    "PreviewTableTool",
    "QueryLineageTool",
    "ConnectionTestTool",
]
