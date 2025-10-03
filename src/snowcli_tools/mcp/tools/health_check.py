"""Health Check MCP Tool - Check system health status.

Part of v1.8.0 Phase 2.2 - extracted from mcp_server.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...mcp_health import MCPHealthMonitor
from .base import MCPTool


class HealthCheckTool(MCPTool):
    """MCP tool for checking system health status."""

    def __init__(self, health_monitor: Optional[MCPHealthMonitor] = None):
        """Initialize health check tool.

        Args:
            health_monitor: Optional health monitoring instance
        """
        self.health_monitor = health_monitor

    @property
    def name(self) -> str:
        return "health_check"

    @property
    def description(self) -> str:
        return "Check system health and service status"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Check system health status.

        Returns:
            Health status including errors, metrics, and profile health
        """
        if not self.health_monitor:
            return {
                "status": "unknown",
                "message": "Health monitoring not available",
            }

        status = self.health_monitor.get_health_status()  # type: ignore[attr-defined]
        return {
            "status": status.status,
            "healthy": status.is_healthy,
            "error_count": status.error_count,
            "warning_count": status.warning_count,
            "metrics": {
                "total_queries": status.metrics.get("total_queries", 0),
                "successful_queries": status.metrics.get("successful_queries", 0),
                "failed_queries": status.metrics.get("failed_queries", 0),
            },
            "recent_errors": status.recent_errors[-5:] if status.recent_errors else [],
        }

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {"type": "object", "properties": {}}
