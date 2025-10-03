"""Check Resource Dependencies MCP Tool - Check dependencies for MCP resources.

Part of v1.8.0 Phase 2.2 - extracted from mcp_server.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...mcp_resources import MCPResourceManager
from .base import MCPTool


class CheckResourceDependenciesTool(MCPTool):
    """MCP tool for checking resource dependencies."""

    def __init__(self, resource_manager: Optional[MCPResourceManager] = None):
        """Initialize check resource dependencies tool.

        Args:
            resource_manager: Optional resource manager instance
        """
        self.resource_manager = resource_manager

    @property
    def name(self) -> str:
        return "check_resource_dependencies"

    @property
    def description(self) -> str:
        return "Check dependencies for MCP resources"

    async def execute(self, uri: str, **kwargs: Any) -> Dict[str, Any]:
        """Check resource dependencies.

        Args:
            uri: Resource URI to check dependencies for

        Returns:
            Resource dependency information

        Raises:
            ValueError: If URI is invalid
            RuntimeError: If resource manager not available or check fails
        """
        if not uri or not uri.strip():
            raise ValueError("Resource URI cannot be empty")

        if not self.resource_manager:
            raise RuntimeError("Resource manager not initialized")

        try:
            # Check if resource exists
            resource = self.resource_manager.get_resource(uri)  # type: ignore[attr-defined]
            if not resource:
                return {
                    "uri": uri,
                    "status": "not_found",
                    "dependencies": [],
                }

            # Get dependencies
            dependencies = self.resource_manager.get_dependencies(uri)  # type: ignore[attr-defined]

            return {
                "uri": uri,
                "status": "found",
                "dependency_count": len(dependencies) if dependencies else 0,
                "dependencies": dependencies if dependencies else [],
            }

        except Exception as e:
            raise RuntimeError(
                f"Failed to check resource dependencies for '{uri}': {e}"
            ) from e

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Resource URI to check dependencies for",
                },
            },
            "required": ["uri"],
        }
