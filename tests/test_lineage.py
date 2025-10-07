from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from nanuk_mcp.cli import _traverse_lineage, find_matches_by_partial_name
from nanuk_mcp.lineage.audit import LineageAudit
from nanuk_mcp.lineage.builder import LineageBuilder
from nanuk_mcp.lineage.graph import EdgeType, LineageGraph, LineageNode, NodeType
from nanuk_mcp.lineage.loader import ObjectType
from nanuk_mcp.lineage.queries import LineageQueryResult, LineageQueryService
from nanuk_mcp.lineage.sql_parser import extract_select_clause


@pytest.fixture()
def sample_catalog(tmp_path: Path) -> Path:
    catalog_dir = tmp_path / "catalog"
    catalog_dir.mkdir()

    def write_jsonl(name: str, rows: list[dict]) -> None:
        path = catalog_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row))
                f.write("\n")

    write_jsonl(
        "tables",
        [
            {
                "TABLE_CATALOG": "PIPELINE",
                "TABLE_SCHEMA": "RAW",
                "TABLE_NAME": "SOURCE_TABLE",
            },
            {
                "TABLE_CATALOG": "PIPELINE",
                "TABLE_SCHEMA": "RAW",
                "TABLE_NAME": "TARGET_TABLE",
            },
        ],
    )

    write_jsonl(
        "views",
        [
            {
                "TABLE_CATALOG": "PIPELINE",
                "TABLE_SCHEMA": "RAW",
                "TABLE_NAME": "VW_SAMPLE",
                "ddl": "create or replace view PIPELINE.RAW.VW_SAMPLE as select * from PIPELINE.RAW.SOURCE_TABLE",
            }
        ],
    )

    write_jsonl(
        "tasks",
        [
            {
                "database_name": "PIPELINE",
                "schema_name": "RAW",
                "name": "LOAD_TASK",
                "definition": "INSERT INTO PIPELINE.RAW.TARGET_TABLE SELECT * FROM PIPELINE.RAW.VW_SAMPLE",
            }
        ],
    )

    return catalog_dir


def test_extract_select_clause_returns_select_body() -> None:
    ddl = """
    create or replace dynamic table PIPELINE.RAW.DT_EXAMPLE
    lag = '1 hour'
    warehouse = ANALYTICS_WH
    as
    select * from PIPELINE.RAW.SOURCE_TABLE
    """
    select_sql = extract_select_clause(ddl)
    assert select_sql is not None
    assert select_sql.lower().startswith("select * from pipeline.raw.source_table")


def test_lineage_builder_creates_edges(sample_catalog: Path) -> None:
    builder = LineageBuilder(sample_catalog)
    result = builder.build()

    graph = result.graph
    audit = result.audit

    view_key = "PIPELINE.RAW.VW_SAMPLE"
    source_key = "PIPELINE.RAW.SOURCE_TABLE"
    target_key = "PIPELINE.RAW.TARGET_TABLE"
    task_key = "PIPELINE.RAW.LOAD_TASK::task"

    assert view_key in graph.nodes
    assert source_key in graph.nodes
    assert target_key in graph.nodes
    assert task_key in graph.nodes

    edges = {
        (src, dst, edge.value) for (src, dst, edge), _ in graph.edge_metadata.items()
    }
    assert (view_key, source_key, EdgeType.DERIVES_FROM.value) in edges
    assert (task_key, view_key, EdgeType.CONSUMES.value) in edges
    assert (task_key, target_key, EdgeType.PRODUCES.value) in edges

    totals = audit.totals()
    assert totals["objects"] == len(audit.entries)
    view_entry = next(e for e in audit.entries if e.key == view_key)
    assert view_entry.status == "parsed"
    assert view_entry.upstreams == 1

    task_entry = next(e for e in audit.entries if e.key == task_key)
    assert task_entry.status == "parsed"
    assert task_entry.upstreams == 1
    assert task_entry.produces == 1

    table_entries = [e for e in audit.entries if e.object_type == ObjectType.TABLE]
    assert all(e.status == "base" for e in table_entries)

    assert audit.unknown_references == {}


