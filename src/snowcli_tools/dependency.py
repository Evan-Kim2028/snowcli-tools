"""Dependency graph extraction for Snowflake objects.

This module builds a lightweight dependency graph by querying the official
Snowflake metadata. It prefers ACCOUNT_USAGE.OBJECT_DEPENDENCIES when
available (broader coverage), and falls back to INFORMATION_SCHEMA views for
view→table usage when ACCOUNT_USAGE is not accessible.

Output format is a simple graph structure with `nodes` and `edges`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .snow_cli import SnowCLI, SnowCLIError


@dataclass
class DependencyEdge:
    source: str  # fully qualified name
    target: str  # fully qualified name
    source_type: Optional[str] = None
    target_type: Optional[str] = None
    relationship: Optional[str] = None


def _fq(db: Optional[str], schema: Optional[str], name: str) -> str:
    parts = [p for p in [db, schema, name] if p]
    return ".".join(parts)


def _query_account_usage(
    cli: SnowCLI, database: Optional[str], schema: Optional[str]
) -> List[DependencyEdge]:
    filters: List[str] = []
    if database:
        # ACCOUNT_USAGE uses REFERENCING_DATABASE (not REFERENCING_OBJECT_DATABASE)
        filters.append("lower(REFERENCING_DATABASE) = lower($db)")
    if schema:
        # ACCOUNT_USAGE uses REFERENCING_SCHEMA (not REFERENCING_OBJECT_SCHEMA)
        filters.append("lower(REFERENCING_SCHEMA) = lower($schema)")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f"""
    SELECT
      REFERENCING_DATABASE,
      REFERENCING_SCHEMA,
      REFERENCING_OBJECT_NAME,
      REFERENCING_OBJECT_DOMAIN,
      REFERENCED_DATABASE,
      REFERENCED_SCHEMA,
      REFERENCED_OBJECT_NAME,
      REFERENCED_OBJECT_DOMAIN,
      -- Both columns exist; prefer RELATIONSHIP but fall back to DEPENDENCY_TYPE
      RELATIONSHIP,
      DEPENDENCY_TYPE
    FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
    {where}
    """

    binds: Dict[str, str] = {}
    if database:
        binds["db"] = database
    if schema:
        binds["schema"] = schema

    # The snow CLI doesn't support bind variables directly; inline safely
    # with simple quoting for our limited use-case (identifiers).
    for k, v in binds.items():
        sql = sql.replace(f"${k}", f"'{v}'")

    out = cli.run_query(sql, output_format="csv")
    edges: List[DependencyEdge] = []
    if not out.rows:
        return edges
    for row in out.rows:
        src = _fq(
            row.get("REFERENCING_DATABASE"),
            row.get("REFERENCING_SCHEMA"),
            row.get("REFERENCING_OBJECT_NAME") or "",
        )
        tgt = _fq(
            row.get("REFERENCED_DATABASE"),
            row.get("REFERENCED_SCHEMA"),
            row.get("REFERENCED_OBJECT_NAME") or "",
        )
        rel = row.get("RELATIONSHIP") or row.get("DEPENDENCY_TYPE")
        edges.append(
            DependencyEdge(
                source=src,
                target=tgt,
                source_type=row.get("REFERENCING_OBJECT_DOMAIN"),
                target_type=row.get("REFERENCED_OBJECT_DOMAIN"),
                relationship=rel,
            )
        )
    return edges


def _query_information_schema(
    cli: SnowCLI, database: Optional[str], schema: Optional[str]
) -> List[DependencyEdge]:
    # Fallback using VIEW_TABLE_USAGE (only view→table dependencies)
    filters: List[str] = []
    if database:
        filters.append("lower(vtu.view_catalog) = lower($db)")
    if schema:
        filters.append("lower(vtu.view_schema) = lower($schema)")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    sql = f"""
    SELECT
      vtu.view_catalog,
      vtu.view_schema,
      vtu.view_name,
      vtu.table_catalog,
      vtu.table_schema,
      vtu.table_name
    FROM information_schema.view_table_usage vtu
    {where}
    """

    binds: Dict[str, str] = {}
    if database:
        binds["db"] = database
    if schema:
        binds["schema"] = schema
    for k, v in binds.items():
        sql = sql.replace(f"${k}", f"'{v}'")

    out = cli.run_query(sql, output_format="csv")
    edges: List[DependencyEdge] = []
    if not out.rows:
        return edges

    for row in out.rows:
        src = _fq(
            row.get("VIEW_CATALOG"), row.get("VIEW_SCHEMA"), row.get("VIEW_NAME") or ""
        )
        tgt = _fq(
            row.get("TABLE_CATALOG"),
            row.get("TABLE_SCHEMA"),
            row.get("TABLE_NAME") or "",
        )
        edges.append(
            DependencyEdge(
                source=src,
                target=tgt,
                source_type="VIEW",
                target_type="TABLE",
                relationship="uses",
            )
        )
    return edges


def build_dependency_graph(
    database: Optional[str] = None,
    schema: Optional[str] = None,
    account_scope: bool = True,
) -> Dict[str, object]:
    """Build a dependency graph and return a dict with nodes and edges.

    Nodes are unique fully qualified names with optional type.
    Edges connect source -> target with optional relationship.
    """
    cli = SnowCLI()
    try:
        edges = _query_account_usage(cli, database, schema) if account_scope else []
    except SnowCLIError:
        edges = []

    if not edges:
        # Fallback to information_schema
        edges = _query_information_schema(cli, database, schema)

    nodes: Dict[str, Dict[str, Optional[str]]] = {}
    out_edges: List[Dict[str, Optional[str]]] = []
    for e in edges:
        if e.source and e.source not in nodes:
            nodes[e.source] = {"id": e.source, "type": e.source_type}
        if e.target and e.target not in nodes:
            nodes[e.target] = {"id": e.target, "type": e.target_type}
        out_edges.append(
            {
                "source": e.source,
                "target": e.target,
                "relationship": e.relationship,
            }
        )

    return {
        "nodes": list(nodes.values()),
        "edges": out_edges,
        "counts": {"nodes": len(nodes), "edges": len(out_edges)},
        "scope": {
            "database": database,
            "schema": schema,
            "account_scope": account_scope,
        },
    }


def to_dot(graph: Dict[str, Any]) -> str:
    nodes: List[Dict[str, Any]] = graph.get("nodes", [])
    edges: List[Dict[str, Any]] = graph.get("edges", [])
    lines = ["digraph dependencies {"]
    for n in nodes:
        nid = n.get("id", "")  # type: ignore
        ntype = n.get("type", "")  # type: ignore
        label = nid.replace('"', "'")
        lines.append(f'  "{label}" [shape=box label="{label}\n({ntype})"];')
    for e in edges:
        s = (e.get("source") or "").replace('"', "'")  # type: ignore
        t = (e.get("target") or "").replace('"', "'")  # type: ignore
        rel = e.get("relationship") or ""  # type: ignore
        attr = f' [label="{rel}"]' if rel else ""
        lines.append(f'  "{s}" -> "{t}"{attr};')
    lines.append("}")
    return "\n".join(lines)
