from __future__ import annotations

from typing import Any, Dict

from click.testing import CliRunner

from snowcli_tools.cli import cli as cli_entry
from snowcli_tools.snow_cli import SnowCLI, SnowCLIError


def _conn(name: str) -> Dict[str, Any]:
    return {"name": name, "connection_name": name}


def test_verify_missing_profile(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(SnowCLI, "list_connections", lambda self: [])

    result = runner.invoke(cli_entry, ["--profile", "readonly-keypair", "verify"])
    assert result.exit_code == 1
    assert "Profile 'readonly-keypair' not found" in result.output


def test_verify_cli_unavailable(monkeypatch):
    runner = CliRunner()

    def raise_unavailable(self):
        raise SnowCLIError("`snow` CLI not found")

    monkeypatch.setattr(SnowCLI, "list_connections", raise_unavailable)

    result = runner.invoke(cli_entry, ["--profile", "readonly-keypair", "verify"])
    assert result.exit_code == 1
    assert "Snow CLI not ready" in result.output


def test_verify_connection_failed(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        SnowCLI, "list_connections", lambda self: [_conn("readonly-keypair")]
    )
    monkeypatch.setattr(SnowCLI, "test_connection", lambda self: False)

    result = runner.invoke(cli_entry, ["--profile", "readonly-keypair", "verify"])
    assert result.exit_code == 1
    assert "Connection test failed" in result.output
