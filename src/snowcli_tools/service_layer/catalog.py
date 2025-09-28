from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..catalog import build_catalog
from ..config import Config, get_config


class CatalogService:
    def __init__(self, *, config: Config | None = None) -> None:
        self._config = config or get_config()

    @property
    def config(self) -> Config:
        return self._config

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
    ) -> Dict[str, Any]:
        return build_catalog(
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
