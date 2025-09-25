"""MCP Server for Snowflake CLI Tools.

A simple MCP server that exposes snowcli-tools functionality to AI assistants
like VS Code, Cursor, and Claude Code.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import mcp.server.stdio
from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions

# Version compatibility detection
try:
    # Check if the new get_capabilities API exists by testing the signature
    import inspect

    from mcp.server import Server

    test_server = Server("test")
    sig = inspect.signature(test_server.get_capabilities)
    # New API has parameters, old API doesn't
    MCP_NEW_API = len(sig.parameters) > 0
except Exception:
    MCP_NEW_API = False

try:
    import mcp

    # Check if package has __version__ or try to determine from setup
    MCP_VERSION = getattr(mcp, "__version__", "unknown")
except Exception:
    MCP_VERSION = "0.0.0"

from .catalog import build_catalog
from .config import get_config
from .dependency import build_dependency_graph, to_dot
from .lineage import LineageQueryService
from .snow_cli import SnowCLI, SnowCLIError


class SnowflakeMCPServer:
    """Simple MCP server for snowcli-tools."""

    def __init__(self):
        self.server = Server("snowflake-cli-tools")
        self.snow_cli = SnowCLI()
        self.config = get_config()

    def _get_server_capabilities(self):
        """Get server capabilities with version compatibility."""
        if MCP_NEW_API:
            try:
                # New API requires notification_options and experimental_capabilities
                return self.server.get_capabilities(
                    notification_options=None,  # Use None or {} for basic setup
                    experimental_capabilities={},
                )
            except Exception:
                # Fallback to old API if new API fails
                return self.server.get_capabilities()
        else:
            # Use old API for older MCP versions
            return self.server.get_capabilities()

    async def _verify_components(self) -> bool:
        """Verify that all required components are available and functional."""
        try:
            # Test Snowflake connection
            if not self.config:
                print("Warning: No configuration found")
                return False

            # Test if we can create a basic query service
            LineageQueryService(self.snow_cli)

            return True
        except Exception as e:
            print(f"Component verification failed: {e}")
            return False

    async def run(self):
        """Run the MCP server."""

        # Set up handlers
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="execute_query",
                    description="Execute a SQL query against Snowflake",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute",
                            },
                            "warehouse": {
                                "type": "string",
                                "description": "Warehouse to use (optional)",
                            },
                            "database": {
                                "type": "string",
                                "description": "Database to use (optional)",
                            },
                            "schema": {
                                "type": "string",
                                "description": "Schema to use (optional)",
                            },
                            "role": {
                                "type": "string",
                                "description": "Role to use (optional)",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                types.Tool(
                    name="preview_table",
                    description="Preview the contents of a Snowflake table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of table to preview",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of rows to preview",
                                "default": 100,
                            },
                            "warehouse": {
                                "type": "string",
                                "description": "Warehouse to use (optional)",
                            },
                            "database": {
                                "type": "string",
                                "description": "Database to use (optional)",
                            },
                            "schema": {
                                "type": "string",
                                "description": "Schema to use (optional)",
                            },
                            "role": {
                                "type": "string",
                                "description": "Role to use (optional)",
                            },
                        },
                        "required": ["table_name"],
                    },
                ),
                types.Tool(
                    name="build_catalog",
                    description="Build a data catalog from Snowflake metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory",
                                "default": "./data_catalogue",
                            },
                            "database": {
                                "type": "string",
                                "description": "Specific database (optional)",
                            },
                            "account": {
                                "type": "boolean",
                                "description": "Include entire account",
                                "default": False,
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (json/jsonl)",
                                "default": "json",
                            },
                            "include_ddl": {
                                "type": "boolean",
                                "description": "Include DDL in output",
                                "default": True,
                            },
                        },
                    },
                ),
                types.Tool(
                    name="query_lineage",
                    description="Query data lineage for a Snowflake object",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of object to analyze",
                            },
                            "direction": {
                                "type": "string",
                                "description": "Direction (upstream/downstream/both)",
                                "default": "both",
                            },
                            "depth": {
                                "type": "integer",
                                "description": "Traversal depth",
                                "default": 3,
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (text/json/html)",
                                "default": "text",
                            },
                            "catalog_dir": {
                                "type": "string",
                                "description": "Catalog directory",
                                "default": "./data_catalogue",
                            },
                            "cache_dir": {
                                "type": "string",
                                "description": "Cache directory",
                                "default": "./lineage",
                            },
                        },
                        "required": ["object_name"],
                    },
                ),
                types.Tool(
                    name="build_dependency_graph",
                    description="Build dependency graph for Snowflake objects",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "Specific database (optional)",
                            },
                            "schema": {
                                "type": "string",
                                "description": "Specific schema (optional)",
                            },
                            "account": {
                                "type": "boolean",
                                "description": "Include entire account",
                                "default": False,
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (json/dot)",
                                "default": "json",
                            },
                        },
                    },
                ),
                types.Tool(
                    name="test_connection",
                    description="Test the Snowflake connection",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="get_catalog_summary",
                    description="Get summary of existing catalog data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "catalog_dir": {
                                "type": "string",
                                "description": "Catalog directory",
                                "default": "./data_catalogue",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent]:
            try:
                if name == "execute_query":
                    result = self._execute_query(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "preview_table":
                    result = self._preview_table(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "build_catalog":
                    result = self._build_catalog(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "query_lineage":
                    result = self._query_lineage(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "build_dependency_graph":
                    result = self._build_dependency_graph(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "test_connection":
                    result = self._test_connection()
                    return [types.TextContent(type="text", text=result)]
                elif name == "get_catalog_summary":
                    result = self._get_catalog_summary(**arguments)
                    return [types.TextContent(type="text", text=result)]
                else:
                    raise Exception(f"Unknown tool: {name}")
            except Exception as e:
                raise Exception(f"Error calling tool {name}: {str(e)}")

        # Verify components before starting server
        if not await self._verify_components():
            raise RuntimeError(
                "Component verification failed - check configuration and dependencies"
            )

        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="snowflake-cli-tools",
                    server_version="1.0.0",
                    capabilities=self._get_server_capabilities(),
                ),
            )

    def _execute_query(
        self,
        query: str,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
    ) -> str:
        """Execute a SQL query."""
        ctx = {
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }
        ctx = {k: v for k, v in ctx.items() if v is not None}

        try:
            result = self.snow_cli.run_query(
                query, output_format="json", ctx_overrides=ctx
            )
            if result.rows:
                return json.dumps(result.rows, indent=2, default=str)
            else:
                return result.raw_stdout
        except SnowCLIError as e:
            # Use standard exception for now - McpError needs ErrorData object
            raise Exception(f"Query execution failed: {e}")

    def _preview_table(
        self,
        table_name: str,
        limit: int = 100,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
    ) -> str:
        """Preview table contents."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self._execute_query(query, warehouse, database, schema, role)

    def _build_catalog(
        self,
        output_dir: str = "./data_catalogue",
        database: Optional[str] = None,
        account: bool = False,
        format: str = "json",
        include_ddl: bool = True,
    ) -> str:
        """Build data catalog."""
        try:
            totals = build_catalog(
                output_dir,
                database=database,
                account_scope=account,
                incremental=False,
                output_format=format,
                include_ddl=include_ddl,
                max_ddl_concurrency=8,
                catalog_concurrency=16,
                export_sql=False,
            )

            return json.dumps(
                {
                    "success": True,
                    "message": f"Catalog built successfully in {output_dir}",
                    "totals": totals,
                },
                indent=2,
            )

        except Exception as e:
            raise Exception(f"Catalog build failed: {e}")

    def _query_lineage(
        self,
        object_name: str,
        direction: str = "both",
        depth: int = 3,
        format: str = "text",
        catalog_dir: str = "./data_catalogue",
        cache_dir: str = "./lineage",
    ) -> str:
        """Query lineage data."""
        try:
            service = LineageQueryService(catalog_dir, cache_dir)

            # Try to find the object
            default_db = self.config.snowflake.database
            default_schema = self.config.snowflake.schema

            from .lineage.identifiers import parse_table_name

            qn = parse_table_name(object_name).with_defaults(default_db, default_schema)
            base_object_key = qn.key()
            candidate_keys = [base_object_key]
            if not base_object_key.endswith("::task"):
                candidate_keys.append(f"{base_object_key}::task")

            result = None
            resolved_key = None

            for candidate in candidate_keys:
                try:
                    result = service.object_subgraph(
                        candidate, direction=direction, depth=depth
                    )
                    resolved_key = candidate
                    break
                except KeyError:
                    continue

            if result is None:
                return f"Object '{object_name}' not found in lineage graph. Try running catalog build first."

            if format == "json":
                return json.dumps(
                    {
                        "object": resolved_key,
                        "direction": direction,
                        "depth": depth,
                        "nodes": len(result.graph.nodes),
                        "edges": len(result.graph.edge_metadata),
                        "graph": (
                            result.graph.to_dict()
                            if hasattr(result.graph, "to_dict")
                            else str(result.graph)
                        ),
                    },
                    indent=2,
                    default=str,
                )
            else:
                # Text format - return summary
                return f"""Lineage Analysis for {resolved_key}:
Direction: {direction}
Depth: {depth}
Nodes: {len(result.graph.nodes)}
Edges: {len(result.graph.edge_metadata)}

Objects found:
{chr(10).join(f"- {node.attributes.get('name', key)} ({node.node_type.value})"
              for key, node in result.graph.nodes.items())}"""

        except Exception as e:
            raise Exception(f"Lineage query failed: {e}")

    def _build_dependency_graph(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        account: bool = False,
        format: str = "json",
    ) -> str:
        """Build dependency graph."""
        try:
            graph = build_dependency_graph(
                database=database, schema=schema, account_scope=account
            )

            if format == "dot":
                return to_dot(graph)
            else:
                return json.dumps(graph, indent=2, default=str)

        except Exception as e:
            raise Exception(f"Dependency graph build failed: {e}")

    def _test_connection(self) -> str:
        """Test connection."""
        try:
            success = self.snow_cli.test_connection()
            if success:
                return "Connection successful!"
            else:
                return "Connection failed!"
        except Exception as e:
            raise Exception(f"Connection test failed: {e}")

    def _get_catalog_summary(self, catalog_dir: str = "./data_catalogue") -> str:
        """Get catalog summary."""
        try:
            summary_file = os.path.join(catalog_dir, "catalog_summary.json")
            if os.path.exists(summary_file):
                with open(summary_file, "r") as f:
                    summary = json.load(f)
                return json.dumps(summary, indent=2)
            else:
                return f"No catalog summary found in {catalog_dir}. Run build_catalog first."
        except Exception as e:
            raise Exception(f"Failed to read catalog summary: {e}")


async def main():
    """Main entry point for MCP server."""
    server = SnowflakeMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
