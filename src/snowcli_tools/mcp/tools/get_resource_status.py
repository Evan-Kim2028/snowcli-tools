"""Get Resource Status MCP Tool - Get MCP resource status information.

Part of v1.8.0 Phase 2.2 - extracted from mcp_server.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...mcp_resources import MCPResourceManager
from .base import MCPTool


class GetResourceStatusTool(MCPTool):
    """MCP tool for getting resource status."""

    def __init__(self, resource_manager: Optional[MCPResourceManager] = None):
        """Initialize get resource status tool.

        Args:
            resource_manager: Optional resource manager instance
        """
        self.resource_manager = resource_manager

    @property
    def name(self) -> str:
        return "get_resource_status"

    @property
    def description(self) -> str:
        return "Get status information for MCP resources"

    async def execute(self, uri: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        """Get resource status.

        Args:
            uri: Optional specific resource URI to check

        Returns:
            Resource status information

        Raises:
            RuntimeError: If resource manager not available
        """
        if not self.resource_manager:
            return {
                "status": "unavailable",
                "message": "Resource manager not initialized",
            }

        try:
            if uri:
                # Get specific resource status
                resource = self.resource_manager.get_resource(uri)  # type: ignore[attr-defined]
                if resource:
                    return {
                        "uri": uri,
                        "status": "found",
                        "resource": resource,
                    }
                else:
                    return {
                        "uri": uri,
                        "status": "not_found",
                    }
            else:
                # Get all resources status
                resources = self.resource_manager.list_resources()  # type: ignore[attr-defined]
                return {
                    "status": "success",
                    "resource_count": len(resources) if resources else 0,
                    "resources": resources if resources else [],
                }

        except Exception as e:
            raise RuntimeError(f"Failed to get resource status: {e}") from e

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Specific resource URI to check (optional)",
                },
            },
        }
