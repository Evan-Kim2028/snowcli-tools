"""Test Connection MCP Tool - Test Snowflake connection.

Part of v1.8.0 Phase 2.2 - extracted from mcp_server.py.
"""

from __future__ import annotations

from typing import Any, Dict

from ...config import Config
from .base import MCPTool


class TestConnectionTool(MCPTool):
    """MCP tool for testing Snowflake connection."""

    def __init__(self, config: Config, snowflake_service: Any):
        """Initialize test connection tool.

        Args:
            config: Application configuration
            snowflake_service: Snowflake service instance
        """
        self.config = config
        self.snowflake_service = snowflake_service

    @property
    def name(self) -> str:
        return "test_connection"

    @property
    def description(self) -> str:
        return "Test Snowflake connection and verify credentials"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Test Snowflake connection.

        Returns:
            Connection test results with status and details

        Raises:
            RuntimeError: If connection test fails
        """
        import anyio

        try:
            result = await anyio.to_thread.run_sync(self._test_connection_sync)
            return {
                "status": "success",
                "connected": True,
                "profile": self.config.snowflake.profile,
                "warehouse": result.get("warehouse"),
                "database": result.get("database"),
                "schema": result.get("schema"),
                "role": result.get("role"),
            }
        except Exception as e:
            return {
                "status": "failed",
                "connected": False,
                "profile": self.config.snowflake.profile,
                "error": str(e),
            }

    def _test_connection_sync(self) -> Dict[str, Any]:
        """Test connection synchronously."""
        with self.snowflake_service.get_connection(
            use_dict_cursor=True,
            session_parameters=self.snowflake_service.get_query_tag_param(),
        ) as (_, cursor):
            # Get current session info
            cursor.execute("SELECT CURRENT_WAREHOUSE() as warehouse")
            warehouse_result = cursor.fetchone()

            cursor.execute("SELECT CURRENT_DATABASE() as database")
            database_result = cursor.fetchone()

            cursor.execute("SELECT CURRENT_SCHEMA() as schema")
            schema_result = cursor.fetchone()

            cursor.execute("SELECT CURRENT_ROLE() as role")
            role_result = cursor.fetchone()

            return {
                "warehouse": (
                    warehouse_result.get("warehouse") if warehouse_result else None
                ),
                "database": (
                    database_result.get("database") if database_result else None
                ),
                "schema": schema_result.get("schema") if schema_result else None,
                "role": role_result.get("role") if role_result else None,
            }

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {},
        }
