"""Query execution commands."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from ..context import create_service_context
from ..errors import UnifiedErrorFormatter
from ..logging import StructuredLogger
from ..parallel import create_object_queries, query_multiple_objects
from ..service_layer.query import QueryService
from ..session_utils import SessionContext
from ..snow_cli import SnowCLIError
from .registry import CommandDescriptor, registry
from .utils import DefaultCommandGroup

console = Console()
formatter = UnifiedErrorFormatter()
logger = StructuredLogger(__name__)


@click.group(name="query", cls=DefaultCommandGroup, default_command="run")
def query_group() -> None:
    """Query execution and data preview commands."""


registry.register(
    CommandDescriptor(
        name="query",
        group="query",
        cli_handler=query_group,
        description="Execute queries and preview data",
    )
)

registry.register_group(query_group)


def _build_session(
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
) -> SessionContext:
    return SessionContext(
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role,
    )


@query_group.command(name="run")
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
def run_command(
    query: str,
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
    output_file: Optional[str],
    format: str,
) -> None:
    """Execute a single SQL query via Snowflake CLI."""

    context = create_service_context()
    service = QueryService(context=context)
    session_ctx = _build_session(warehouse, database, schema, role)
    start = perf_counter()
    try:
        out_fmt = (
            "json"
            if format == "json"
            else ("csv" if format == "csv" or output_file else None)
        )
        out = service.execute_cli(
            query,
            session=session_ctx,
            output_format=out_fmt,
        )

        if output_file:
            if format == "csv":
                with open(output_file, "w", encoding="utf-8") as file:
                    file.write(out.raw_stdout)
                console.print(f"[green]✓[/green] Results saved to {output_file}")
            else:
                console.print("[red]✗[/red] Output file only supports CSV format")
                raise SystemExit(1)
            return

        if format == "json" and out.rows is not None:
            console.print(json.dumps(out.rows, indent=2, default=str))
        elif format == "csv" and out.raw_stdout:
            console.print(out.raw_stdout)
        else:
            console.print(out.raw_stdout)
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.run",
            duration,
            True,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

    except SnowCLIError as exc:
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.run",
            duration,
            False,
            warehouse=warehouse,
            database=database,
            schema=schema,
            error=str(exc),
        )
        console.print(formatter.format_for_cli(exc))
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="run",
        group="query",
        cli_handler=run_command,
        description="Execute ad-hoc SQL queries",
    )
)


@query_group.command(name="preview")
@click.argument("table_name")
@click.option("--limit", "-l", type=int, default=100, help="Limit number of rows")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option("--role", help="Snowflake role")
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file for results",
)
def preview_command(
    table_name: str,
    limit: int,
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
    output_file: Optional[str],
) -> None:
    """Preview table contents via Snowflake CLI."""

    context = create_service_context()
    service = QueryService(context=context)
    session_ctx = _build_session(warehouse, database, schema, role)
    start = perf_counter()
    try:
        out = service.preview_cli(
            table_name,
            limit=limit,
            session=session_ctx,
        )

        if not out.raw_stdout.strip():
            console.print(
                f"[yellow]⚠[/yellow] Table {table_name} returned no results",
            )
            return

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

        table = Table(title=f"Preview ({min(len(rows), 50)} rows)")
        for col in columns:
            table.add_column(str(col), justify="left", style="cyan", no_wrap=False)
        for row in rows[:50]:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        console.print(table)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(out.raw_stdout)
            console.print(f"[green]✓[/green] Full results saved to {output_file}")
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.preview",
            duration,
            True,
            table=table_name,
            limit=limit,
        )

    except SnowCLIError as exc:
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.preview",
            duration,
            False,
            table=table_name,
            limit=limit,
            error=str(exc),
        )
        console.print(formatter.format_for_cli(exc))
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="preview",
        group="query",
        cli_handler=preview_command,
        description="Preview table contents",
    )
)


@query_group.command(name="parallel")
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
def parallel_command(
    objects: Tuple[str, ...],
    query_template: str,
    max_concurrent: Optional[int],
    output_dir: Optional[str],
    format: str,
) -> None:
    """Execute parallel queries for multiple objects."""

    if not objects:
        console.print("[red]✗[/red] No objects specified")
        console.print("Usage: sct query parallel <object1> <object2> ...")
        raise SystemExit(1)

    start = perf_counter()
    try:
        object_list = list(objects)
        queries = create_object_queries(object_list, query_template)

        console.print(f"[blue]🚀[/blue] Executing {len(queries)} parallel queries...")

        results = query_multiple_objects(
            queries,
            max_concurrent=max_concurrent,
        )

        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
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
                        with open(
                            output_path, "w", newline="", encoding="utf-8"
                        ) as file:
                            writer = _csv.DictWriter(file, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(result.rows)
                    elif format == "json":
                        output_path = Path(output_dir) / f"{safe_name}.json"
                        with open(output_path, "w", encoding="utf-8") as file:
                            json.dump(result.rows, file, indent=2, default=str)
                    saved_count += 1

            console.print(
                f"[green]✓[/green] Saved {saved_count} result files to {output_dir}"
            )
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.parallel",
            duration,
            True,
            objects=len(objects),
            output_dir=output_dir,
        )

    except Exception as exc:  # pragma: no cover - passthrough for runtime errors
        duration = perf_counter() - start
        logger.log_tool_execution(
            "query.parallel",
            duration,
            False,
            objects=len(objects),
            output_dir=output_dir,
            error=str(exc),
        )
        console.print(formatter.format_for_cli(exc))
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="parallel",
        group="query",
        cli_handler=parallel_command,
        description="Run templated queries concurrently",
    )
)
