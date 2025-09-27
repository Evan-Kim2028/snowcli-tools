"""Service layer for catalog operations with proper separation of concerns."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .snow_cli import SnowCLI, SnowCLIError


@dataclass
class CatalogTotals:
    """Tracks totals for different object types in the catalog."""

    databases: int = 0
    schemas: int = 0
    tables: int = 0
    columns: int = 0
    views: int = 0
    materialized_views: int = 0
    routines: int = 0
    tasks: int = 0
    dynamic_tables: int = 0
    functions: int = 0
    procedures: int = 0


@dataclass
class CatalogData:
    """Holds all collected catalog data."""

    schemata: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[Dict[str, Any]] = field(default_factory=list)
    views: List[Dict[str, Any]] = field(default_factory=list)
    mviews: List[Dict[str, Any]] = field(default_factory=list)
    routines: List[Dict[str, Any]] = field(default_factory=list)
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    dynamic: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    procedures: List[Dict[str, Any]] = field(default_factory=list)

    def extend_from(self, other: "CatalogData") -> None:
        """Extend this catalog data with data from another instance."""
        self.schemata.extend(other.schemata)
        self.tables.extend(other.tables)
        self.columns.extend(other.columns)
        self.views.extend(other.views)
        self.mviews.extend(other.mviews)
        self.routines.extend(other.routines)
        self.tasks.extend(other.tasks)
        self.dynamic.extend(other.dynamic)
        self.functions.extend(other.functions)
        self.procedures.extend(other.procedures)


@dataclass
class CatalogConfig:
    """Configuration for catalog building operations."""

    database: Optional[str] = None
    account_scope: bool = False
    incremental: bool = False
    output_format: str = "json"
    include_ddl: bool = True
    max_ddl_concurrency: int = 8
    catalog_concurrency: int = 16
    export_sql: bool = False


class DatabaseDiscoveryService:
    """Service for discovering databases and schemas."""

    def __init__(self, cli: SnowCLI):
        self.cli = cli

    def list_databases(
        self, include_account: bool, only_database: Optional[str]
    ) -> List[str]:
        """List available databases based on scope."""
        if only_database:
            return [only_database]
        if not include_account:
            # Rely on current connection's default database via SELECT CURRENT_DATABASE()
            from .catalog import _run_json

            db = _run_json(self.cli, "SELECT CURRENT_DATABASE() AS DB").pop().get("DB")
            return [db] if db else []
        # Account-wide
        from .catalog import _run_json

        rows = _run_json(self.cli, "SHOW DATABASES")
        names: List[str] = []
        for r in rows:
            name = r.get("name") or r.get("database_name") or r.get("DATABASE_NAME")
            if name:
                names.append(name)
        return names

    def list_schemas(self, database: str) -> List[str]:
        """List schemas for a given database."""
        from .catalog import _run_json_safe

        # Prefer SHOW SCHEMAS (less privilege-sensitive than INFORMATION_SCHEMA)
        rows = _run_json_safe(self.cli, f"SHOW SCHEMAS IN DATABASE {database}")
        names: List[str] = []
        for r in rows:
            name = r.get("name") or r.get("schema_name") or r.get("SCHEMA_NAME")
            if name:
                names.append(name)
        return names


class SchemaMetadataCollector:
    """Collects metadata for a single schema."""

    def __init__(self, cli: SnowCLI):
        self.cli = cli

    def collect_schema_metadata(self, db: str, sch: str) -> CatalogData:
        """Collect all metadata for a specific schema."""
        from .catalog import _run_json, _run_json_safe

        data = CatalogData()

        # Schemas
        rows = _run_json_safe(
            self.cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{sch}'",
        )
        for r in rows:
            r.setdefault("DATABASE_NAME", db)
        data.schemata.extend(rows)

        # Tables and Columns
        tables = _run_json_safe(
            self.cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in tables:
            r.setdefault("DATABASE_NAME", db)
        data.tables.extend(tables)

        cols = _run_json_safe(
            self.cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in cols:
            r.setdefault("DATABASE_NAME", db)
        data.columns.extend(cols)

        # Views
        views = _run_json_safe(
            self.cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in views:
            r.setdefault("DATABASE_NAME", db)
        data.views.extend(views)

        # Materialized Views
        mviews = _run_json_safe(
            self.cli, f"SHOW MATERIALIZED VIEWS IN SCHEMA {db}.{sch}"
        )
        for r in mviews:
            r.setdefault("DATABASE_NAME", db)
            r.setdefault("SCHEMA_NAME", sch)
        data.mviews.extend(mviews)

        # Routines
        routines = _run_json_safe(
            self.cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = '{sch}'",
        )
        for r in routines:
            r.setdefault("DATABASE_NAME", db)
        data.routines.extend(routines)

        # Tasks
        try:
            tasks = _run_json(self.cli, f"SHOW TASKS IN SCHEMA {db}.{sch}")
            for r in tasks:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            data.tasks.extend(tasks)
        except SnowCLIError:
            pass

        # Dynamic tables
        try:
            dyn = _run_json(self.cli, f"SHOW DYNAMIC TABLES IN SCHEMA {db}.{sch}")
            for r in dyn:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            data.dynamic.extend(dyn)
        except SnowCLIError:
            pass

        # Functions
        try:
            funcs = _run_json(self.cli, f"SHOW USER FUNCTIONS IN SCHEMA {db}.{sch}")
            for r in funcs:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            data.functions.extend(funcs)
        except SnowCLIError:
            pass

        # Procedures
        try:
            procs = _run_json(self.cli, f"SHOW PROCEDURES IN SCHEMA {db}.{sch}")
            for r in procs:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            data.procedures.extend(procs)
        except SnowCLIError:
            pass

        return data


class CatalogBuilder:
    """Main service for building catalogs with proper separation of concerns."""

    def __init__(self):
        self.cli = SnowCLI()
        self.discovery_service = DatabaseDiscoveryService(self.cli)
        self.metadata_collector = SchemaMetadataCollector(self.cli)

    def build_schema_worklist(self, config: CatalogConfig) -> List[Tuple[str, str]]:
        """Build list of (database, schema) pairs to process."""
        databases = self.discovery_service.list_databases(
            config.account_scope, config.database
        )
        schema_pairs: List[Tuple[str, str]] = []
        for db in databases:
            for sch in self.discovery_service.list_schemas(db):
                schema_pairs.append((db, sch))
        return schema_pairs

    def collect_metadata_parallel(
        self, schema_pairs: List[Tuple[str, str]], catalog_concurrency: int
    ) -> CatalogData:
        """Collect metadata for all schemas in parallel."""
        all_data = CatalogData()

        with ThreadPoolExecutor(max_workers=max(1, int(catalog_concurrency))) as ex:
            futures = [
                ex.submit(self.metadata_collector.collect_schema_metadata, db, sch)
                for db, sch in schema_pairs
            ]
            for fut in as_completed(futures):
                schema_data = fut.result()
                all_data.extend_from(schema_data)

        return all_data

    def calculate_totals(self, data: CatalogData, num_databases: int) -> CatalogTotals:
        """Calculate totals from collected data."""
        return CatalogTotals(
            databases=num_databases,
            schemas=len(data.schemata),
            tables=len(data.tables),
            columns=len(data.columns),
            views=len(data.views),
            materialized_views=len(data.mviews),
            routines=len(data.routines),
            tasks=len(data.tasks),
            dynamic_tables=len(data.dynamic),
            functions=len(data.functions),
            procedures=len(data.procedures),
        )
