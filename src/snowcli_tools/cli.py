"""CLI entrypoint wiring command registry and legacy aliases."""

from __future__ import annotations

import sys
import types
from typing import Dict, Optional, cast

import click
from rich.console import Console

from .commands import analyze as _analyze  # noqa: F401
from .commands import discover as _discover  # noqa: F401
from .commands import query as _query  # noqa: F401
from .commands import register_cli_groups
from .commands import setup as _setup  # noqa: F401
from .commands.analyze import LINEAGE_SERVICE_CLASS as _LINEAGE_SERVICE_CLASS
from .commands.analyze import (
    _traverse_lineage,
)
from .commands.analyze import analyze as analyze_group  # noqa: F401
from .commands.analyze import (
    dependencies_command,
    find_matches_by_partial_name,
    lineage_group,
)
from .commands.discover import catalog_command, export_sql_command
from .commands.query import (  # noqa: F401
    parallel_command,
    preview_command,
    query_group,
    run_command,
)
from .commands.setup import (
    config_command,
    init_config_command,
    mcp_command,
    profile_create_command,
    test_command,
    verify_command,
)
from .config import ConfigError, load_config
from .lineage.queries import LineageQueryService

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
@click.version_option(version="1.6.0")
def cli(config_path: Optional[str], profile: Optional[str], verbose: bool) -> None:
    """Snowflake CLI Tools consolidated entrypoint."""

    overrides: Dict[str, Optional[str]] = {}
    if profile:
        overrides["profile"] = profile

    try:
        config = load_config(
            config_path=config_path,
            cli_overrides=overrides or None,
        )
    except ConfigError as err:
        console.print(f"[red]✗[/red] Failed to load config: {err}")
        raise SystemExit(1) from err

    if verbose and config_path:
        console.print(f"[green]✓[/green] Loaded configuration from {config_path}")

    if verbose and profile:
        console.print(f"[green]✓[/green] Using profile: {config.snowflake.profile}")

    if verbose:
        console.print("[blue]ℹ[/blue] Using SNOWCLI-TOOLS v1.6.0")


register_cli_groups(cli)

# Legacy aliases for backward compatibility
cli.add_command(catalog_command, name="catalog")
cli.add_command(export_sql_command, name="export-sql")
cli.add_command(dependencies_command, name="depgraph")
cli.add_command(lineage_group, name="lineage")
cli.add_command(parallel_command, name="parallel")
cli.add_command(preview_command, name="preview")
cli.add_command(verify_command, name="verify")
cli.add_command(test_command, name="test")
cli.add_command(config_command, name="config")
cli.add_command(init_config_command, name="init_config")
cli.add_command(mcp_command, name="mcp")
cli.add_command(profile_create_command, name="setup_connection")


class _CLIModule(types.ModuleType):
    def __setattr__(self, name: str, value: object) -> None:
        if name == "LineageQueryService" and isinstance(value, type):
            _analyze.LINEAGE_SERVICE_CLASS = cast(type[LineageQueryService], value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _CLIModule  # type: ignore[misc]
setattr(sys.modules[__name__], "LineageQueryService", _LINEAGE_SERVICE_CLASS)  # type: ignore[assignment]


__all__ = [
    "cli",
    "main",
    "LineageQueryService",
    "_traverse_lineage",
    "find_matches_by_partial_name",
    "sys",
]


def main() -> None:
    """Entry point for CLI execution."""

    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Operation cancelled by user")
        raise SystemExit(1) from None
    except Exception as exc:  # pragma: no cover - top-level safety
        console.print(f"[red]✗[/red] Unexpected error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
