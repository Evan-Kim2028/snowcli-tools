"""Command-line interface for snowflake-cli-tools-py (Snowflake CLI-backed)."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table

from .catalog import build_catalog, export_sql_from_catalog
from .config import Config, get_config, set_config
from .dependency import build_dependency_graph, to_dot
from .lineage import LineageQueryService
from .lineage.graph import LineageGraph, LineageNode
from .lineage.identifiers import QualifiedName, parse_table_name
from .lineage.queries import LineageQueryResult

# MCP import is guarded - only imported when the command is called
from .parallel import create_object_queries, query_multiple_objects
from .snow_cli import SnowCLI, SnowCLIError

console = Console()


@click.group()
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option("--profile", "-p", "profile", help="Snowflake CLI profile name")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.version_option(version="1.3.0")
def cli(config_path: Optional[str], profile: Optional[str], verbose: bool):
    """Snowflake CLI Tools - Efficient database operations CLI.

    Primary features:
    - Data Catalog generation (JSON/JSONL)
    - Dependency Graph generation (DOT/JSON)
    - Lineage Graph analysis (upstream/downstream traversal)

    Also includes a parallel query helper and convenience utilities.

    Authentication is provided entirely by the official `snow` CLI profiles
    (bring-your-own profile). This tool never manages secrets or opens a browser;
    it shells out to `snow sql` with your selected profile and optional context.
    """
    if config_path:
        try:
            config = Config.from_yaml(config_path)
            set_config(config)
            if verbose:
                console.print(
                    f"[green]✓[/green] Loaded configuration from {config_path}"
                )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load config: {e}")
            sys.exit(1)

    if profile:
        cfg = get_config()
        cfg.snowflake.profile = profile
        set_config(cfg)
        if verbose:
            console.print(f"[green]✓[/green] Using profile: {profile}")

    if verbose:
        console.print("[blue]ℹ[/blue] Using SNOWCLI-TOOLS v1.3.0")


@cli.command()
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option("--role", help="Snowflake role")
def test(
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
):
    """Test Snowflake connection via Snowflake CLI."""
    try:
        cli = SnowCLI()
        success = cli.test_connection()
        if success:
            console.print("[green]✓[/green] Connection successful!")
        else:
            console.print("[red]✗[/red] Connection failed!")
            sys.exit(1)
    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Snowflake CLI error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option("--role", help="Snowflake role")
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file for results (CSV format)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
def query(
    query: str,
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
    output_file: Optional[str],
    format: str,
):
    """Execute a single SQL query via Snowflake CLI."""
    ctx = {"warehouse": warehouse, "database": database, "schema": schema, "role": role}
    try:
        cli = SnowCLI()
        out_fmt = (
            "json"
            if format == "json"
            else ("csv" if format == "csv" or output_file else None)
        )
        out = cli.run_query(query, output_format=out_fmt, ctx_overrides=ctx)

        # Save to file
        if output_file:
            if format == "csv":
                with open(output_file, "w") as f:
                    f.write(out.raw_stdout)
                console.print(f"[green]✓[/green] Results saved to {output_file}")
            else:
                console.print("[red]✗[/red] Output file only supports CSV format")
                sys.exit(1)
            return

        # Print based on format
        if format == "json" and out.rows is not None:
            console.print(json.dumps(out.rows, indent=2, default=str))
        elif format == "csv" and out.raw_stdout:
            console.print(out.raw_stdout)
        else:
            # Fall back to raw stdout (pretty table from CLI)
            console.print(out.raw_stdout)

    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Query execution failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("objects", nargs=-1)
@click.option(
    "--query-template",
    "-t",
    default="SELECT * FROM object_parquet2 WHERE type = '{object}' LIMIT 100",
    help="Query template with {object} placeholder",
)
@click.option("--max-concurrent", "-m", type=int, help="Maximum concurrent queries")
@click.option(
    "--output-dir",
    "-o",
    "output_dir",
    type=click.Path(),
    help="Output directory for results",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "json", "parquet"]),
    default="csv",
    help="Output format for individual results",
)
def parallel(
    objects: tuple,
    query_template: str,
    max_concurrent: Optional[int],
    output_dir: Optional[str],
    format: str,
):
    """Execute parallel queries for multiple objects."""
    if not objects:
        console.print("[red]✗[/red] No objects specified")
        console.print("Usage: snowflake-cli parallel <object1> <object2> ...")
        sys.exit(1)

    try:
        # Create queries
        object_list = list(objects)
        queries = create_object_queries(object_list, query_template)

        console.print(f"[blue]🚀[/blue] Executing {len(queries)} parallel queries...")

        # Execute queries
        results = query_multiple_objects(
            queries,
            max_concurrent=max_concurrent,
        )

        # Save results if output directory specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            saved_count = 0

            for obj_name, result in results.items():
                if result.success and result.rows is not None:
                    safe_name = obj_name.replace("::", "_").replace("0x", "")
                    if format == "parquet":
                        console.print(
                            "[yellow]⚠[/yellow] Parquet export requires 'polars'. "
                            "Install polars or use --format csv/json. Skipping.",
                        )
                        continue
                    elif format == "csv":
                        output_path = Path(output_dir) / f"{safe_name}.csv"
                        import csv as _csv

                        fieldnames = list(result.rows[0].keys()) if result.rows else []
                        with open(output_path, "w", newline="") as f:
                            writer = _csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(result.rows)
                    elif format == "json":
                        output_path = Path(output_dir) / f"{safe_name}.json"
                        with open(output_path, "w") as f:
                            json.dump(result.rows, f, indent=2, default=str)
                    saved_count += 1

            console.print(
                f"[green]✓[/green] Saved {saved_count} result files to {output_dir}"
            )

    except Exception as e:
        console.print(f"[red]✗[/red] Parallel execution failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("table_name")
@click.option("--limit", "-l", type=int, default=100, help="Limit number of rows")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option("--role", help="Snowflake role")
@click.option(
    "--output", "-o", "output_file", type=click.Path(), help="Output file for results"
)
def preview(
    table_name: str,
    limit: int,
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
    output_file: Optional[str],
):
    """Preview table contents via Snowflake CLI."""
    query_str = f"SELECT * FROM {table_name} LIMIT {limit}"
    try:
        cli = SnowCLI()
        out = cli.run_query(
            query_str,
            output_format="csv",
            ctx_overrides={
                "warehouse": warehouse,
                "database": database,
                "schema": schema,
                "role": role,
            },
        )

        if not out.raw_stdout.strip():
            console.print(
                f"[yellow]⚠[/yellow] Table {table_name} returned no results",
            )
            return

        # Parse CSV for summary
        import csv as _csv
        from io import StringIO as _SIO

        reader = _csv.DictReader(_SIO(out.raw_stdout))
        rows = list(reader)

        if not rows:
            console.print(
                f"[yellow]⚠[/yellow] Table {table_name} returned no rows",
            )
            return

        columns = reader.fieldnames or []
        console.print(f"[blue]📊[/blue] Table: {table_name}")
        console.print(f"[blue]📏[/blue] Rows: {len(rows)}, Columns: {len(columns)}")
        console.print(f"[blue]📝[/blue] Columns: {', '.join(columns)}")

        # Display as table (first page only)
        table = Table(title=f"Preview ({min(len(rows), 50)} rows)")
        for col in columns:
            table.add_column(str(col), justify="left", style="cyan", no_wrap=False)
        for row in rows[:50]:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        console.print(table)

        if output_file:
            with open(output_file, "w") as f:
                f.write(out.raw_stdout)
            console.print(f"[green]✓[/green] Full results saved to {output_file}")

    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Preview failed: {e}")
        sys.exit(1)


@cli.command()
def config():
    """Show current configuration."""
    try:
        config = get_config()

        table = Table(title="Snowflake Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Profile", config.snowflake.profile)
        table.add_row("Warehouse", config.snowflake.warehouse)
        table.add_row("Database", config.snowflake.database)
        table.add_row("Schema", config.snowflake.schema)
        table.add_row("Role", config.snowflake.role or "None")
        table.add_row("Max Concurrent Queries", str(config.max_concurrent_queries))
        table.add_row("Connection Pool Size", str(config.connection_pool_size))
        table.add_row("Retry Attempts", str(config.retry_attempts))
        table.add_row("Retry Delay", f"{config.retry_delay}s")
        table.add_row("Timeout", f"{config.timeout_seconds}s")
        table.add_row("Log Level", config.log_level)

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help=(
        "Output path. Defaults to './dependencies' directory. If a directory is provided, a default filename is used."
    ),
)
@click.option("--format", "-f", type=click.Choice(["json", "dot"]), default="json")
@click.option("--database", help="Restrict to a database (optional)")
@click.option("--schema", help="Restrict to a schema (optional)")
@click.option(
    "--account", "-a", is_flag=True, help="Use ACCOUNT_USAGE scope (broader coverage)"
)
def depgraph(
    output: Optional[str],
    format: str,
    database: Optional[str],
    schema: Optional[str],
    account: bool,
):
    """Create a dependency graph of Snowflake objects.

    Uses ACCOUNT_USAGE.OBJECT_DEPENDENCIES when available, otherwise falls back
    to INFORMATION_SCHEMA (view→table usage).
    """
    try:
        graph = build_dependency_graph(
            database=database, schema=schema, account_scope=account
        )
        if format == "json":
            payload = json.dumps(graph, indent=2)
        else:
            payload = to_dot(graph)

        # Determine output target
        default_dir = Path("./dependencies")
        out_target = output
        if not out_target:
            # No output provided: default to directory
            out_dir = default_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (
                "dependencies.json" if format == "json" else "dependencies.dot"
            )
        else:
            p = Path(out_target)
            # If it's an existing directory or endswith path separator, treat as dir
            if p.exists() and p.is_dir():
                out_path = p / (
                    "dependencies.json" if format == "json" else "dependencies.dot"
                )
            else:
                # If user provided a path without a suffix, treat like a directory
                if p.suffix.lower() in (".json", ".dot"):
                    out_path = p
                else:
                    p.mkdir(parents=True, exist_ok=True)
                    out_path = p / (
                        "dependencies.json" if format == "json" else "dependencies.dot"
                    )

        with open(out_path, "w") as f:
            f.write(payload)
        console.print(f"[green]✓[/green] Dependency graph written to {out_path}")
    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Failed to build dependency graph: {e}")
        sys.exit(1)


@cli.command()
@click.option("--name", "-n", required=False, help="Connection name (e.g., my-dev)")
@click.option("--account", "-a", required=False, help="Account identifier")
@click.option("--user", "-u", required=False, help="Snowflake username")
@click.option(
    "--private-key-file",
    "-k",
    required=False,
    type=click.Path(),
    help="Path to RSA private key file",
)
@click.option("--role", required=False, help="Default role")
@click.option("--warehouse", required=False, help="Default warehouse")
@click.option("--database", required=False, help="Default database")
@click.option("--schema", required=False, help="Default schema")
@click.option("--default", is_flag=True, help="Set as default connection")
def setup_connection(
    name: Optional[str],
    account: Optional[str],
    user: Optional[str],
    private_key_file: Optional[str],
    role: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    default: bool,
):
    """Convenience helper to create a key‑pair `snow` CLI connection.

    Notes:
    - Optional. You can always use `snow connection add` directly.
    - Creates a profile that this tool (and `snow`) can use.
    - Prompts for any missing values.
    """
    cli = SnowCLI()

    # Prompt for missing values
    name = name or click.prompt("Connection name", default="my-dev", type=str)
    account = account or click.prompt("Account identifier", type=str)
    user = user or click.prompt("Username", type=str)
    private_key_file = private_key_file or click.prompt(
        "Path to RSA private key file",
        default=str(Path.home() / "Documents" / "snowflake_keys" / "rsa_key.p8"),
        type=str,
    )

    # Expand and normalize key path
    private_key_file = os.path.abspath(os.path.expanduser(private_key_file))

    try:
        if cli.connection_exists(name):
            console.print(f"[yellow]ℹ[/yellow] Connection '{name}' already exists")
        else:
            cli.add_connection(
                name,
                account=account,
                user=user,
                private_key_file=private_key_file,
                role=role,
                warehouse=warehouse,
                database=database,
                schema=schema,
                make_default=default,
            )
            console.print(f"[green]✓[/green] Connection '{name}' created")

        if default:
            cli.set_default_connection(name)
            console.print(f"[green]✓[/green] Set '{name}' as default connection")

        # Update local config profile to this name for convenience
        cfg = get_config()
        cfg.snowflake.profile = name
        set_config(cfg)
        console.print(f"[green]✓[/green] Local profile set to '{name}'")

        # Test and print a sample result header
        if cli.test_connection():
            console.print("[green]✓[/green] Connection test succeeded")
        else:
            console.print(
                "[yellow]⚠[/yellow] Connection test did not return expected result"
            )

    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Failed to setup connection: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="./data_catalogue",
    help="Output directory for catalog files",
)
@click.option(
    "--database",
    "-d",
    help="Specific database to introspect (default uses current database)",
)
@click.option(
    "--account", "-a", is_flag=True, help="Introspect all databases in the account"
)
@click.option(
    "--incremental",
    is_flag=True,
    default=False,
    help="Update catalog incrementally based on LAST_ALTERED timestamps.",
)
@click.option(
    "--format",
    type=click.Choice(["json", "jsonl"]),
    default="json",
    help="Output format for entity files",
)
@click.option(
    "--include-ddl/--no-include-ddl",
    default=True,
    help="Include DDL in catalog outputs",
)
@click.option(
    "--max-ddl-concurrency", type=int, default=8, help="Max concurrent DDL fetches"
)
@click.option(
    "--catalog-concurrency",
    type=int,
    default=None,
    help="Parallel workers for schema scanning (default 16)",
)
@click.option(
    "--export-sql",
    is_flag=True,
    default=False,
    help="Export a human-readable SQL repo from captured DDL",
)
def catalog(
    output_dir: str,
    database: Optional[str],
    account: bool,
    incremental: bool,
    format: str,
    include_ddl: bool,
    max_ddl_concurrency: int,
    catalog_concurrency: Optional[int],
    export_sql: bool,
):
    """Build a Snowflake data catalog (JSON files) from INFORMATION_SCHEMA/SHOW.

    Generates JSON files: schemata.json, tables.json, columns.json, views.json,
    materialized_views.json, routines.json, tasks.json, dynamic_tables.json,
    plus a catalog_summary.json with counts.
    """
    try:
        console.print(
            f"[blue]🔍[/blue] Building catalog to [cyan]{output_dir}[/cyan]..."
        )
        totals = build_catalog(
            output_dir,
            database=database,
            account_scope=account,
            incremental=incremental,
            output_format=format,
            include_ddl=include_ddl,
            max_ddl_concurrency=max_ddl_concurrency,
            catalog_concurrency=catalog_concurrency or 16,
            export_sql=export_sql,
        )
        console.print("[green]✓[/green] Catalog build complete")
        console.print(
            " | ".join(
                [
                    f"Databases: {totals.get('databases', 0)}",
                    f"Schemas: {totals.get('schemas', 0)}",
                    f"Tables: {totals.get('tables', 0)}",
                    f"Views: {totals.get('views', 0)}",
                    f"Materialized Views: {totals.get('materialized_views', 0)}",
                    f"Dynamic Tables: {totals.get('dynamic_tables', 0)}",
                    f"Tasks: {totals.get('tasks', 0)}",
                    f"Functions: {totals.get('functions', 0)}",
                    f"Procedures: {totals.get('procedures', 0)}",
                    f"Columns: {totals.get('columns', 0)}",
                ]
            )
        )

        # If SQL export requested but no files were written, surface a hint
        if export_sql:
            from pathlib import Path as _P

            sql_dir = _P(output_dir) / "sql"
            has_sql = sql_dir.exists() and any(sql_dir.rglob("*.sql"))
            if not has_sql:
                console.print(
                    "[yellow]⚠[/yellow] No SQL files were exported. "
                    "This usually means DDL could not be captured for the scanned objects. "
                    "Ensure the selected profile has sufficient privileges (e.g., USAGE/OWNERSHIP) "
                    "or run `snowflake-cli export-sql -i <catalog_dir>` to fetch DDL from JSON."
                )
    except SnowCLIError as e:
        console.print(f"[red]✗[/red] Catalog build failed: {e}")
        sys.exit(1)


@cli.command("export-sql")
@click.option(
    "--input-dir",
    "-i",
    type=click.Path(exists=True),
    default="./data_catalogue",
    help="Catalog directory containing JSON/JSONL files",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Output directory for SQL tree (default: <input-dir>/sql)",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=16,
    help="Max concurrent DDL fetch/write workers",
)
def export_sql_cmd(input_dir: str, output_dir: Optional[str], workers: int):
    """Export categorized SQL files from an existing JSON catalog.

    Layout: sql/<asset_type>/<DB>/<SCHEMA>/<OBJECT>.sql. If JSON rows are
    missing a `ddl` field, DDL is fetched on-demand.
    """
    try:
        console.print(
            f"[blue]🛠️[/blue] Exporting SQL from catalog: [cyan]{input_dir}[/cyan]"
        )
        counts = export_sql_from_catalog(input_dir, output_dir, max_workers=workers)
        out_dir = output_dir or (Path(input_dir) / "sql")
        console.print(
            f"[green]✓[/green] Exported {counts.get('written', 0)} SQL files to {out_dir}"
        )
        missing = counts.get("missing", 0)
        if missing:
            console.print(
                f"[yellow]ℹ[/yellow] {missing} objects lacked DDL or were inaccessible"
            )
    except SnowCLIError as e:
        console.print(f"[red]✗[/red] SQL export failed: {e}")
        sys.exit(1)


@cli.group()
def lineage() -> None:
    """Lineage graph utilities backed by the local catalog."""


@lineage.command()
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing JSON/JSONL exports",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
def rebuild(catalog_dir: str, cache_dir: str) -> None:
    """Parse catalog JSON and rebuild the cached lineage graph."""
    service = LineageQueryService(catalog_dir, cache_dir)
    console.print(
        f"[blue]🧭[/blue] Rebuilding lineage graph from [cyan]{catalog_dir}[/cyan]"
    )
    console.print(f"[blue]ℹ[/blue] Cache directory: [cyan]{service.cache_dir}[/cyan]")
    result = service.build(force=True)
    totals = result.audit.totals()
    console.print(
        " | ".join(
            [
                f"Objects: {totals.get('objects', 0)}",
                f"Parsed: {totals.get('parsed', 0)}",
                f"Missing SQL: {totals.get('missing_sql', 0)}",
                f"Parse errors: {totals.get('parse_error', 0)}",
                f"Unknown refs: {len(result.audit.unknown_references)}",
            ]
        )
    )


@lineage.command()
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=3,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def neighbors(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show upstream AND downstream lineage for a Snowflake object.

    This is the most common lineage query - see what depends on your object
    AND what your object depends on, within a limited depth.

    Examples:
        snowflake-cli lineage neighbors MY_TABLE
        snowflake-cli lineage neighbors MY_DB.MY_SCHEMA.MY_VIEW -d 5
        snowflake-cli lineage neighbors MY_VIEW --format dot -o my_view.dot
    """
    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "both", depth, format, output
    )


