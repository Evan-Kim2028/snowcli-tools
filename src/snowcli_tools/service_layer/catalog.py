from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional, cast

from ..catalog import build_catalog
from ..config import Config, get_config
from ..context import ServiceContext, create_service_context
from ..models import CatalogBuildResult, CatalogBuildTotals, CatalogMetadata


class CatalogService:
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
        output_dir: str,
        *,
        database: Optional[str] = None,
        account_scope: bool = False,
        incremental: bool = False,
        output_format: str = "json",
        include_ddl: bool = True,
        max_ddl_concurrency: int = 8,
        catalog_concurrency: Optional[int] = None,
        export_sql: bool = False,
    ) -> CatalogBuildResult:
        totals = build_catalog(
            output_dir,
            database=database,
            account_scope=account_scope,
            incremental=incremental,
            output_format=output_format,
            include_ddl=include_ddl,
            max_ddl_concurrency=max_ddl_concurrency,
            catalog_concurrency=catalog_concurrency or 16,
            export_sql=export_sql,
        )
        metadata = CatalogMetadata(
            output_dir=Path(output_dir),
            output_format=cast(Literal["json", "jsonl"], output_format),
            account_scope=account_scope,
            incremental=incremental,
            include_ddl=include_ddl,
            export_sql=export_sql,
            max_ddl_concurrency=max_ddl_concurrency,
            catalog_concurrency=catalog_concurrency,
        )
        totals_model = CatalogBuildTotals(**totals)
        return CatalogBuildResult(totals=totals_model, metadata=metadata)

    def load_summary(self, catalog_dir: str) -> Dict[str, Any]:
        path = Path(catalog_dir) / "catalog_summary.json"
        if not path.exists():
            return {
                "success": False,
                "message": f"No catalog summary found in {catalog_dir}. Run build_catalog first.",
            }
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": f"Failed to parse catalog summary at {path}",
            }
        return {"success": True, "catalog_dir": catalog_dir, "summary": data}
