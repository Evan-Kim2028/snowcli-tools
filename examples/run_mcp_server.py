#!/usr/bin/env python3
"""Example: Start the MCP server for AI assistant integration.

This example demonstrates how to start the MCP server that provides AI assistants
like VS Code, Cursor, and Claude Code with direct access to your Snowflake data.

Usage:
    # Start the MCP server directly
    uv run python examples/run_mcp_server.py

    # Or use the CLI command
    uv run snowflake-cli mcp

The server provides tools for:
- Executing SQL queries
- Building data catalogs
- Querying lineage information
- Generating dependency graphs
- Previewing table data
- Testing connections

Prerequisites:
- Configure a Snowflake CLI connection (e.g., `uv run snow connection add ...`)
- Ensure your SNOWFLAKE_PROFILE is set or pass --profile to the CLI
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def print_usage_info():
    """Print information about how to use the MCP server."""
    print("🚀 Snowflake MCP Server Example")
    print("=" * 40)
    print()
    print("This example starts an MCP (Model Context Protocol) server that provides")
    print("AI assistants with direct access to your Snowflake data and metadata.")
    print()
    print("Available MCP Tools:")
    print("• execute_query      - Run SQL queries against Snowflake")
    print("• preview_table      - Preview table contents")
    print("• build_catalog      - Generate data catalogs")
    print("• query_lineage      - Analyze data lineage")
    print("• build_dependency_graph - Create dependency graphs")
    print("• test_connection    - Test Snowflake connection")
    print("• get_catalog_summary - Get catalog summaries")
    print()
    print("Usage with AI Assistants:")
    print("1. VS Code/Cursor: Configure MCP server in settings")
    print("2. Claude Code: Add to MCP configuration")
    print("3. Other MCP clients: Use stdio transport")
    print()
    print("Press Ctrl+C to stop the server")
    print()


async def main():
    """Start the MCP server."""
    print_usage_info()

    print("⚠️  Note: This example shows usage information.")
    print("💡 To actually start the MCP server, use:")
    print("   uv run snowflake-cli mcp")
    print()
    print("The MCP server requires stdio interaction with AI assistants.")
    print("This example cannot run the server directly in a terminal.")
    print()
    print("For more information, see the MCP Server Integration section in README.md")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
