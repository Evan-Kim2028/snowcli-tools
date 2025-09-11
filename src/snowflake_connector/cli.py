"""Command-line interface for Snowflake Connector."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .config import Config, get_config, set_config
from .connection import execute_query_to_dataframe, test_connection
from .parallel import create_object_queries, query_multiple_objects

console = Console()


@click.group()
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.version_option(version="0.1.0")
def cli(config_path: Optional[str], verbose: bool):
    """Snowflake Connector - Efficient database operations CLI.

    A command-line tool for Snowflake database operations with parallel execution,
    connection pooling, and comprehensive error handling.
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

    if verbose:
        console.print("[blue]ℹ[/blue] Using Snowflake Connector v0.1.0")


@cli.command()
@click.option("--account", help="Snowflake account")
@click.option("--user", help="Snowflake user")
@click.option("--private-key-path", help="Path to private key file")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
def test(
    account: Optional[str],
    user: Optional[str],
    private_key_path: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
):
    """Test Snowflake connection."""
    try:
        success = test_connection(
            account=account,
            user=user,
            private_key_path=private_key_path,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

        if success:
            console.print("[green]✓[/green] Connection successful!")
        else:
            console.print("[red]✗[/red] Connection failed!")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Connection error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--account", help="Snowflake account")
@click.option("--user", help="Snowflake user")
@click.option("--private-key-path", help="Path to private key file")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
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
    account: Optional[str],
    user: Optional[str],
    private_key_path: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    output_file: Optional[str],
    format: str,
):
    """Execute a single SQL query."""
    try:
        df = execute_query_to_dataframe(
            query=query,
            account=account,
            user=user,
            private_key_path=private_key_path,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

        if df.empty:
            console.print("[yellow]⚠[/yellow] No results returned")
            return

        if output_file:
            if format == "csv":
                df.to_csv(output_file, index=False)
                console.print(f"[green]✓[/green] Results saved to {output_file}")
            else:
                console.print("[red]✗[/red] Output file only supports CSV format")
                sys.exit(1)
        elif format == "table":
            # Display as table
            table = Table(title=f"Query Results ({len(df)} rows)")
            for col in df.columns:
                table.add_column(str(col), justify="left", style="cyan", no_wrap=False)

            for _, row in df.iterrows():
                table.add_row(*[str(val) for val in row])

            console.print(table)
        elif format == "json":
            # Display as JSON
            result_dict = df.to_dict("records")
            console.print(json.dumps(result_dict, indent=2, default=str))
        elif format == "csv":
            # Display as CSV
            console.print(df.to_csv(index=False))

    except Exception as e:
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
@click.option("--private-key-path", help="Path to private key file")
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
    type=click.Choice(["parquet", "csv", "json"]),
    default="parquet",
    help="Output format for individual results",
)
def parallel(
    objects: tuple,
    query_template: str,
    max_concurrent: Optional[int],
    private_key_path: Optional[str],
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
            private_key_path=private_key_path,
        )

        # Save results if output directory specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            saved_count = 0

            for obj_name, result in results.items():
                if result.success and result.data is not None:
                    safe_name = obj_name.replace("::", "_").replace("0x", "")
                    if format == "parquet":
                        output_path = Path(output_dir) / f"{safe_name}.parquet"
                        result.data.write_parquet(output_path)
                    elif format == "csv":
                        output_path = Path(output_dir) / f"{safe_name}.csv"
                        result.data.write_csv(output_path)
                    elif format == "json":
                        output_path = Path(output_dir) / f"{safe_name}.json"
                        json_data = result.data.to_pandas().to_dict("records")
                        with open(output_path, "w") as f:
                            json.dump(json_data, f, indent=2, default=str)
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
@click.option("--account", help="Snowflake account")
@click.option("--user", help="Snowflake user")
@click.option("--private-key-path", help="Path to private key file")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option(
    "--output", "-o", "output_file", type=click.Path(), help="Output file for results"
)
def preview(
    table_name: str,
    limit: int,
    account: Optional[str],
    user: Optional[str],
    private_key_path: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    output_file: Optional[str],
):
    """Preview table contents."""
    query_str = f"SELECT * FROM {table_name} LIMIT {limit}"

    try:
        df = execute_query_to_dataframe(
            query=query_str,
            account=account,
            user=user,
            private_key_path=private_key_path,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

        if df.empty:
            console.print(
                f"[yellow]⚠[/yellow] Table {table_name} is empty or doesn't exist"
            )
            return

        # Display table info
        console.print(f"[blue]📊[/blue] Table: {table_name}")
        console.print(f"[blue]📏[/blue] Rows: {len(df)}, Columns: {len(df.columns)}")
        console.print(f"[blue]📝[/blue] Columns: {', '.join(df.columns)}")

        # Display sample data
        table = Table(title=f"Preview ({len(df)} rows)")
        for col in df.columns:
            table.add_column(str(col), justify="left", style="cyan", no_wrap=False)

        for _, row in df.iterrows():
            table.add_row(*[str(val) for val in row])

        console.print(table)

        if output_file:
            df.to_csv(output_file, index=False)
            console.print(f"[green]✓[/green] Full results saved to {output_file}")

    except Exception as e:
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

        table.add_row("Account", config.snowflake.account)
        table.add_row("User", config.snowflake.user)
        table.add_row("Private Key Path", config.snowflake.private_key_path)
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
