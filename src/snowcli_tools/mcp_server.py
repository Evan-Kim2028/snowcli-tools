"""FastMCP-powered MCP server that layers snowcli-tools features on top of
Snowflake's official MCP service implementation.

This module boots a FastMCP server, reusing the upstream Snowflake MCP runtime
(`snowflake-labs-mcp`) for authentication, connection management, middleware,
transport wiring, and its suite of Cortex/object/query tools. On top of that
foundation we register the snowcli-tools catalog, lineage, and dependency
workflows so agents can access both sets of capabilities via a single MCP
endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import anyio
from pydantic import Field
from typing_extensions import Annotated

try:  # Prefer the standalone fastmcp package when available
    from fastmcp import Context, FastMCP
    from fastmcp.utilities.logging import configure_logging, get_logger
except ImportError:  # Fall back to the implementation bundled with python-sdk
    from mcp.server.fastmcp import Context, FastMCP
    from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger

from mcp_server_snowflake.server import (
    SnowflakeService,
)
from mcp_server_snowflake.server import (
    create_lifespan as create_snowflake_lifespan,  # type: ignore[import-untyped]
)
from mcp_server_snowflake.utils import (  # type: ignore[import-untyped]
    get_login_params,
    warn_deprecated_params,
)

from .catalog import build_catalog
from .config import Config, get_config, set_config
from .dependency import build_dependency_graph, to_dot
from .lineage import LineageQueryService
from .lineage.identifiers import parse_table_name
from .session_utils import (
    apply_session_context,
    ensure_session_lock,
    restore_session_context,
    snapshot_session,
)
from .snow_cli import SnowCLI, SnowCLIError

logger = get_logger(__name__)


def _json_compatible(payload: Any) -> Any:
    """Convert non-JSON-serialisable objects to strings recursively."""

    return json.loads(json.dumps(payload, default=str))


def _execute_query_sync(
    snowflake_service: SnowflakeService,
    statement: str,
    overrides: Dict[str, str],
) -> Dict[str, Any]:
    lock = ensure_session_lock(snowflake_service)
    with lock:
        with snowflake_service.get_connection(
            use_dict_cursor=True,
            session_parameters=snowflake_service.get_query_tag_param(),
        ) as (_, cursor):
            original = snapshot_session(cursor)
            try:
                if overrides:
                    apply_session_context(cursor, overrides)
                cursor.execute(statement)
                rows = cursor.fetchall()
                return {
                    "statement": statement,
                    "rowcount": cursor.rowcount,
                    "rows": _json_compatible(rows),
                }
            finally:
                try:
                    restore_session_context(cursor, original)
                except (
                    Exception
                ) as restore_error:  # pragma: no cover - catastrophic restore failure
                    logger.error(
                        "Failed to restore Snowflake session context: %s", restore_error
                    )
                    raise


def _test_connection_sync(snowflake_service: SnowflakeService) -> bool:
    try:
        with snowflake_service.get_connection(use_dict_cursor=True) as (_, cursor):
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if isinstance(row, dict):
                return any(str(value).strip() == "1" for value in row.values())
            if isinstance(row, (list, tuple)):
                return any(str(value).strip() == "1" for value in row)
            return bool(row)
    except Exception as exc:  # pragma: no cover - connector errors surface upstream
        logger.warning("Snowflake connection test failed: %s", exc)
        return False


def _query_lineage_sync(
    object_name: str,
    direction: str,
    depth: int,
    fmt: str,
    catalog_dir: str,
    cache_dir: str,
    config: Config,
) -> Dict[str, Any]:
    service = LineageQueryService(
        catalog_dir=Path(catalog_dir),
        cache_root=Path(cache_dir),
    )

    default_db = config.snowflake.database
    default_schema = config.snowflake.schema

    qualified = parse_table_name(object_name).with_defaults(default_db, default_schema)
    base_key = qualified.key()
    candidates = [base_key]
    if not base_key.endswith("::task"):
        candidates.append(f"{base_key}::task")

    lineage_result = None
    resolved_key: Optional[str] = None
    for candidate in candidates:
        try:
            result = service.object_subgraph(
                candidate, direction=direction, depth=depth
            )
        except KeyError:
            continue
        lineage_result = result
        resolved_key = candidate
        break

    if lineage_result is None or resolved_key is None:
        return {
            "success": False,
            "message": (
                "Object not found in lineage graph. Run build_catalog first or verify the name."
            ),
        }

    nodes = len(lineage_result.graph.nodes)
    edges = len(lineage_result.graph.edge_metadata)

    payload: Dict[str, Any] = {
        "success": True,
        "object": resolved_key,
        "direction": direction,
        "depth": depth,
        "node_count": nodes,
        "edge_count": edges,
    }

    if fmt == "json":
        graph = getattr(lineage_result.graph, "to_dict", None)
        payload["graph"] = (
            graph() if callable(graph) else _json_compatible(lineage_result.graph)
        )
    else:
        summary = [
            f"- {node.attributes.get('name', key)} ({node.node_type.value})"
            for key, node in lineage_result.graph.nodes.items()
        ]
        payload["summary"] = "\n".join(summary)
    return payload


def _get_catalog_summary_sync(catalog_dir: str) -> Dict[str, Any]:
    path = Path(catalog_dir) / "catalog_summary.json"
    if not path.exists():
        return {
            "success": False,
            "message": f"No catalog summary found in {catalog_dir}. Run build_catalog first.",
        }
    try:
        return {
            "success": True,
            "catalog_dir": catalog_dir,
            "summary": json.loads(path.read_text()),
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "message": f"Failed to parse catalog summary at {path}",
        }


def register_snowcli_tools(
    server: FastMCP,
    snowflake_service: SnowflakeService,
    *,
    enable_cli_bridge: bool = False,
) -> None:
    """Register snowcli-tools MCP endpoints on top of the official service."""

    if getattr(server, "_snowcli_tools_registered", False):  # pragma: no cover - safety
        return

    config = get_config()
    snow_cli: SnowCLI | None = SnowCLI() if enable_cli_bridge else None

    @server.tool(
        name="execute_query", description="Execute a SQL query against Snowflake"
    )
    async def execute_query_tool(
        statement: Annotated[str, Field(description="SQL statement to execute")],
        warehouse: Annotated[
            Optional[str], Field(description="Warehouse override", default=None)
        ] = None,
        database: Annotated[
            Optional[str], Field(description="Database override", default=None)
        ] = None,
        schema: Annotated[
            Optional[str], Field(description="Schema override", default=None)
        ] = None,
        role: Annotated[
            Optional[str], Field(description="Role override", default=None)
        ] = None,
        ctx: Context | None = None,
    ) -> Dict[str, Any]:
        overrides = {
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }
        packed = {k: v for k, v in overrides.items() if v}
        result = await anyio.to_thread.run_sync(
            _execute_query_sync,
            snowflake_service,
            statement,
            packed,
        )
        if ctx is not None:
            await ctx.debug(
                f"Executed query with {len(result['rows'])} rows (rowcount={result['rowcount']})."
            )
        return result

    @server.tool(name="preview_table", description="Preview table contents")
    async def preview_table_tool(
        table_name: Annotated[str, Field(description="Fully qualified table name")],
        limit: Annotated[int, Field(description="Row limit", ge=1, default=100)] = 100,
        warehouse: Annotated[
            Optional[str], Field(description="Warehouse override", default=None)
        ] = None,
        database: Annotated[
            Optional[str], Field(description="Database override", default=None)
        ] = None,
        schema: Annotated[
            Optional[str], Field(description="Schema override", default=None)
        ] = None,
        role: Annotated[
            Optional[str], Field(description="Role override", default=None)
        ] = None,
    ) -> Dict[str, Any]:
        statement = f"SELECT * FROM {table_name} LIMIT {limit}"
        overrides = {
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }
        packed = {k: v for k, v in overrides.items() if v}
        return await anyio.to_thread.run_sync(
            _execute_query_sync,
            snowflake_service,
            statement,
            packed,
        )

    @server.tool(name="build_catalog", description="Build Snowflake catalog metadata")
    async def build_catalog_tool(
        output_dir: Annotated[
            str,
            Field(description="Catalog output directory", default="./data_catalogue"),
        ] = "./data_catalogue",
        database: Annotated[
            Optional[str],
            Field(description="Specific database to introspect", default=None),
        ] = None,
        account: Annotated[
            bool, Field(description="Include entire account", default=False)
        ] = False,
        format: Annotated[
            str, Field(description="Output format (json/jsonl)", default="json")
        ] = "json",
        include_ddl: Annotated[
            bool, Field(description="Include object DDL", default=True)
        ] = True,
    ) -> Dict[str, Any]:
        def run_catalog() -> Dict[str, Any]:
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
            return {
                "success": True,
                "output_dir": output_dir,
                "totals": totals,
            }

        try:
            return await anyio.to_thread.run_sync(run_catalog)
        except Exception as exc:
            raise RuntimeError(f"Catalog build failed: {exc}") from exc

    @server.tool(name="query_lineage", description="Query cached lineage graph")
    async def query_lineage_tool(
        object_name: Annotated[str, Field(description="Object name to analyze")],
        direction: Annotated[
            str,
            Field(
                description="Traversal direction (upstream/downstream/both)",
                default="both",
            ),
        ] = "both",
        depth: Annotated[
            int, Field(description="Traversal depth", ge=1, le=10, default=3)
        ] = 3,
        format: Annotated[
            str, Field(description="Output format (text/json)", default="text")
        ] = "text",
        catalog_dir: Annotated[
            str,
            Field(description="Catalog directory", default="./data_catalogue"),
        ] = "./data_catalogue",
        cache_dir: Annotated[
            str,
            Field(description="Lineage cache directory", default="./lineage"),
        ] = "./lineage",
    ) -> Dict[str, Any]:
        return await anyio.to_thread.run_sync(
            _query_lineage_sync,
            object_name,
            direction,
            depth,
            format,
            catalog_dir,
            cache_dir,
            config,
        )

    @server.tool(
        name="build_dependency_graph", description="Build object dependency graph"
    )
    async def build_dependency_graph_tool(
        database: Annotated[
            Optional[str], Field(description="Specific database", default=None)
        ] = None,
        schema: Annotated[
            Optional[str], Field(description="Specific schema", default=None)
        ] = None,
        account: Annotated[
            bool, Field(description="Include account-level metadata", default=False)
        ] = False,
        format: Annotated[
            str, Field(description="Output format (json/dot)", default="json")
        ] = "json",
    ) -> Dict[str, Any]:
        def run_graph() -> Dict[str, Any]:
            graph = build_dependency_graph(
                database=database,
                schema=schema,
                account_scope=account,
            )
            if format == "dot":
                return {"format": "dot", "graph": to_dot(graph)}
            return {"format": "json", "graph": graph}

        return await anyio.to_thread.run_sync(run_graph)

    @server.tool(name="test_connection", description="Validate Snowflake connectivity")
    async def test_connection_tool() -> Dict[str, Any]:
        ok = await anyio.to_thread.run_sync(_test_connection_sync, snowflake_service)
        return {"success": ok}

    @server.tool(name="health_check", description="Get comprehensive health status")
    async def health_check_tool() -> Dict[str, Any]:
        """Get health status including connection state and system info."""
        from .services import RobustSnowflakeService

        try:
            # Test basic connection
            connection_ok = await anyio.to_thread.run_sync(
                _test_connection_sync, snowflake_service
            )

            # Get more detailed health from service layer
            robust_service = RobustSnowflakeService(config.snowflake.profile)
            health_status = await anyio.to_thread.run_sync(
                robust_service.get_health_status
            )

            return {
                "status": (
                    "healthy"
                    if connection_ok and health_status.healthy
                    else "unhealthy"
                ),
                "snowflake_connection": connection_ok,
                "detailed_health": {
                    "healthy": health_status.healthy,
                    "snowflake_connection": health_status.snowflake_connection,
                    "last_error": health_status.last_error,
                    "circuit_breaker_state": health_status.circuit_breaker_state,
                },
                "version": getattr(
                    __import__("snowcli_tools"), "__version__", "unknown"
                ),
                "timestamp": anyio.current_time(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": anyio.current_time(),
            }

    @server.tool(name="get_catalog_summary", description="Read catalog summary JSON")
    async def get_catalog_summary_tool(
        catalog_dir: Annotated[
            str,
            Field(description="Catalog directory", default="./data_catalogue"),
        ] = "./data_catalogue",
    ) -> Dict[str, Any]:
        return await anyio.to_thread.run_sync(_get_catalog_summary_sync, catalog_dir)

    if enable_cli_bridge and snow_cli is not None:

        @server.tool(
            name="run_cli_query",
            description="Execute a query via the Snowflake CLI bridge",
        )
        async def run_cli_query_tool(
            statement: Annotated[
                str, Field(description="SQL query to execute using snow CLI")
            ],
            warehouse: Annotated[
                Optional[str], Field(description="Warehouse override", default=None)
            ] = None,
            database: Annotated[
                Optional[str], Field(description="Database override", default=None)
            ] = None,
            schema: Annotated[
                Optional[str], Field(description="Schema override", default=None)
            ] = None,
            role: Annotated[
                Optional[str], Field(description="Role override", default=None)
            ] = None,
        ) -> Dict[str, Any]:
            overrides = {
                "warehouse": warehouse,
                "database": database,
                "schema": schema,
                "role": role,
            }
            packed = {k: v for k, v in overrides.items() if v}
            try:
                result = await anyio.to_thread.run_sync(
                    snow_cli.run_query,
                    statement,
                    output_format="json",
                    ctx_overrides=packed,
                )
            except SnowCLIError as exc:
                raise RuntimeError(f"Snow CLI query failed: {exc}") from exc

            rows = result.rows or []
            return {
                "statement": statement,
                "rows": rows,
                "stdout": result.raw_stdout,
                "stderr": result.raw_stderr,
            }

    setattr(server, "_snowcli_tools_registered", True)


def _apply_config_overrides(args: argparse.Namespace) -> None:
    if args.snowcli_config:
        cfg = Config.from_yaml(args.snowcli_config)
    else:
        cfg = get_config()

    if args.profile:
        cfg.snowflake.profile = args.profile

    # Propagate CLI context overrides from args if present
    for attr in ("warehouse", "database", "schema", "role"):
        value = getattr(args, attr, None)
        if value:
            setattr(cfg.snowflake, attr, value)

    set_config(cfg)

    if cfg.snowflake.profile:
        os.environ.setdefault("SNOWFLAKE_PROFILE", cfg.snowflake.profile)
        # Also set it immediately for the snowflake-labs-mcp package
        os.environ["SNOWFLAKE_PROFILE"] = cfg.snowflake.profile


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Snowflake MCP server with snowcli-tools extensions",
    )

    login_params = get_login_params()
    for value in login_params.values():
        if len(value) < 2:
            # Malformed entry; ignore to avoid argparse blow-ups
            continue

        help_text = value[-1]
        if len(value) >= 3:
            flags = value[:-2]
            default_value = value[-2]
        else:
            flags = value[:-1]
            default_value = None

        # Guard against implementations that only provide flags + help text
        if default_value == help_text:
            default_value = None

        parser.add_argument(
            *flags,
            required=False,
            default=default_value,
            help=help_text,
        )

    parser.add_argument(
        "--service-config-file",
        required=False,
        help="Path to Snowflake MCP service configuration YAML",
    )
    parser.add_argument(
        "--transport",
        required=False,
        choices=["stdio", "http", "sse", "streamable-http"],
        default=os.environ.get("SNOWCLI_MCP_TRANSPORT", "stdio"),
        help="Transport to use for FastMCP (default: stdio)",
    )
    parser.add_argument(
        "--endpoint",
        required=False,
        default=os.environ.get("SNOWCLI_MCP_ENDPOINT", "/mcp"),
        help="Endpoint path when running HTTP-based transports",
    )
    parser.add_argument(
        "--mount-path",
        required=False,
        default=None,
        help="Optional mount path override for SSE transport",
    )
    parser.add_argument(
        "--snowcli-config",
        required=False,
        help="Optional path to snowcli-tools YAML config (defaults to env)",
    )
    parser.add_argument(
        "--profile",
        required=False,
        help="Override Snowflake CLI profile for snowcli-tools operations",
    )
    parser.add_argument(
        "--enable-cli-bridge",
        action="store_true",
        help="Expose the legacy Snowflake CLI bridge tool (disabled by default)",
    )
    parser.add_argument(
        "--log-level",
        required=False,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("SNOWCLI_MCP_LOG_LEVEL", "INFO"),
        help="Log level for FastMCP runtime",
    )
    parser.add_argument(
        "--name",
        required=False,
        default="snowcli-tools MCP Server",
        help="Display name for the FastMCP server",
    )
    parser.add_argument(
        "--instructions",
        required=False,
        default="Snowcli-tools MCP server combining Snowflake official tools with catalog/lineage helpers.",
        help="Instructions string surfaced to MCP clients",
    )

    args = parser.parse_args()

    # Mirror CLI behaviour for env overrides
    if not getattr(args, "service_config_file", None):
        args.service_config_file = os.environ.get("SERVICE_CONFIG_FILE")

    return args


def create_combined_lifespan(args: argparse.Namespace):
    snowflake_lifespan = create_snowflake_lifespan(args)

    @asynccontextmanager
    async def lifespan(server: FastMCP):
        async with snowflake_lifespan(server) as snowflake_service:
            register_snowcli_tools(
                server,
                snowflake_service,
                enable_cli_bridge=args.enable_cli_bridge,
            )
            yield snowflake_service

    return lifespan


def main() -> None:
    args = parse_arguments()

    warn_deprecated_params()
    configure_logging(level=args.log_level)
    _apply_config_overrides(args)

    # Ensure SNOWFLAKE_PROFILE is set in environment for snowflake-labs-mcp
    cfg = get_config()
    configured_profile = cfg.snowflake.profile or os.environ.get("SNOWFLAKE_PROFILE")
    default_profile = configured_profile or os.environ.get("SNOWCLI_DEFAULT_PROFILE")

    if default_profile:
        os.environ["SNOWFLAKE_PROFILE"] = default_profile
        os.environ["SNOWFLAKE_DEFAULT_CONNECTION_NAME"] = default_profile
    else:
        logger.warning(
            "No Snowflake profile configured. Set SNOWFLAKE_PROFILE, "
            "SNOWCLI_DEFAULT_PROFILE, or pass --profile when starting the MCP server."
        )

    server = FastMCP(
        args.name,
        instructions=args.instructions,
        lifespan=create_combined_lifespan(args),
    )

    try:
        logger.info("Starting FastMCP server using transport=%s", args.transport)
        if args.transport in {"http", "sse", "streamable-http"}:
            endpoint = os.environ.get("SNOWFLAKE_MCP_ENDPOINT", args.endpoint)
            server.run(
                transport=args.transport,
                host="0.0.0.0",
                port=9000,
                path=endpoint,
            )
        else:
            server.run(transport=args.transport)
    except Exception as exc:  # pragma: no cover - run loop issues bubble up
        logger.error("MCP server terminated with error: %s", exc)
        raise


if __name__ == "__main__":
    main()