def test_lineage_service_caches_results(sample_catalog: Path) -> None:
    service = LineageQueryService(sample_catalog)
    service.build(force=True)

    cache_dir = sample_catalog.parent / "lineage" / sample_catalog.name
    assert cache_dir.exists()
    graph_path = cache_dir / "lineage_graph.json"
    audit_path = cache_dir / "lineage_audit.json"
    assert graph_path.exists()
    assert audit_path.exists()

    # Subsequent builds should reuse cached artifacts without raising.
    result = service.build()
    assert result.graph.nodes

    html_path = cache_dir / "graph.html"
    LineageQueryService.to_html(result.graph, html_path)
    assert html_path.exists()
    html_content = html_path.read_text()
    assert "toggle-derives_from" in html_content
    assert "edge_type" in html_content


def test_traverse_lineage_appends_task_suffix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    graph = LineageGraph()
    graph.add_node(
        LineageNode(
            key="PIPELINE.RAW.LOAD_TASK::task",
            node_type=NodeType.TASK,
            attributes={"name": "LOAD_TASK"},
        )
    )

    result = LineageQueryResult(graph=graph, audit=LineageAudit())

    class DummyService:
        def __init__(self, catalog_dir: str | Path, cache_dir: str | Path) -> None:
            self.catalog_dir = catalog_dir
            self.cache_dir = cache_dir

        def load_cached(self) -> LineageQueryResult:
            return result

        def object_subgraph(
            self,
            object_key: str,
            *,
            direction: str,
            depth: Optional[int],
        ) -> LineageQueryResult:
            calls.append(object_key)
            if object_key.endswith("::task"):
                return result
            raise KeyError(f"Object not found in lineage graph: {object_key}")

    monkeypatch.setattr("snowcli_tools.cli.LineageQueryService", DummyService)

    _traverse_lineage(
        "PIPELINE.RAW.LOAD_TASK",
        str(tmp_path / "catalog"),
        str(tmp_path / "cache"),
        "both",
        1,
        "text",
        None,
    )

    assert calls == ["PIPELINE.RAW.LOAD_TASK", "PIPELINE.RAW.LOAD_TASK::task"]


