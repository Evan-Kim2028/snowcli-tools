"""Discover command group implementations."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Optional

import anyio
import click

from ..catalog import export_sql_from_catalog
from ..context import create_service_context
from ..errors import UnifiedErrorFormatter
from ..logging import StructuredLogger
from ..models import CatalogBuildResult
from ..pipelines.catalog import CatalogOptions, CatalogPipeline
from ..service_layer.catalog import CatalogService
from ..snow_cli import SnowCLIError
from .registry import CommandDescriptor, registry
from .utils import DefaultCommandGroup

formatter = UnifiedErrorFormatter()
logger = StructuredLogger(__name__)


@click.group(name="discover", cls=DefaultCommandGroup, default_command="catalog")
def discover() -> None:
    """Data discovery and exploration commands."""


registry.register_group(discover)


@discover.command(name="catalog")
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
    "--account",
    "-a",
    is_flag=True,
    help="Introspect all databases in the account",
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
def catalog_command(
    output_dir: str,
    database: Optional[str],
    account: bool,
    incremental: bool,
    format: str,
    include_ddl: bool,
    max_ddl_concurrency: int,
    catalog_concurrency: Optional[int],
    export_sql: bool,
) -> None:
    """Build a Snowflake data catalog from INFORMATION_SCHEMA/SHOW."""

    from rich.console import Console

    console = Console()
    context = create_service_context()
    service = CatalogService(context=context)
    cache_dir = Path(output_dir) / ".cache"
    start = perf_counter()
    try:
        console.print(
            f"[blue]🔍[/blue] Building catalog to [cyan]{output_dir}[/cyan]..."
        )
        options = CatalogOptions(
            output_dir=Path(output_dir),
            database=database,
            account_scope=account,
            incremental=incremental,
            output_format=format,
            include_ddl=include_ddl,
            max_ddl_concurrency=max_ddl_concurrency,
            catalog_concurrency=catalog_concurrency,
            export_sql=export_sql,
        )
        pipeline = CatalogPipeline(service, cache_dir=cache_dir)
        result = anyio.run(pipeline.execute, options)
        duration = perf_counter() - start
        logger.log_tool_execution(
            "discover.catalog",
            duration,
            True,
            database=database,
            account_scope=account,
            output_dir=str(options.output_dir),
        )
        console.print("[green]✓[/green] Catalog build complete")
        totals = result.totals.model_dump()
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

        if export_sql:
            sql_dir = result.metadata.output_dir / "sql"
            has_sql = sql_dir.exists() and any(sql_dir.rglob("*.sql"))
            if not has_sql:
                console.print(
                    "[yellow]⚠[/yellow] No SQL files were exported. "
                    "Ensure the selected profile has DDL access or rerun with export-sql",
                )
    except SnowCLIError as exc:
        duration = perf_counter() - start
        logger.log_tool_execution(
            "discover.catalog",
            duration,
            False,
            error=str(exc),
            database=database,
            account_scope=account,
        )
        console.print(formatter.format_for_cli(exc))
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="catalog",
        group="discover",
        cli_handler=catalog_command,
        description="Generate comprehensive data catalog",
        schema=CatalogBuildResult,
    )
)


@discover.command(name="export-sql")
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
def export_sql_command(input_dir: str, output_dir: Optional[str], workers: int) -> None:
    """Export categorized SQL files from an existing JSON catalog."""

    from rich.console import Console

    console = Console()
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
    except SnowCLIError as exc:
        console.print(f"[red]✗[/red] SQL export failed: {exc}")
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="export-sql",
        group="discover",
        cli_handler=export_sql_command,
        description="Export SQL files from existing catalog",
    )
)
