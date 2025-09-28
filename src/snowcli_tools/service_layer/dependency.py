from __future__ import annotations

from typing import Dict, Optional

from ..config import Config, get_config
from ..dependency import build_dependency_graph, to_dot


class DependencyService:
    def __init__(self, *, config: Config | None = None) -> None:
        self._config = config or get_config()

    @property
    def config(self) -> Config:
        return self._config

    def build(
        self,
        *,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        account_scope: bool = True,
    ) -> Dict[str, object]:
        return build_dependency_graph(
            database=database,
            schema=schema,
            account_scope=account_scope,
        )

    def to_dot(self, graph: Dict[str, object]) -> str:
        return to_dot(graph)
