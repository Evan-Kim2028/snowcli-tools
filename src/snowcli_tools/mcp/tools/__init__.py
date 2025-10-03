"""MCP tools package - individual tool implementations.

This package contains all MCP tool implementations extracted from the monolithic
mcp_server.py file as part of v1.8.0 Phase 2.2 refactoring.

Each tool is self-contained in its own file and follows the command pattern
using the MCPTool base class.

Part of v1.8.0 Phase 2.2 - MCP Server Simplification
"""

from __future__ import annotations

from .base import MCPTool, MCPToolSchema
from .execute_query import ExecuteQueryTool
from .health_check import HealthCheckTool

# TODO: Extract remaining tools:
# - PreviewTableTool
# - BuildCatalogTool
# - QueryLineageTool
# - BuildDependencyGraphTool
# - TestConnectionTool
# - GetCatalogSummaryTool
# - CheckProfileConfigTool
# - GetResourceStatusTool
# - CheckResourceDependenciesTool

__all__ = [
    "MCPTool",
    "MCPToolSchema",
    "ExecuteQueryTool",
    "HealthCheckTool",
]