@lineage.command()
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=5,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def upstream(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show what a Snowflake object DEPENDS ON (upstream lineage).

    Follow the chain backwards to see source tables, views, and data sources
    that this object relies on.

    Examples:
        snowflake-cli lineage upstream MY_TABLE
        snowflake-cli lineage upstream MY_VIEW -d 10
        snowflake-cli lineage upstream MY_VIEW --format json -o sources.json
    """
    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "upstream", depth, format, output
    )


@lineage.command()
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=5,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def downstream(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show what DEPENDS ON a Snowflake object (downstream lineage).

    Follow the chain forward to see views, materialized views, and tasks
    that depend on this object.

    Examples:
        snowflake-cli lineage downstream MY_TABLE
        snowflake-cli lineage downstream MY_TABLE -d 3
        snowflake-cli lineage downstream MY_TABLE --format dot -o dependents.dot
    """
    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "downstream", depth, format, output
    )


def _traverse_lineage(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    direction: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Shared implementation for lineage traversal commands."""
    service = LineageQueryService(catalog_dir, cache_dir)
    cfg = get_config()
    default_db = cfg.snowflake.database
    default_schema = cfg.snowflake.schema
    qn = parse_table_name(object_name).with_defaults(default_db, default_schema)
    base_object_key = qn.key()
    candidate_keys = [base_object_key]
    if not base_object_key.endswith("::task"):
        candidate_keys.append(f"{base_object_key}::task")

    result: Optional[LineageQueryResult] = None
    resolved_key: Optional[str] = None

    for candidate in candidate_keys:
        try:
            result = service.object_subgraph(
                candidate, direction=direction, depth=depth
            )
            resolved_key = candidate
            break
        except KeyError:
            continue

    if result is None or resolved_key is None:
        try:
            cached = service.load_cached()
        except FileNotFoundError:
            console.print(
                "[red]✗[/red] Lineage graph not available. Run `snowflake-cli lineage rebuild` first."
            )
            sys.exit(1)

        matches = find_matches_by_partial_name(object_name, cached.graph)

        if not matches:
            console.print(
                f"[red]✗[/red] No matches found for '{object_name}' in lineage graph"
            )
            console.print(
                "[dim]💡[/dim] Try using the fully qualified name (database.schema.object)."
            )
            sys.exit(1)

        resolved_key, result = resolve_partial_match(
            matches,
            object_name,
            base_object_key,
            qn,
            cached.graph,
            service,
            direction,
            depth,
        )

        if result is None or resolved_key is None:
            sys.exit(1)

    if result is None or resolved_key is None:
        console.print(
            f"[red]✗[/red] Object not found in lineage graph: {base_object_key}"
        )
        sys.exit(1)

    object_key = resolved_key

    graph = result.graph
    direction_desc = {
        "upstream": "depends on",
        "downstream": "is used by",
        "both": "is connected to",
    }[direction]

    # Handle file output
    if output and format in ["json", "html"]:
        if format == "json":
            output_path = Path(output)
            output_path.write_text(
                json.dumps(LineageQueryService.to_json(graph), indent=2)
            )
            console.print(f"[green]✓[/green] Lineage JSON written to {output_path}")
        else:  # html
            html_path = Path(output)
            full_html_path = LineageQueryService.to_html(
                graph,
                html_path,
                title=f"{direction.title()} Lineage: {object_key}",
                root_key=object_key,
            )
            console.print(
                f"[green]✓[/green] Interactive HTML lineage written to {full_html_path}"
            )
        return

    # Auto-save JSON files to lineage/json/ directory (unless explicitly saved elsewhere)
    if format == "json" and not output:
        json_dir = Path("lineage/json")
        json_dir.mkdir(parents=True, exist_ok=True)

        # Create filename based on object and direction
        safe_name = object_key.replace(".", "_").replace("::", "_")
        json_filename = f"{direction}_{safe_name}.json"
        json_path = json_dir / json_filename

        json_path.write_text(json.dumps(LineageQueryService.to_json(graph), indent=2))
        console.print(f"[blue]💾[/blue] Lineage JSON auto-saved to {json_path}")

    # Console output
    if format == "json":
        console.print_json(data=LineageQueryService.to_json(graph))
        return

    # Text output
    console.print(
        f"[blue]🔗[/blue] {direction.title()} lineage for [cyan]{object_key}[/cyan]"
    )
    console.print(
        f"[blue]📏[/blue] Depth: {depth} | Nodes: {len(graph.nodes)} | Edges: {len(graph.edge_metadata)}"
    )

    if not graph.nodes:
        console.print(f"[yellow]⚠[/yellow] No {direction} lineage found")
        return

    # Group nodes by type for better readability
    by_type: Dict[str, List[LineageNode]] = {}
    for node in graph.nodes.values():
        node_type = node.node_type.value
        if node_type not in by_type:
            by_type[node_type] = []
        by_type[node_type].append(node)

    # Show summary by type
    for node_type, nodes in sorted(by_type.items()):
        plural = "s" if len(nodes) != 1 else ""
        in_catalog = sum(1 for n in nodes if n.attributes.get("in_catalog") == "true")
        console.print(
            f"[blue]📊[/blue] {len(nodes)} {node_type}{plural} ({in_catalog} in catalog)"
        )

    # Show detailed edges
    if graph.edge_metadata:
        console.print(f"\n[blue]🔗[/blue] Connections ({direction_desc}):")
        for (src, dst, edge_type), evidence in sorted(graph.edge_metadata.items()):
            src_name = graph.nodes[src].attributes.get("name", src.split(".")[-1])
            dst_name = graph.nodes[dst].attributes.get("name", dst.split(".")[-1])
            console.print(f"  - {src_name} → {dst_name} [{edge_type.value}]")


@lineage.command()
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format",
)
def audit(catalog_dir: str, cache_dir: str, format: str) -> None:
    """Display lineage parsing coverage and unknown references."""
    service = LineageQueryService(catalog_dir, cache_dir)
    try:
        lineage = service.load_cached()
    except FileNotFoundError:
        console.print(
            "[red]✗[/red] Lineage graph not found. Run `snowflake-cli lineage rebuild` first."
        )
        sys.exit(1)

    console.print(f"[blue]ℹ[/blue] Cache directory: [cyan]{service.cache_dir}[/cyan]")
    audit_report = lineage.audit
    if format == "json":
        console.print_json(data=audit_report.to_dict())
        return

    totals = audit_report.totals()
    console.print(
        " | ".join(
            [
                f"Objects: {totals.get('objects', 0)}",
                f"Parsed: {totals.get('parsed', 0)}",
                f"Missing SQL: {totals.get('missing_sql', 0)}",
                f"Parse errors: {totals.get('parse_error', 0)}",
                f"Unknown refs: {len(audit_report.unknown_references)}",
            ]
        )
    )
    if audit_report.unknown_references:
        console.print("\n[blue]Unresolved references:[/blue]")
        for ref, count in audit_report.unknown_references.items():
            console.print(f"  - {ref}: {count}")


@lineage.command()
def help() -> None:
    """Show lineage command help and examples."""
    console.print("\n[bold blue]🔗 Snowflake Lineage Commands[/bold blue]")
    console.print("\n[bold]Workflow:[/bold]")
    console.print("1. snowflake-cli lineage rebuild    # Build full lineage graph")
    console.print("2. snowflake-cli lineage neighbors  # Query specific objects")
    console.print("3. snowflake-cli lineage upstream   # What does this depend on?")
    console.print("4. snowflake-cli lineage downstream # What depends on this?")
    console.print("5. snowflake-cli lineage audit      # Check parsing coverage")

    console.print("\n[bold]Quick Examples:[/bold]")
    console.print("  snowflake-cli lineage neighbors MY_TABLE")
    console.print("  snowflake-cli lineage upstream MY_VIEW -d 3")
    console.print(
        "  snowflake-cli lineage downstream MY_TABLE --format html -o my_table_downstream.html"
    )
    console.print("  snowflake-cli lineage audit --format json")

    console.print("\n[bold]Tips:[/bold]")
    console.print("  • Use -d to limit depth (default: 3-5 levels)")
    console.print("  • Use --format html for interactive visualization")
    console.print("  • HTML files are saved to lineage/html/ directory")
    console.print("  • Use --output to specify custom filename")
    console.print("  • Start with 'neighbors' to see both directions")


@cli.command()
@click.argument("config_path", type=click.Path())
def init_config(config_path: str):
    """Initialize a new configuration file."""
    try:
        config = Config.from_env()
        config.save_to_yaml(config_path)
        console.print(f"[green]✓[/green] Configuration saved to {config_path}")

        # Show the created config
        console.print("\n[blue]📝[/blue] Created configuration:")
        with open(config_path, "r") as f:
            console.print(f.read())

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create configuration: {e}")
        sys.exit(1)


@cli.command()
def mcp():
    """Start the MCP server for integration with AI assistants.

    This command starts an MCP server that provides access to all snowcli-tools
    functionality for AI assistants like VS Code, Cursor, and Claude Code.

    Usage:
        snowflake-cli mcp

    The server will run on stdio and provide tools for:
    - Executing SQL queries
    - Building data catalogs
    - Querying lineage information
    - Generating dependency graphs
    - Previewing table data
    - Testing connections

    Use this with MCP-compatible clients to get AI assistance with your Snowflake data.
    """
    try:
        # Guarded import - only load MCP when the command is called
        import asyncio

        from .mcp_server import main as mcp_main

        console.print("[blue]🚀[/blue] Starting Snowflake MCP Server...")
        console.print(
            "[blue]ℹ[/blue] This server provides AI assistants access to your Snowflake data"
        )
        console.print("[blue]💡[/blue] Press Ctrl+C to stop the server")
        console.print()

        # Run the MCP server
        asyncio.run(mcp_main())

    except ImportError:
        console.print(
            "[red]✗[/red] MCP server requires the 'mcp' extra: uv add snowcli-tools[mcp]"
        )
        console.print("[yellow]💡[/yellow] Install with: uv add snowcli-tools[mcp]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] MCP server stopped by user")
    except Exception as e:
        import os
        import re
        import traceback

        def sanitize_error_message(msg: str) -> str:
            """Sanitize error messages to prevent credential disclosure."""
            # Remove potential passwords, tokens, and connection strings
            patterns = [
                (r"password=[^;,\s]+", "password=***"),
                (r"token=[^;,\s]+", "token=***"),
                (r"authenticator=[^;,\s]+", "authenticator=***"),
                (r"private_key=[^;,\s]+", "private_key=***"),
                (r"://[^:@]+:[^@]+@", "://***:***@"),  # URLs with credentials
                (r"Connection string.*", "Connection string: [SANITIZED]"),
            ]
            sanitized = str(msg)
            for pattern, replacement in patterns:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            return sanitized

        console.print(
            f"[red]✗[/red] MCP server failed: {sanitize_error_message(str(e))}"
        )

        # Show detailed traceback in debug mode or when DEBUG env var is set
        if "--debug" in sys.argv or os.getenv("DEBUG", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            console.print("[yellow]Debug traceback:[/yellow]")
            # Sanitize the full traceback as well
            sanitized_traceback = sanitize_error_message(traceback.format_exc())
            console.print(sanitized_traceback)

            # Additional debugging for TaskGroup exceptions (sanitized)
            if hasattr(e, "__cause__") and e.__cause__:
                sanitized_cause = sanitize_error_message(str(e.__cause__))
                console.print(f"[yellow]Root cause:[/yellow] {sanitized_cause}")
            if hasattr(e, "__context__") and e.__context__:
                sanitized_context = sanitize_error_message(str(e.__context__))
                console.print(
                    f"[yellow]Exception context:[/yellow] {sanitized_context}"
                )
        else:
            console.print(
                "[dim]💡 Run with --debug for detailed error information[/dim]"
            )

        sys.exit(1)


def resolve_partial_match(
    matches: List[str],
    raw_input: str,
    base_object_key: str,
    parsed_input: QualifiedName,
    graph: LineageGraph,
    service: LineageQueryService,
    direction: str,
    depth: int,
) -> tuple[Optional[str], Optional[LineageQueryResult]]:
    """Select the best match and execute the lineage query."""

    def _try(lineage_key: str) -> tuple[Optional[str], Optional[LineageQueryResult]]:
        try:
            result = service.object_subgraph(
                lineage_key, direction=direction, depth=depth
            )
            console.print(f"[green]✓[/green] Using lineage node: {lineage_key}")
            return lineage_key, result
        except KeyError:
            return None, None

    normalized_target = base_object_key.lower()
    exact_key_matches = [key for key in matches if key.lower() == normalized_target]
    if exact_key_matches:
        return _try(exact_key_matches[0])

    target_name = parsed_input.name.lower()

    def _object_name(lineage_key: str) -> str:
        return lineage_key.replace("::task", "").split(".")[-1].lower()

    name_matches = [key for key in matches if _object_name(key) == target_name]
    if len(name_matches) == 1:
        return _try(name_matches[0])

    if len(matches) == 1:
        return _try(matches[0])

    chosen = disambiguate_matches(matches, raw_input, graph)
    if chosen is None:
        return None, None
    return _try(chosen)


def find_matches_by_partial_name(partial_name: str, graph: LineageGraph) -> List[str]:
    """Find objects in the lineage graph that contain all tokens of the partial name."""
    tokens = [token for token in re.split(r"[\s.]+", partial_name.lower()) if token]
    if not tokens:
        return []

    matches: List[str] = []
    seen: set[str] = set()

    for node_key, node in graph.nodes.items():
        key_lower = node_key.lower()
        haystacks = {key_lower}

        attrs = node.attributes
        db = attrs.get("database", "").lower()
        schema = attrs.get("schema", "").lower()
        name = attrs.get("name", "").lower()

        if name:
            haystacks.add(name)
        if schema and name:
            haystacks.add(f"{schema}.{name}")
        if db and schema and name:
            haystacks.add(f"{db}.{schema}.{name}")

        for haystack in haystacks:
            if haystack and all(token in haystack for token in tokens):
                if node_key not in seen:
                    matches.append(node_key)
                    seen.add(node_key)
                break

    return matches


def disambiguate_matches(
    matches: List[str], raw_input: str, graph: LineageGraph
) -> Optional[str]:
    """Prompt the user to select a match when multiple options exist."""
    if not sys.stdin.isatty():
        console.print(
            f"[red]✗[/red] Ambiguous lineage lookup for '{raw_input}'. "
            "Provide a more specific name (e.g. database.schema.object)."
        )
        return None

    console.print(f"[yellow]⚠[/yellow] Found {len(matches)} matches for '{raw_input}':")
    for index, key in enumerate(matches, start=1):
        node = graph.nodes.get(key)
        obj_type = node.attributes.get("object_type") if node else None
        type_label = f" [{obj_type}]" if obj_type else ""
        console.print(f"  {index}. {key}{type_label}")

    choice = click.prompt(
        "Select the desired object",
        type=click.IntRange(1, len(matches)),
        default=1,
    )
    return matches[choice - 1]


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
