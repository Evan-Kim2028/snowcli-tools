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

    async def execute(
        self,
        resource_name: str,
        catalog_dir: str = "./data_catalogue",
        snowflake_service: Any = None,
        health_monitor: Any = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Check resource dependencies.

        Args:
            resource_name: Name of the resource to check
            catalog_dir: Catalog directory path
            snowflake_service: Snowflake service instance (optional)
            health_monitor: Health monitor instance (optional)

        Returns:
            Resource dependency information

        Raises:
            RuntimeError: If resource manager not available or check fails
        """
        from functools import partial

        import anyio

        if not self.resource_manager:
            raise RuntimeError(
                "Resource manager not available. "
                "Server may not be fully initialized."
            )

        try:
            # Get resource availability
            availability = await anyio.to_thread.run_sync(
                partial(
                    self.resource_manager.get_resource_availability,
                    resource_name,
                    snowflake_service,
                    catalog_dir=catalog_dir,
                )
            )

            # Get recommendations
            recommendations = self.resource_manager.get_resource_recommendations(
                resource_name, availability
            )

            # Get dependency information
            dependencies = self.resource_manager.dependencies.get(resource_name, [])

            return {
                "resource_name": resource_name,
                "availability": availability.to_dict(),
                "dependencies": dependencies,
                "recommendations": recommendations,
                "timestamp": anyio.current_time(),
            }

        except Exception as e:
            if health_monitor:
                health_monitor.record_error(f"Resource dependency check failed: {e}")
            raise RuntimeError(f"Failed to check resource dependencies: {e}") from e

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
