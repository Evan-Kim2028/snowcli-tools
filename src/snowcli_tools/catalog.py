"""Snowflake catalog builder using Snowflake CLI connections.

Collects metadata from INFORMATION_SCHEMA and SHOW commands to assemble a
portable data catalog for any Snowflake account or database.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .snow_cli import SnowCLI, SnowCLIError


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, rows: List[Dict]) -> None:
    with path.open("w") as f:
        json.dump(rows, f, indent=2, default=str)


def _write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str))
            f.write("\n")


def _run_json(cli: SnowCLI, query: str) -> List[Dict]:
    out = cli.run_query(query, output_format="json")
    return out.rows or []


def _run_json_safe(cli: SnowCLI, query: str) -> List[Dict]:
    try:
        return _run_json(cli, query)
    except SnowCLIError:
        return []


def _list_databases(
    cli: SnowCLI, include_account: bool, only_database: Optional[str]
) -> List[str]:
    if only_database:
        return [only_database]
    if not include_account:
        # Rely on current connection's default database via SELECT CURRENT_DATABASE()
        db = _run_json(cli, "SELECT CURRENT_DATABASE() AS DB").pop().get("DB")
        return [db] if db else []
    # Account-wide
    rows = _run_json(cli, "SHOW DATABASES")
    names: List[str] = []
    for r in rows:
        name = r.get("name") or r.get("database_name") or r.get("DATABASE_NAME")
        if name:
            names.append(name)
    return names


def _list_schemas(cli: SnowCLI, database: str) -> List[str]:
    # Prefer SHOW SCHEMAS (less privilege-sensitive than INFORMATION_SCHEMA)
    rows = _run_json_safe(cli, f"SHOW SCHEMAS IN DATABASE {database}")
    names: List[str] = []
    for r in rows:
        name = r.get("name") or r.get("schema_name") or r.get("SCHEMA_NAME")
        if name:
            names.append(name)
    return names


def _quote_ident(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def _get_ddl(
    cli: SnowCLI, object_type: str, fq_name: str, timeout: int = 60
) -> Optional[str]:
    try:
        out = cli.run_query(
            f"SELECT GET_DDL('{object_type}', '{fq_name}') AS DDL",
            output_format="json",
            timeout=timeout,
        )
        rows = out.rows or []
        if rows and isinstance(rows, list):
            r0 = rows[0]
            return r0.get("DDL") or r0.get("ddl") or next(iter(r0.values()))
    except SnowCLIError:
        return None
    return None


def build_catalog(
    output_dir: str,
    *,
    database: Optional[str] = None,
    account_scope: bool = False,
    output_format: str = "json",
    include_ddl: bool = True,
    max_ddl_concurrency: int = 8,
) -> Dict[str, int]:
    """Build a JSON data catalog under `output_dir`.

    - database: specific database to introspect; if None, uses current database
    - account_scope: if True, spans all databases (requires privileges)
    """
    cli = SnowCLI()
    out_path = Path(output_dir)
    _ensure_dir(out_path)

    totals = {
        "databases": 0,
        "schemas": 0,
        "tables": 0,
        "columns": 0,
        "views": 0,
        "materialized_views": 0,
        "routines": 0,
        "tasks": 0,
        "dynamic_tables": 0,
    }

    databases = _list_databases(cli, account_scope, database)
    totals["databases"] = len(databases)

    all_schemata: List[Dict] = []
    all_tables: List[Dict] = []
    all_columns: List[Dict] = []
    all_views: List[Dict] = []
    all_mviews: List[Dict] = []
    all_routines: List[Dict] = []
    all_tasks: List[Dict] = []
    all_dynamic: List[Dict] = []
    all_functions: List[Dict] = []
    all_procedures: List[Dict] = []

    for db in databases:
        schemas = _list_schemas(cli, db)
        for sch in schemas:
            # Schemas
            rows = _run_json_safe(
                cli,
                f"SELECT * FROM {db}.INFORMATION_SCHEMA.SCHEMATA "
                f"WHERE SCHEMA_NAME = '{sch}'",
            )
            for r in rows:
                r.setdefault("DATABASE_NAME", db)
            all_schemata.extend(rows)

            # Tables and Columns
            tables = _run_json_safe(
                cli,
                f"SELECT * FROM {db}.INFORMATION_SCHEMA.TABLES "
                f"WHERE TABLE_SCHEMA = '{sch}'",
            )
            for r in tables:
                r.setdefault("DATABASE_NAME", db)
            all_tables.extend(tables)

            cols = _run_json_safe(
                cli,
                f"SELECT * FROM {db}.INFORMATION_SCHEMA.COLUMNS "
                f"WHERE TABLE_SCHEMA = '{sch}'",
            )
            for r in cols:
                r.setdefault("DATABASE_NAME", db)
            all_columns.extend(cols)

            # Views
            views = _run_json_safe(
                cli,
                f"SELECT * FROM {db}.INFORMATION_SCHEMA.VIEWS "
                f"WHERE TABLE_SCHEMA = '{sch}'",
            )
            for r in views:
                r.setdefault("DATABASE_NAME", db)
            all_views.extend(views)

            # Materialized Views (if privileges)
            # MATERIALIZED VIEWS (SHOW is more permissive than INFORMATION_SCHEMA)
            mviews = _run_json_safe(
                cli,
                f"SHOW MATERIALIZED VIEWS IN SCHEMA {db}.{sch}",
            )
            for r in mviews:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            all_mviews.extend(mviews)

            # Routines (Procedures/Functions)
            routines = _run_json_safe(
                cli,
                f"SELECT * FROM {db}.INFORMATION_SCHEMA.ROUTINES "
                f"WHERE ROUTINE_SCHEMA = '{sch}'",
            )
            for r in routines:
                r.setdefault("DATABASE_NAME", db)
            all_routines.extend(routines)

            # Tasks (SHOW is widely permitted; ACCOUNT_USAGE requires privileges)
            try:
                tasks = _run_json(cli, f"SHOW TASKS IN SCHEMA {db}.{sch}")
                for r in tasks:
                    r.setdefault("DATABASE_NAME", db)
                    r.setdefault("SCHEMA_NAME", sch)
                all_tasks.extend(tasks)
            except SnowCLIError:
                pass

            # Dynamic tables (SHOW is widely permitted)
            try:
                dyn = _run_json(cli, f"SHOW DYNAMIC TABLES IN SCHEMA {db}.{sch}")
                for r in dyn:
                    r.setdefault("DATABASE_NAME", db)
                    r.setdefault("SCHEMA_NAME", sch)
                all_dynamic.extend(dyn)
            except SnowCLIError:
                pass

            # User-defined functions (UDFs)
            try:
                funcs = _run_json(cli, f"SHOW USER FUNCTIONS IN SCHEMA {db}.{sch}")
                for r in funcs:
                    r.setdefault("DATABASE_NAME", db)
                    r.setdefault("SCHEMA_NAME", sch)
                all_functions.extend(funcs)
            except SnowCLIError:
                pass

            # Stored procedures
            try:
                procs = _run_json(cli, f"SHOW PROCEDURES IN SCHEMA {db}.{sch}")
                for r in procs:
                    r.setdefault("DATABASE_NAME", db)
                    r.setdefault("SCHEMA_NAME", sch)
                all_procedures.extend(procs)
            except SnowCLIError:
                pass

    totals["schemas"] = len(all_schemata)
    totals["tables"] = len(all_tables)
    totals["columns"] = len(all_columns)
    totals["views"] = len(all_views)
    totals["materialized_views"] = len(all_mviews)
    totals["routines"] = len(all_routines)
    totals["tasks"] = len(all_tasks)
    totals["dynamic_tables"] = len(all_dynamic)
    totals["functions"] = len(all_functions)
    totals["procedures"] = len(all_procedures)

    writer = _write_jsonl if output_format.lower() == "jsonl" else _write_json
    writer(out_path / f"schemata.{output_format}", all_schemata)
    writer(out_path / f"tables.{output_format}", all_tables)
    writer(out_path / f"columns.{output_format}", all_columns)
    writer(out_path / f"views.{output_format}", all_views)
    writer(out_path / f"materialized_views.{output_format}", all_mviews)
    writer(out_path / f"routines.{output_format}", all_routines)
    writer(out_path / f"tasks.{output_format}", all_tasks)
    writer(out_path / f"dynamic_tables.{output_format}", all_dynamic)
    writer(out_path / f"functions.{output_format}", all_functions)
    writer(out_path / f"procedures.{output_format}", all_procedures)

    # index file
    # Optionally include DDLs
    if include_ddl:
        # Prepare DDL fetch tasks (object_type, fq_name, record)
        ddl_jobs: List[Tuple[str, str, Dict]] = []

        def add_job(obj_type: str, name_key: str, rec: Dict, sig: Optional[str] = None):
            db = rec.get("database_name") or rec.get("DATABASE_NAME")
            sch = rec.get("schema_name") or rec.get("SCHEMA_NAME")
            name = rec.get(name_key) or rec.get(name_key.upper()) or rec.get("name")
            if db and sch and name:
                if sig:
                    fq = (
                        f"{_quote_ident(db)}.{_quote_ident(sch)}."
                        f"{_quote_ident(name)}({sig})"
                    )
                else:
                    fq = f"{_quote_ident(db)}.{_quote_ident(sch)}.{_quote_ident(name)}"
                ddl_jobs.append((obj_type, fq, rec))

        for r in all_views:
            add_job("VIEW", "VIEW_NAME", r)
        for r in all_mviews:
            add_job("MATERIALIZED VIEW", "MATERIALIZED_VIEW_NAME", r)
        for r in all_tasks:
            add_job("TASK", "TASK_NAME", r)
        for r in all_dynamic:
            add_job("DYNAMIC TABLE", "DYNAMIC_TABLE_NAME", r)
        for r in all_functions:
            sig = r.get("arguments") or r.get("signature")
            add_job("FUNCTION", "FUNCTION_NAME", r, sig)
        for r in all_procedures:
            sig = r.get("arguments") or r.get("signature")
            add_job("PROCEDURE", "PROCEDURE_NAME", r, sig)

        # Fetch in parallel
        def fetch(job: Tuple[str, str, Dict]) -> Tuple[Dict, Optional[str]]:
            obj_type, fq, rec = job
            ddl = _get_ddl(cli, obj_type, fq)
            return rec, ddl

        with ThreadPoolExecutor(max_workers=max_ddl_concurrency) as ex:
            futures = [ex.submit(fetch, j) for j in ddl_jobs]
            for fut in as_completed(futures):
                rec, ddl = fut.result()
                if ddl:
                    rec["ddl"] = ddl

    _write_json(
        out_path / "catalog_summary.json", [{"totals": totals, "databases": databases}]
    )
    return totals
