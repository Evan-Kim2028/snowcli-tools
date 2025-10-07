from __future__ import annotations

from click.testing import CliRunner

from snowcli_tools.cli import cli as cli_entry
from snowcli_tools.snow_cli import SnowCLI


def test_profile_short_flag_before_subcommand(monkeypatch):
    runner = CliRunner()

    # Ensure verify path executes without needing real Snow CLI
    monkeypatch.setattr(SnowCLI, "list_connections", lambda self: [])

    result = runner.invoke(cli_entry, ["-p", "readonly-keypair", "verify"])
    # Root option recognized; verify command executes and reports missing profile
    assert result.exit_code == 1
    assert "Profile 'readonly-keypair' not found" in result.output


def test_profile_flag_after_subcommand_errors(monkeypatch):
    runner = CliRunner()

    # Subcommands don't accept -p; Click should report unknown option
    result = runner.invoke(cli_entry, ["verify", "-p", "readonly-keypair"])
    assert result.exit_code == 2  # Click usage error
    assert "no such option: -p" in result.output.lower()


