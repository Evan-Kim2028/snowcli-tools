"""Command-line interface for snowflake-cli-tools-py (Snowflake CLI-backed)."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .catalog import build_catalog, export_sql_from_catalog
from .config import Config, get_config, set_config
from .dependency import build_dependency_graph, to_dot
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
@click.version_option(version="1.2.0")
def cli(config_path: Optional[str], profile: Optional[str], verbose: bool):
    """Snowflake CLI Tools - Efficient database operations CLI.

    Primary features:
    - Data Catalog generation (JSON/JSONL)
    - Dependency Graph generation (DOT/JSON)

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
        console.print("[blue]ℹ[/blue] Using SNOWCLI-TOOLS v1.2.0")


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
        "Output path. Defaults to './dependencies' directory. "
        "If a directory is provided, a default filename is used."
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
