"""Contract tests ensuring CLI and service layer integrations stay stable."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable

from click.testing import CliRunner

from nanuk_mcp.cli import cli as cli_entry
from nanuk_mcp.context import create_service_context
from nanuk_mcp.models import (
    CatalogBuildResult,
    CatalogBuildTotals,
    CatalogMetadata,
    DependencyCounts,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyScope,
)
from nanuk_mcp.service_layer import CatalogService, DependencyService, QueryService
from nanuk_mcp.session_utils import SessionContext


def test_catalog_command_uses_service_snapshot(monkeypatch, tmp_path):
    sample_totals = {
        "databases": 2,
        "schemas": 4,
        "tables": 6,
        "views": 3,
        "materialized_views": 1,
        "dynamic_tables": 0,
        "tasks": 2,
        "functions": 5,
        "procedures": 1,
        "columns": 12,
    }

    def fake_build(self, output_dir: str, **kwargs: Any) -> CatalogBuildResult:
        assert output_dir == str(tmp_path)
        totals = CatalogBuildTotals(**sample_totals)
        metadata = CatalogMetadata(
            output_dir=Path(output_dir),
            output_format=kwargs.get("output_format", "json"),
            account_scope=kwargs.get("account_scope", False),
            incremental=kwargs.get("incremental", False),
            include_ddl=kwargs.get("include_ddl", True),
            export_sql=kwargs.get("export_sql", False),
            max_ddl_concurrency=kwargs.get("max_ddl_concurrency", 8),
            catalog_concurrency=kwargs.get("catalog_concurrency"),
        )
        return CatalogBuildResult(totals=totals, metadata=metadata)

    monkeypatch.setattr(CatalogService, "build", fake_build)

    runner = CliRunner()
    result = runner.invoke(
        cli_entry,
        [
            "catalog",
            "--output-dir",
            str(tmp_path),
            "--format",
            "json",
            "--no-include-ddl",
        ],
    )

    assert result.exit_code == 0
    assert "Catalog build complete" in result.output
    assert "Databases: 2" in result.output
    assert "Columns: 12" in result.output


def test_depgraph_command_writes_json_snapshot(monkeypatch, tmp_path):
    sample_graph = {
        "nodes": [
            {"id": "DB.SCHEMA.VIEW", "type": "VIEW"},
            {"id": "DB.SCHEMA.TABLE", "type": "TABLE"},
        ],
        "edges": [
            {
                "source": "DB.SCHEMA.VIEW",
                "target": "DB.SCHEMA.TABLE",
                "relationship": "uses",
            }
        ],
        "counts": {"nodes": 2, "edges": 1},
        "scope": {"database": "DB", "schema": "SCHEMA", "account_scope": False},
    }

    def fake_build(self, **kwargs: Any) -> DependencyGraph:
        assert kwargs["database"] == "DB"
        assert kwargs["schema"] == "SCHEMA"
        assert kwargs["account_scope"] is False
        return DependencyGraph(
            nodes=[DependencyNode(**node) for node in sample_graph["nodes"]],
            edges=[DependencyEdge(**edge) for edge in sample_graph["edges"]],
            counts=DependencyCounts(**sample_graph["counts"]),
            scope=DependencyScope(**sample_graph["scope"]),
        )

    monkeypatch.setattr(DependencyService, "build", fake_build)
    monkeypatch.setattr(
        DependencyService,
        "to_dot",
        lambda self, graph: 'digraph {\n  "DB.SCHEMA.VIEW" -> "DB.SCHEMA.TABLE";\n}',
    )

    runner = CliRunner()
    result = runner.invoke(
        cli_entry,
        [
            "depgraph",
            "--output",
            str(tmp_path),
            "--database",
            "DB",
            "--schema",
            "SCHEMA",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    graph_path = Path(tmp_path) / "dependencies.json"
    assert graph_path.exists()
    stored = json.loads(graph_path.read_text())
    assert stored == sample_graph


class _StubCursor:
    def __init__(self, rows: Iterable[Dict[str, Any]]) -> None:
        self._rows = list(rows)
        self._fetchone_called = False
        self.executed: list[str] = []
        self.rowcount = len(self._rows)

    def execute(self, query: str) -> None:
        self.executed.append(query)

    def fetchone(self) -> tuple[str, str, str, str]:
        if not self._fetchone_called:
            self._fetchone_called = True
            return ("ROLE", "WAREHOUSE", "DATABASE", "SCHEMA")
        return ("ROLE", "WAREHOUSE", "DATABASE", "SCHEMA")

    def fetchall(self) -> list[Dict[str, Any]]:
        return self._rows


class _StubSnowflakeService:
    def __init__(self) -> None:
        self.lock = None

    def get_query_tag_param(self) -> Dict[str, Any]:
        return {}

    @contextmanager
    def get_connection(self, **_: Any):
        yield (
            None,
            _StubCursor(
                [
                    {"COL1": "A", "COL2": 1},
                    {"COL1": "B", "COL2": 2},
                ]
            ),
        )


def test_query_service_execute_with_service_returns_expected_payload():
    service = QueryService(context=create_service_context())
    snowflake_service = _StubSnowflakeService()
    session = SessionContext(warehouse="WH", database="DB")

    result = service.execute_with_service(
        snowflake_service,
        "SELECT 1",
        session=session,
    )

    assert result["statement"] == "SELECT 1"
    assert result["rowcount"] == 2
    assert result["rows"] == [
        {"COL1": "A", "COL2": 1},
        {"COL1": "B", "COL2": 2},
    ]
