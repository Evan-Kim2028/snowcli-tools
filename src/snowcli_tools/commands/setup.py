"""Setup and configuration commands."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..config import Config, apply_config_overrides, get_config
from ..snow_cli import SnowCLI, SnowCLIError
from .registry import CommandDescriptor, registry
from .utils import DefaultCommandGroup

console = Console()


@click.group(name="setup", cls=DefaultCommandGroup, default_command="verify")
def setup_group() -> None:
    """Provision profiles, verify connectivity, and inspect configuration."""


registry.register_group(setup_group)
registry.register(
    CommandDescriptor(
        name="setup",
        group="setup",
        cli_handler=setup_group,
        description="Provision Snowflake CLI context",
    )
)


@setup_group.command(name="verify")
def verify_command() -> None:
    """Verify Snow CLI availability, profile existence, and connectivity."""

    cfg = get_config()
    try:
        runner = SnowCLI(profile=cfg.snowflake.profile)
        conns = runner.list_connections()
        names = {c.get("name") or c.get("connection_name") for c in conns}
        if cfg.snowflake.profile not in names:
            console.print(
                f"[red]✗[/red] Profile '{cfg.snowflake.profile}' not found in Snow CLI connections."
            )
            console.print(
                "[blue]ℹ[/blue] Create one with: `snow connection add --connection-name "
                f"{cfg.snowflake.profile} --account <acct> --user <user> --private-key <path>`"
            )
            console.print(
                "[blue]ℹ[/blue] Or run with: `--profile <existing_profile>` or set SNOWFLAKE_PROFILE."
            )
            raise SystemExit(1)

        if not runner.test_connection():
            console.print(
                f"[red]✗[/red] Connection test failed for profile '{cfg.snowflake.profile}'."
            )
            console.print(
                "[blue]ℹ[/blue] Verify credentials and defaults (role/warehouse/database/schema)."
            )
            raise SystemExit(1)

        console.print(
            f"[green]✓[/green] Verified Snow CLI and profile '{cfg.snowflake.profile}'."
        )
    except SnowCLIError as exc:
        console.print(
            "[red]✗[/red] Snow CLI not ready. Install `snowflake-cli` and configure a profile."
        )
        console.print(f"[dim]{exc}[/dim]")
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="verify",
        group="setup",
        cli_handler=verify_command,
        description="Verify Snow CLI profile connectivity",
    )
)


@setup_group.command(name="test")
@click.option("--warehouse", help="Snowflake warehouse")
@click.option("--database", help="Snowflake database")
@click.option("--schema", help="Snowflake schema")
@click.option("--role", help="Snowflake role")
def test_command(
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    role: Optional[str],
) -> None:
    """Test Snowflake connection via Snowflake CLI."""

    try:
        cli = SnowCLI()
        success = cli.test_connection()
        if success:
            console.print("[green]✓[/green] Connection successful!")
        else:
            console.print("[red]✗[/red] Connection failed!")
            raise SystemExit(1)
    except SnowCLIError as exc:
        console.print(f"[red]✗[/red] Snowflake CLI error: {exc}")
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="test",
        group="setup",
        cli_handler=test_command,
        description="Test Snow CLI connectivity",
    )
)


@setup_group.group(name="profile")
def profile_group() -> None:
    """Manage Snow CLI profiles used by the toolset."""


registry.register(
    CommandDescriptor(
        name="profile",
        group="setup",
        cli_handler=profile_group,
        description="Manage Snowflake CLI profiles",
    )
)


@profile_group.command(name="create")
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
def profile_create_command(
    name: Optional[str],
    account: Optional[str],
    user: Optional[str],
    private_key_file: Optional[str],
    role: Optional[str],
    warehouse: Optional[str],
    database: Optional[str],
    schema: Optional[str],
    default: bool,
) -> None:
    """Convenience helper to create a key-pair Snow CLI connection."""

    cli = SnowCLI()

    name = name or click.prompt("Connection name", default="my-dev", type=str)
    account = account or click.prompt("Account identifier", type=str)
    user = user or click.prompt("Username", type=str)
    private_key_file = private_key_file or click.prompt(
        "Path to RSA private key file",
        default=str(Path.home() / "Documents" / "snowflake_keys" / "rsa_key.p8"),
        type=str,
    )

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

        apply_config_overrides(snowflake={"profile": name})
        console.print(f"[green]✓[/green] Local profile set to '{name}'")

        if cli.test_connection():
            console.print("[green]✓[/green] Connection test succeeded")
        else:
            console.print(
                "[yellow]⚠[/yellow] Connection test did not return expected result"
            )

    except SnowCLIError as exc:
        console.print(f"[red]✗[/red] Failed to setup connection: {exc}")
        raise SystemExit(1)


@setup_group.command(name="config")
def config_command() -> None:
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

    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]✗[/red] Failed to load configuration: {exc}")
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="config",
        group="setup",
        cli_handler=config_command,
        description="Display active configuration",
    )
)


@setup_group.command(name="init-config")
@click.argument("config_path", type=click.Path())
def init_config_command(config_path: str) -> None:
    """Initialize a new configuration file from environment defaults."""

    try:
        config = Config.from_env()
        config.save_to_yaml(config_path)
        console.print(f"[green]✓[/green] Configuration saved to {config_path}")

        console.print("\n[blue]📝[/blue] Created configuration:")
        with open(config_path, "r", encoding="utf-8") as file:
            console.print(file.read())

    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]✗[/red] Failed to create configuration: {exc}")
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="init-config",
        group="setup",
        cli_handler=init_config_command,
        description="Bootstrap configuration file",
    )
)


@setup_group.command(name="mcp")
def mcp_command() -> None:
    """Start the MCP server for integration with AI assistants."""

    try:
        from ..mcp_server import main as mcp_main

        console.print("[blue]🚀[/blue] Starting Snowflake MCP Server...")
        console.print(
            "[blue]ℹ[/blue] This server provides AI assistants access to your Snowflake data"
        )
        console.print("[blue]💡[/blue] Press Ctrl+C to stop the server")
        console.print()

        config_path = Path("mcp_service_config.json")
        if not config_path.exists():
            minimal_config = {
                "snowflake": {
                    "account": "",
                    "user": "",
                    "database": "",
                    "schema": "",
                    "warehouse": "",
                }
            }
            with open(config_path, "w", encoding="utf-8") as file:
                json.dump(minimal_config, file, indent=2)

        mcp_main(["--service-config-file", str(config_path)])

    except ImportError:
        console.print(
            "[red]✗[/red] MCP server requires the 'mcp' extra: uv add snowcli-tools[mcp]"
        )
        console.print("[yellow]💡[/yellow] Install with: uv add snowcli-tools[mcp]")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] MCP server stopped by user")
    except Exception as exc:

        def sanitize_error_message(msg: str) -> str:
            patterns = [
                (r"password=[^;,\s]+", "password=***"),
                (r"token=[^;,\s]+", "token=***"),
                (r"authenticator=[^;,\s]+", "authenticator=***"),
                (r"private_key=[^;,\s]+", "private_key=***"),
                (r"://[^:@]+:[^@]+@", "://***:***@"),
                (r"Connection string.*", "Connection string: [SANITIZED]"),
            ]
            sanitized = str(msg)
            for pattern, replacement in patterns:
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            return sanitized

        console.print(
            f"[red]✗[/red] MCP server failed: {sanitize_error_message(str(exc))}"
        )

        if "--debug" in sys.argv or os.getenv("DEBUG", "").lower() in (
            "1",
            "true",
            "yes",
        ):
            console.print("[yellow]Debug traceback:[/yellow]")
            sanitized_traceback = sanitize_error_message(
                "".join(line for line in __import__("traceback").format_exc())
            )
            console.print(sanitized_traceback)
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="mcp",
        group="setup",
        cli_handler=mcp_command,
        description="Launch MCP server",
    )
)