def test_traverse_lineage_respects_html_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = LineageGraph()
    graph.add_node(
        LineageNode(
            key="PIPELINE.RAW.VW_SAMPLE",
            node_type=NodeType.DATASET,
            attributes={"name": "VW_SAMPLE"},
        )
    )
    result = LineageQueryResult(graph=graph, audit=LineageAudit())
    captured: dict[str, Path] = {}

    def fake_to_html(
        graph_arg: LineageGraph,
        output_path: Path | str,
        *,
        title: str | None = None,
        root_key: str | None = None,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html></html>")
        captured["path"] = path
        return path

    class DummyService:
        def __init__(self, catalog_dir: str | Path, cache_dir: str | Path) -> None:
            self.catalog_dir = catalog_dir
            self.cache_dir = cache_dir

        def load_cached(self) -> LineageQueryResult:
            return result

        def object_subgraph(
            self,
            object_key: str,
            *,
            direction: str,
            depth: Optional[int],
        ) -> LineageQueryResult:
            return result

        to_html = staticmethod(fake_to_html)

    monkeypatch.setattr("snowcli_tools.cli.LineageQueryService", DummyService)

    output_path = tmp_path / "custom" / "graph.html"

    _traverse_lineage(
        "PIPELINE.RAW.VW_SAMPLE",
        str(tmp_path / "catalog"),
        str(tmp_path / "cache"),
        "both",
        1,
        "html",
        str(output_path),
    )

    assert captured["path"] == output_path


def test_find_matches_by_partial_name_includes_schema_tokens() -> None:
    graph = LineageGraph()
    graph.add_node(
        LineageNode(
            key="PIPELINE.RAW.VW_SAMPLE",
            node_type=NodeType.DATASET,
            attributes={
                "database": "PIPELINE",
                "schema": "RAW",
                "name": "VW_SAMPLE",
            },
        )
    )
    graph.add_node(
        LineageNode(
            key="PIPELINE.ANALYTICS.VW_OTHER",
            node_type=NodeType.DATASET,
            attributes={
                "database": "PIPELINE",
                "schema": "ANALYTICS",
                "name": "VW_OTHER",
            },
        )
    )

    matches = find_matches_by_partial_name("RAW.VW", graph)
    assert matches == ["PIPELINE.RAW.VW_SAMPLE"]


def test_traverse_lineage_partial_match_unique(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []

    cached_graph = LineageGraph()
    cached_graph.add_node(
        LineageNode(
            key="PIPELINE.RAW.VW_SAMPLE",
            node_type=NodeType.DATASET,
            attributes={
                "database": "PIPELINE",
                "schema": "RAW",
                "name": "VW_SAMPLE",
            },
        )
    )

    query_graph = LineageGraph()
    query_graph.add_node(
        LineageNode(
            key="PIPELINE.RAW.VW_SAMPLE",
            node_type=NodeType.DATASET,
        )
    )

    cached_result = LineageQueryResult(graph=cached_graph, audit=LineageAudit())
    query_result = LineageQueryResult(graph=query_graph, audit=LineageAudit())

    class DummyService:
        def __init__(self, catalog_dir: str | Path, cache_dir: str | Path) -> None:
            self.catalog_dir = catalog_dir
            self.cache_dir = cache_dir

        def load_cached(self) -> LineageQueryResult:
            return cached_result

        def object_subgraph(
            self,
            object_key: str,
            *,
            direction: str,
            depth: Optional[int],
        ) -> LineageQueryResult:
            calls.append(object_key)
            if object_key == "PIPELINE.RAW.VW_SAMPLE":
                return query_result
            raise KeyError(object_key)

    monkeypatch.setattr("snowcli_tools.cli.LineageQueryService", DummyService)

    _traverse_lineage(
        "VW_SAMPLE",
        str(tmp_path / "catalog"),
        str(tmp_path / "cache"),
        "upstream",
        2,
        "text",
        None,
    )

    assert calls[0:2] == ["VW_SAMPLE", "VW_SAMPLE::task"]
    assert calls[-1] == "PIPELINE.RAW.VW_SAMPLE"


def test_traverse_lineage_partial_match_multiple_requires_disambiguation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cached_graph = LineageGraph()
    for schema in ("RAW", "ANALYTICS"):
        cached_graph.add_node(
            LineageNode(
                key=f"PIPELINE.{schema}.VW_SAMPLE",
                node_type=NodeType.DATASET,
                attributes={
                    "database": "PIPELINE",
                    "schema": schema,
                    "name": "VW_SAMPLE",
                },
            )
        )

    cached_result = LineageQueryResult(graph=cached_graph, audit=LineageAudit())

    class DummyService:
        def __init__(self, catalog_dir: str | Path, cache_dir: str | Path) -> None:
            self.catalog_dir = catalog_dir
            self.cache_dir = cache_dir

        def load_cached(self) -> LineageQueryResult:
            return cached_result

        def object_subgraph(
            self,
            object_key: str,
            *,
            direction: str,
            depth: Optional[int],
        ) -> LineageQueryResult:
            raise KeyError(object_key)

    monkeypatch.setattr("snowcli_tools.cli.LineageQueryService", DummyService)
    monkeypatch.setattr("snowcli_tools.cli.sys.stdin.isatty", lambda: False)

    with pytest.raises(SystemExit):
        _traverse_lineage(
            "VW_SAMPLE",
            str(tmp_path / "catalog"),
            str(tmp_path / "cache"),
            "upstream",
            1,
            "text",
            None,
        )
