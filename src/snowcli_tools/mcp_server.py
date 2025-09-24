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

from .catalog import build_catalog
from .config import get_config
from .dependency import build_dependency_graph, to_dot
from .lineage import (
    LineageQueryService,
    ColumnLineageExtractor,
    TransformationTracker,
    ImpactAnalyzer,
    ChangeType,
    ExternalSourceMapper,
    LineageHistoryManager,
)
from .snow_cli import SnowCLI, SnowCLIError


class SnowflakeMCPServer:
    """Simple MCP server for snowcli-tools."""

    def __init__(self):
        self.server = Server("snowflake-cli-tools")
        self.snow_cli = SnowCLI()
        self.config = get_config()

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
                # Advanced Lineage Tools
                types.Tool(
                    name="extract_column_lineage",
                    description="Extract column-level lineage from SQL query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL query to analyze",
                            },
                            "target_table": {
                                "type": "string",
                                "description": "Target table name (optional)",
                            },
                            "database": {
                                "type": "string",
                                "description": "Default database context",
                            },
                            "schema": {
                                "type": "string",
                                "description": "Default schema context",
                            },
                        },
                        "required": ["sql"],
                    },
                ),
                types.Tool(
                    name="analyze_impact",
                    description="Analyze impact of changes to database objects",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Object to analyze",
                            },
                            "change_type": {
                                "type": "string",
                                "description": "Type of change (DROP, ALTER_SCHEMA, etc.)",
                                "enum": ["DROP", "ALTER_SCHEMA", "ALTER_DATA_TYPE", "DROP_COLUMN", "RENAME", "MODIFY_LOGIC"],
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum traversal depth",
                                "default": 5,
                            },
                            "catalog_dir": {
                                "type": "string",
                                "description": "Catalog directory",
                                "default": "./data_catalogue",
                            },
                        },
                        "required": ["object_name", "change_type"],
                    },
                ),
                types.Tool(
                    name="map_external_sources",
                    description="Map external data sources (S3, Azure, GCS)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "catalog_dir": {
                                "type": "string",
                                "description": "Catalog directory",
                                "default": "./data_catalogue",
                            },
                            "include_stages": {
                                "type": "boolean",
                                "description": "Include stage configurations",
                                "default": True,
                            },
                            "include_external_tables": {
                                "type": "boolean",
                                "description": "Include external table mappings",
                                "default": True,
                            },
                        },
                    },
                ),
                types.Tool(
                    name="track_lineage_history",
                    description="Track lineage evolution over time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Action to perform",
                                "enum": ["snapshot", "compare", "list", "rollback"],
                            },
                            "catalog_dir": {
                                "type": "string",
                                "description": "Catalog directory for snapshot",
                                "default": "./data_catalogue",
                            },
                            "tag": {
                                "type": "string",
                                "description": "Snapshot tag",
                            },
                            "description": {
                                "type": "string",
                                "description": "Snapshot description",
                            },
                            "from_tag": {
                                "type": "string",
                                "description": "From snapshot for comparison",
                            },
                            "to_tag": {
                                "type": "string",
                                "description": "To snapshot for comparison",
                            },
                        },
                        "required": ["action"],
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
                # Advanced Lineage Tools
                elif name == "extract_column_lineage":
                    result = self._extract_column_lineage(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "analyze_impact":
                    result = self._analyze_impact(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "map_external_sources":
                    result = self._map_external_sources(**arguments)
                    return [types.TextContent(type="text", text=result)]
                elif name == "track_lineage_history":
                    result = self._track_lineage_history(**arguments)
                    return [types.TextContent(type="text", text=result)]
                else:
                    raise Exception(f"Unknown tool: {name}")
            except Exception as e:
                raise Exception(f"Error calling tool {name}: {str(e)}")

        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="snowflake-cli-tools",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(),
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

    # Advanced Lineage Feature Methods
    def _extract_column_lineage(
        self,
        sql: str,
        target_table: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> str:
        """Extract column-level lineage from SQL."""
        try:
            extractor = ColumnLineageExtractor(
                default_database=database, default_schema=schema
            )
            lineage = extractor.extract_column_lineage(sql, target_table=target_table)

            result = {
                "success": True,
                "transformations": [t.to_dict() for t in lineage.transformations],
                "column_dependencies": {
                    k: list(v) for k, v in lineage.column_dependencies.items()
                },
                "issues": lineage.issues,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            raise Exception(f"Column lineage extraction failed: {e}")

    def _analyze_impact(
        self,
        object_name: str,
        change_type: str,
        max_depth: int = 5,
        catalog_dir: str = "./data_catalogue",
    ) -> str:
        """Analyze impact of changes."""
        try:
            from pathlib import Path
            from .lineage.builder import LineageBuilder

            # Build lineage from catalog
            builder = LineageBuilder(Path(catalog_dir))
            lineage_result = builder.build()

            # Convert change_type string to enum
            change_type_enum = ChangeType[change_type.upper()]

            # Create impact analyzer
            analyzer = ImpactAnalyzer(lineage_result.graph)
            report = analyzer.analyze_impact(object_name, change_type_enum, max_depth)

            # Format report for output
            result = {
                "object": report.source_object,
                "change_type": report.change_type.value,
                "total_impacted": report.total_impacted_objects,
                "risk_score": report.risk_score,
                "critical_paths": [
                    {
                        "path": [p.object_name for p in path.path],
                        "impact_score": path.total_impact_score
                    }
                    for path in report.critical_paths
                ],
                "recommendations": report.recommendations,
                "impact_summary": report.impact_summary,
                "notification_list": report.notification_list,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            raise Exception(f"Impact analysis failed: {e}")

    def _map_external_sources(
        self,
        catalog_dir: str = "./data_catalogue",
        include_stages: bool = True,
        include_external_tables: bool = True,
    ) -> str:
        """Map external data sources."""
        try:
            from pathlib import Path

            mapper = ExternalSourceMapper(Path(catalog_dir))
            external_lineage = mapper.map_external_sources(
                include_stages=include_stages,
                include_external_tables=include_external_tables,
            )

            result = {
                "success": True,
                "external_sources": [s.to_dict() for s in external_lineage.sources],
                "external_tables": {
                    k: v.to_dict() for k, v in external_lineage.external_tables.items()
                },
                "stages": {k: v.to_dict() for k, v in external_lineage.stages.items()},
                "summary": external_lineage.summary,
            }
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            raise Exception(f"External source mapping failed: {e}")

    def _track_lineage_history(
        self,
        action: str,
        catalog_dir: str = "./data_catalogue",
        tag: Optional[str] = None,
        description: Optional[str] = None,
        from_tag: Optional[str] = None,
        to_tag: Optional[str] = None,
    ) -> str:
        """Track lineage history with snapshots."""
        try:
            from pathlib import Path
            from datetime import datetime

            history_manager = LineageHistoryManager(Path("./lineage_history"))

            if action == "snapshot":
                if not tag:
                    tag = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                snapshot = history_manager.capture_snapshot(
                    Path(catalog_dir), tag=tag, description=description
                )
                result = {
                    "success": True,
                    "action": "snapshot",
                    "snapshot": {
                        "tag": snapshot.tag,
                        "timestamp": snapshot.timestamp.isoformat(),
                        "description": snapshot.description,
                        "metadata": snapshot.metadata,
                    },
                }

            elif action == "compare":
                if not from_tag or not to_tag:
                    raise ValueError("Both from_tag and to_tag required for comparison")
                diff = history_manager.compare_lineage(from_tag, to_tag)
                if diff:
                    result = {
                        "success": True,
                        "action": "compare",
                        "diff": {
                            "from_tag": diff.from_tag,
                            "to_tag": diff.to_tag,
                            "added_nodes": diff.added_nodes,
                            "removed_nodes": diff.removed_nodes,
                            "added_edges": diff.added_edges,
                            "removed_edges": diff.removed_edges,
                            "summary": diff.summary,
                        },
                    }
                else:
                    result = {
                        "success": False,
                        "message": f"Could not compare {from_tag} to {to_tag}",
                    }

            elif action == "list":
                snapshots = history_manager.list_snapshots()
                result = {
                    "success": True,
                    "action": "list",
                    "snapshots": [
                        {
                            "tag": s.tag,
                            "timestamp": s.timestamp.isoformat(),
                            "description": s.description,
                        }
                        for s in snapshots
                    ],
                }

            elif action == "rollback":
                if not tag:
                    raise ValueError("Tag required for rollback")
                rollback_path = Path(f"./lineage_rollback_{tag}.json")
                history_manager.rollback_to_snapshot(tag, rollback_path)
                result = {
                    "success": True,
                    "action": "rollback",
                    "tag": tag,
                    "output_path": str(rollback_path),
                }

            else:
                raise ValueError(f"Unknown action: {action}")

            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            raise Exception(f"Lineage history tracking failed: {e}")


async def main():
    """Main entry point for MCP server."""
    server = SnowflakeMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
