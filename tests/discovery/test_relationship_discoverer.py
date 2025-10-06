"""Tests for RelationshipDiscoverer SQL sanitization."""

from unittest.mock import Mock

import pytest

from snowcli_tools.discovery.relationship_discoverer import RelationshipDiscoverer
from snowcli_tools.snow_cli import QueryOutput


@pytest.fixture
def mock_snow_cli():
    """Provide a mocked SnowCLI with JSON output convenience."""
    mock = Mock()
    mock.run_query.return_value = QueryOutput(
        raw_stdout="",
        raw_stderr="",
        returncode=0,
        rows=[{"CNT": 1}],
    )
    return mock


def test_table_exists_escapes_literals(mock_snow_cli):
    """Ensure schema/table literals escape single quotes."""
    discoverer = RelationshipDiscoverer(
        snow_cli=mock_snow_cli,
        database="MY_DB",
        schema="PUB'LIC",
    )

    discoverer._table_exists("O'RLY")

    sql = mock_snow_cli.run_query.call_args[0][0]
    assert "PUB''LIC" in sql
    assert "O''RLY" in sql


def test_calculate_overlap_escapes_strings_and_identifiers(mock_snow_cli):
    """Verify overlap calculation escapes values and quotes identifiers."""
    mock_snow_cli.run_query.return_value = QueryOutput(
        raw_stdout="",
        raw_stderr="",
        returncode=0,
        rows=[{"MATCH_COUNT": 1}],
    )

    discoverer = RelationshipDiscoverer(
        snow_cli=mock_snow_cli,
        database='DB"NAME',
        schema='SC"HEMA',
    )

    overlap = discoverer._calculate_overlap('ORD"ERS', 'COL"NAME', ["O'Brien"])
    assert overlap == pytest.approx(100.0)

    sql = mock_snow_cli.run_query.call_args[0][0]
    assert '"DB""NAME"."SC""HEMA"."ORD""ERS"' in sql
    assert '"COL""NAME"' in sql
    assert "O''Brien" in sql


def test_table_exists_uses_session_database_when_missing(mock_snow_cli):
    """When no database is provided, INFORMATION_SCHEMA should be unqualified."""
    discoverer = RelationshipDiscoverer(
        snow_cli=mock_snow_cli,
        database="",
        schema="PUBLIC",
    )

    discoverer._table_exists("ACCOUNTS")

    sql = mock_snow_cli.run_query.call_args[0][0]
    assert "INFORMATION_SCHEMA.TABLES" in sql
    assert '"".INFORMATION_SCHEMA' not in sql


def test_get_tables_in_schema_without_database(mock_snow_cli):
    """Ensure schema listing works with session database context."""
    mock_snow_cli.run_query.return_value = QueryOutput(
        raw_stdout="",
        raw_stderr="",
        returncode=0,
        rows=[{"TABLE_NAME": "FOO"}],
    )

    discoverer = RelationshipDiscoverer(
        snow_cli=mock_snow_cli,
        database="",
        schema="PUBLIC",
    )

    tables = discoverer._get_tables_in_schema()

    assert tables == ["FOO"]
    sql = mock_snow_cli.run_query.call_args[0][0]
    assert "INFORMATION_SCHEMA.TABLES" in sql
    assert '"".INFORMATION_SCHEMA' not in sql
