from __future__ import annotations

from typing import Any, Dict, List, Optional, cast

from ..config import Config, get_config
from ..context import ServiceContext, create_service_context
from ..dependency import build_dependency_graph, to_dot
from ..models import (
    DependencyCounts,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyScope,
)


class DependencyService:
    def __init__(
        self, *, context: ServiceContext | None = None, config: Config | None = None
    ) -> None:
        if context is not None:
            self._context = context
        else:
            cfg = config or get_config()
            self._context = create_service_context(existing_config=cfg)

    @property
    def config(self) -> Config:
        return self._context.config

    @property
    def context(self) -> ServiceContext:
        return self._context

    def build(
        self,
        *,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        account_scope: bool = True,
    ) -> DependencyGraph:
        payload = build_dependency_graph(
            database=database,
            schema=schema,
            account_scope=account_scope,
        )
        raw_nodes = cast(List[Dict[str, Any]], payload.get("nodes", []))
        raw_edges = cast(List[Dict[str, Any]], payload.get("edges", []))
        raw_counts = cast(
            Dict[str, Any], payload.get("counts", {"nodes": 0, "edges": 0})
        )
        raw_scope = cast(Dict[str, Any], payload.get("scope", {}))
        return DependencyGraph(
            nodes=[DependencyNode(**node) for node in raw_nodes],
            edges=[DependencyEdge(**edge) for edge in raw_edges],
            counts=DependencyCounts(**raw_counts),
            scope=DependencyScope(**raw_scope),
        )

    def to_dot(self, graph: DependencyGraph) -> str:
        return to_dot(graph.model_dump(by_alias=True))
