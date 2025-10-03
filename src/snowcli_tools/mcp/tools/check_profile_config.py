"""Check Profile Config MCP Tool - Validate Snowflake profile configuration.

Part of v1.8.0 Phase 2.2 - extracted from mcp_server.py.
"""

from __future__ import annotations

from typing import Any, Dict

import anyio

from ...config import Config
from ...profile_utils import ProfileValidationError, validate_and_resolve_profile
from .base import MCPTool


class CheckProfileConfigTool(MCPTool):
    """MCP tool for checking profile configuration."""

    def __init__(self, config: Config):
        """Initialize check profile config tool.

        Args:
            config: Application configuration
        """
        self.config = config

    @property
    def name(self) -> str:
        return "check_profile_config"

    @property
    def description(self) -> str:
        return "Validate Snowflake profile configuration and check credentials"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Check profile configuration.

        Returns:
            Profile validation results with status and details

        Raises:
            ValueError: If profile validation fails critically
        """
        profile = self.config.snowflake.profile

        try:
            # Validate profile
            resolved_profile = await anyio.to_thread.run_sync(
                validate_and_resolve_profile, profile
            )

            # Get profile summary
            from ...profile_utils import get_profile_summary

            summary = await anyio.to_thread.run_sync(
                get_profile_summary, resolved_profile
            )

            return {
                "status": "valid",
                "profile": resolved_profile,
                "config": {
                    "account": summary.get("account"),
                    "warehouse": summary.get("warehouse"),
                    "database": summary.get("database"),
                    "schema": summary.get("schema"),
                    "role": summary.get("role"),
                    "authenticator": summary.get("authenticator"),
                },
                "warnings": summary.get("warnings", []),
            }

        except ProfileValidationError as e:
            raise ValueError(
                f"Profile validation failed for '{profile}': {e}. "
                f"Check your Snowflake CLI configuration with 'snow connection list'."
            ) from e
        except Exception as e:
            raise ValueError(f"Failed to check profile configuration: {e}") from e

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {
            "type": "object",
            "properties": {},
        }
