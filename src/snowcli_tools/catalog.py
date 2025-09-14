"""Snowflake catalog + SQL exporter (backed by the official `snow` CLI).

Features
- Parallel catalog builder: collects metadata via INFORMATION_SCHEMA and SHOW
  to assemble a portable JSON/JSONL catalog for any Snowflake account.
- Optional DDL capture: concurrently fetches object DDL via GET_DDL and
  embeds it in the JSON (when enabled).
- SQL export from JSON: generates a categorized SQL tree from existing
  catalog files, fetching missing DDL on demand.

SQL export layout
- <output_dir>/tables/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/views/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/materialized_views/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/dynamic_tables/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/tasks/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/functions/<DB>/<SCHEMA>/<OBJECT>.sql
- <output_dir>/procedures/<DB>/<SCHEMA>/<OBJECT>.sql

Notes
- GET_DDL object type mapping differences:
  - Materialized views require GET_DDL('VIEW', ...)
  - Dynamic tables require GET_DDL('TABLE', ...)
- Function/procedure signatures are normalized from SHOW outputs when
  constructing fully-qualified names for GET_DDL.
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _safe_filename(name: str) -> str:
    # Basic sanitization for filesystem safety
    return name.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")


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


# Sampling helpers removed in this refactor


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


def _extract_args_from_arguments_field(
    name: str, arguments: Optional[str], signature: Optional[str]
) -> Optional[str]:
    """Extract the parenthesized argument list for functions/procedures.

    Inputs observed from SHOW outputs often look like:
      - "FUNCNAME(TYPE, TYPE) RETURN VARCHAR"
      - "PROCEDURE_NAME(TYPE, TYPE) RETURN TABLE (...)"
      - Or sometimes a dedicated `signature` like "(TYPE, TYPE)"

    We return a string that includes the surrounding parentheses, e.g., "(TYPE, TYPE)".
    Returns None if no argument list can be determined (e.g., UDFs with no args -> "()").
    """
    if signature:
        sig = signature.strip()
        # Ensure it is parenthesized already
        if sig.startswith("(") and sig.endswith(")"):
            return sig
        # If not, try to wrap
        if sig:
            return f"({sig})"
        return "()"

    if not arguments:
        return None
    s = arguments.strip()
    # Find the first '(' after the name occurrence (case-insensitive match of name prefix)
    # But simpler/safer: find first '(' at all and match until the balancing ')'
    i = s.find("(")
    if i == -1:
        return None
    # Extract until the matching ')'
    depth = 0
    end = None
    for idx in range(i, len(s)):
        ch = s[idx]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = idx
                break
    if end is None:
        return None
    arg_part = s[i : end + 1]
    if not arg_part:
        return None
    return arg_part


def build_catalog(
    output_dir: str,
    *,
    database: Optional[str] = None,
    account_scope: bool = False,
    incremental: bool = False,
    output_format: str = "json",
    include_ddl: bool = True,
    max_ddl_concurrency: int = 8,
    catalog_concurrency: int = 16,
    export_sql: bool = False,
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

    # Sampling disabled: no sample queries or indices

    # Build schema worklist
    schema_pairs: List[Tuple[str, str]] = []
    for db in databases:
        for sch in _list_schemas(cli, db):
            schema_pairs.append((db, sch))

    def process_schema(db: str, sch: str) -> Dict[str, List[Dict]]:
        local: Dict[str, List[Dict]] = {
            "schemata": [],
            "tables": [],
            "columns": [],
            "views": [],
            "mviews": [],
            "routines": [],
            "tasks": [],
            "dynamic": [],
            "functions": [],
            "procedures": [],
        }
        # Schemas
        rows = _run_json_safe(
            cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{sch}'",
        )
        for r in rows:
            r.setdefault("DATABASE_NAME", db)
        local["schemata"].extend(rows)

        # Tables and Columns
        tables = _run_json_safe(
            cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in tables:
            r.setdefault("DATABASE_NAME", db)
        local["tables"].extend(tables)

        cols = _run_json_safe(
            cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in cols:
            r.setdefault("DATABASE_NAME", db)
        local["columns"].extend(cols)

        # Views
        views = _run_json_safe(
            cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{sch}'",
        )
        for r in views:
            r.setdefault("DATABASE_NAME", db)
        local["views"].extend(views)

        # Materialized Views
        mviews = _run_json_safe(cli, f"SHOW MATERIALIZED VIEWS IN SCHEMA {db}.{sch}")
        for r in mviews:
            r.setdefault("DATABASE_NAME", db)
            r.setdefault("SCHEMA_NAME", sch)
        local["mviews"].extend(mviews)

        # Routines
        routines = _run_json_safe(
            cli,
            f"SELECT * FROM {db}.INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = '{sch}'",
        )
        for r in routines:
            r.setdefault("DATABASE_NAME", db)
        local["routines"].extend(routines)

        # Tasks
        try:
            tasks = _run_json(cli, f"SHOW TASKS IN SCHEMA {db}.{sch}")
            for r in tasks:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            local["tasks"].extend(tasks)
        except SnowCLIError:
            pass

        # Dynamic tables
        try:
            dyn = _run_json(cli, f"SHOW DYNAMIC TABLES IN SCHEMA {db}.{sch}")
            for r in dyn:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            local["dynamic"].extend(dyn)
        except SnowCLIError:
            pass

        # Functions
        try:
            funcs = _run_json(cli, f"SHOW USER FUNCTIONS IN SCHEMA {db}.{sch}")
            for r in funcs:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            local["functions"].extend(funcs)
        except SnowCLIError:
            pass

        # Procedures
        try:
            procs = _run_json(cli, f"SHOW PROCEDURES IN SCHEMA {db}.{sch}")
            for r in procs:
                r.setdefault("DATABASE_NAME", db)
                r.setdefault("SCHEMA_NAME", sch)
            local["procedures"].extend(procs)
        except SnowCLIError:
            pass

        # Sampling removed

        return local

    # Run schema processing in parallel
    with ThreadPoolExecutor(max_workers=max(1, int(catalog_concurrency))) as ex:
        futures = [ex.submit(process_schema, db, sch) for db, sch in schema_pairs]
        for fut in as_completed(futures):
            res = fut.result()
            all_schemata.extend(res["schemata"])
            all_tables.extend(res["tables"])
            all_columns.extend(res["columns"])
            all_views.extend(res["views"])
            all_mviews.extend(res["mviews"])
            all_routines.extend(res["routines"])
            all_tasks.extend(res["tasks"])
            all_dynamic.extend(res["dynamic"])
            all_functions.extend(res["functions"])
            all_procedures.extend(res["procedures"])

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

    # Incremental state support
    state_path = out_path / "catalog_state.json"
    prev_state: Dict[str, Any] = {}
    if incremental and state_path.exists():
        try:
            prev_state = json.loads(state_path.read_text())
        except Exception:
            prev_state = {}

    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _kv(rec: Dict, *keys: str) -> Optional[str]:
        for k in keys:
            if k in rec and rec.get(k) is not None:
                return str(rec.get(k))
        lower = {str(k).lower(): v for k, v in rec.items()}
        for k in keys:
            v = lower.get(k.lower())
            if v is not None:
                return str(v)
        return None

    def _change_token(rec: Dict) -> Optional[str]:
        return _kv(
            rec,
            "LAST_ALTERED",
            "LAST_MODIFIED",
            "LAST_DDL",
            "MODIFIED",
            "UPDATED_ON",
            "CREATED",
            "CREATED_ON",
        )

    def _sig_for(rec: Dict, name: Optional[str]) -> Optional[str]:
        return _extract_args_from_arguments_field(
            str(name) if name else "", rec.get("arguments"), rec.get("signature")
        )

    def _identity(
        category: str, rec: Dict, name_key: str, sig: Optional[str]
    ) -> Optional[str]:
        db = (
            rec.get("DATABASE_NAME")
            or rec.get("TABLE_CATALOG")
            or rec.get("CATALOG_NAME")
            or rec.get("database_name")
        )
        sch = (
            rec.get("SCHEMA_NAME") or rec.get("TABLE_SCHEMA") or rec.get("schema_name")
        )
        name = rec.get(name_key) or rec.get(name_key.upper()) or rec.get("name")
        if not (db and sch and name):
            return None
        cat = category.upper()
        ident = f"{cat}|{str(db).upper()}|{str(sch).upper()}|{str(name).upper()}"
        if category in ("FUNCTION", "PROCEDURE"):
            sig_norm = sig or "()"
            ident += sig_norm
        return ident

    # Build map of previous DDLs when incremental and include_ddl
    prev_ddl_map: Dict[str, str] = {}
    if incremental and include_ddl:

        def load_prev(base: str, category: str, name_key: str) -> None:
            p = _find_catalog_file(out_path, base)
            if not p:
                return
            for r in _load_rows(p):
                name = r.get(name_key) or r.get(name_key.upper()) or r.get("name")
                sig = (
                    _sig_for(r, name) if category in ("FUNCTION", "PROCEDURE") else None
                )
                ident = _identity(category, r, name_key, sig)
                ddl = r.get("ddl")
                if ident and ddl:
                    prev_ddl_map[ident] = str(ddl)

        load_prev("tables", "TABLE", "TABLE_NAME")
        load_prev("views", "VIEW", "TABLE_NAME")
        load_prev("materialized_views", "MVIEW", "MATERIALIZED_VIEW_NAME")
        load_prev("tasks", "TASK", "TASK_NAME")
        load_prev("dynamic_tables", "DTABLE", "DYNAMIC_TABLE_NAME")
        load_prev("functions", "FUNCTION", "FUNCTION_NAME")
        load_prev("procedures", "PROCEDURE", "PROCEDURE_NAME")

    # Optionally include DDLs
    if include_ddl:
        # Prepare DDL fetch tasks (object_type, fq_name, record)
        ddl_jobs: List[Tuple[str, str, Dict, str, Optional[str]]] = []

        def add_job(
            obj_type: str,
            name_key: str,
            rec: Dict,
            sig: Optional[str] = None,
            id_category: Optional[str] = None,
        ) -> None:
            # Be permissive about key casing and field naming across SHOW/INFORMATION_SCHEMA outputs
            db = (
                rec.get("database_name")
                or rec.get("DATABASE_NAME")
                or rec.get("catalog_name")
                or rec.get("CATALOG_NAME")
            )
            sch = (
                rec.get("schema_name")
                or rec.get("SCHEMA_NAME")
                or rec.get("TABLE_SCHEMA")
                or rec.get("table_schema")
            )
            name = rec.get(name_key) or rec.get(name_key.upper()) or rec.get("name")
            if db and sch and name:
                if sig:
                    # `sig` may already include parentheses; normalize
                    sig_norm = sig if sig.startswith("(") else f"({sig})"
                    fq = (
                        f"{_quote_ident(db)}.{_quote_ident(sch)}."
                        f"{_quote_ident(name)}{sig_norm}"
                    )
                else:
                    fq = f"{_quote_ident(db)}.{_quote_ident(sch)}.{_quote_ident(name)}"
                category = (id_category or obj_type).upper()
                ident = _identity(category, rec, name_key, sig)
                token = _change_token(rec)
                if incremental and ident and token:
                    prev_obj = (prev_state.get("objects", {}) or {}).get(ident)
                    if prev_obj and str(prev_obj.get("last_altered")) == str(token):
                        # unchanged: skip fetching; will backfill from prev map if available
                        return
                if incremental and ident and prev_ddl_map.get(ident):
                    # have previous DDL we can backfill
                    return
                ddl_jobs.append((obj_type, fq, rec, category, ident))

        # Tables
        for r in all_tables:
            # INFORMATION_SCHEMA.TABLES uses TABLE_NAME for the table name
            add_job("TABLE", "TABLE_NAME", r, None, "TABLE")

        for r in all_views:
            # INFORMATION_SCHEMA.VIEWS uses TABLE_NAME for the view name
            add_job("VIEW", "TABLE_NAME", r, None, "VIEW")
        for r in all_mviews:
            # SHOW MATERIALIZED VIEWS uses `name`; GET_DDL expects VIEW for mviews
            add_job("VIEW", "name", r, None, "MVIEW")
        for r in all_tasks:
            # SHOW TASKS uses `name`
            add_job("TASK", "name", r, None, "TASK")
        for r in all_dynamic:
            # SHOW DYNAMIC TABLES uses `name`; GET_DDL expects TABLE for dynamic tables
            add_job("TABLE", "name", r, None, "DTABLE")
        for r in all_functions:
            # SHOW USER FUNCTIONS uses `name` + `arguments`
            name = r.get("name")
            sig = _extract_args_from_arguments_field(
                str(name) if name else "", r.get("arguments"), r.get("signature")
            )
            add_job("FUNCTION", "name", r, sig, "FUNCTION")
        for r in all_procedures:
            # SHOW PROCEDURES uses `name` + `arguments`
            name = r.get("name")
            sig = _extract_args_from_arguments_field(
                str(name) if name else "", r.get("arguments"), r.get("signature")
            )
            add_job("PROCEDURE", "name", r, sig, "PROCEDURE")

        # Fetch in parallel
        def fetch(
            job: Tuple[str, str, Dict, str, Optional[str]],
        ) -> Tuple[Dict, Optional[str], str, Optional[str]]:
            obj_type, fq, rec, category, ident = job
            ddl = _get_ddl(cli, obj_type, fq)
            return rec, ddl, category, ident

        with ThreadPoolExecutor(max_workers=max_ddl_concurrency) as ddl_ex:
            ddl_futures = [ddl_ex.submit(fetch, j) for j in ddl_jobs]
            for ddl_future in as_completed(ddl_futures):
                rec, ddl, category, ident = ddl_future.result()
                if ddl:
                    # Ensure correct type for mypy
                    rec = dict(rec)  # type: ignore[assignment]
                    rec["ddl"] = ddl
                    if incremental and ident:
                        prev_ddl_map[ident] = ddl

    # After possible DDL enrichment, write JSON files to disk
    writer = _write_jsonl if output_format.lower() == "jsonl" else _write_json
    # If incremental with include_ddl, backfill unchanged objects' DDL from previous JSON/state
    if incremental and include_ddl and prev_ddl_map:

        def backfill(lst: List[Dict], category: str, name_key: str) -> None:
            for r in lst:
                if r.get("ddl"):
                    continue
                name = r.get(name_key) or r.get(name_key.upper()) or r.get("name")
                sig = (
                    _sig_for(r, name) if category in ("FUNCTION", "PROCEDURE") else None
                )
                ident = _identity(category, r, name_key, sig)
                ddl = prev_ddl_map.get(ident or "")
                if ddl:
                    r["ddl"] = ddl

        backfill(all_tables, "TABLE", "TABLE_NAME")
        backfill(all_views, "VIEW", "TABLE_NAME")
        backfill(all_mviews, "MVIEW", "MATERIALIZED_VIEW_NAME")
        backfill(all_tasks, "TASK", "TASK_NAME")
        backfill(all_dynamic, "DTABLE", "DYNAMIC_TABLE_NAME")
        backfill(all_functions, "FUNCTION", "FUNCTION_NAME")
        backfill(all_procedures, "PROCEDURE", "PROCEDURE_NAME")
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

    # Export SQL files if requested (delegates to function that reads JSON back)
    if export_sql:
        export_sql_from_catalog(output_dir, max_workers=catalog_concurrency)

    _write_json(
        out_path / "catalog_summary.json", [{"totals": totals, "databases": databases}]
    )

    # Save incremental state
    if incremental:
        objects_state: Dict[str, Any] = {}

        def upd(lst: List[Dict], category: str, name_key: str) -> None:
            for r in lst:
                name = r.get(name_key) or r.get(name_key.upper()) or r.get("name")
                sig = (
                    _sig_for(r, name) if category in ("FUNCTION", "PROCEDURE") else None
                )
                ident = _identity(category, r, name_key, sig)
                if not ident:
                    continue
                token = _change_token(r) or ""
                entry: Dict[str, Any] = {"last_altered": token}
                ddl_text = r.get("ddl")
                if ddl_text:
                    h = hashlib.sha256(str(ddl_text).encode("utf-8")).hexdigest()
                    entry["ddl_hash"] = f"sha256:{h}"
                objects_state[ident] = entry

        upd(all_tables, "TABLE", "TABLE_NAME")
        upd(all_views, "VIEW", "TABLE_NAME")
        upd(all_mviews, "MVIEW", "MATERIALIZED_VIEW_NAME")
        upd(all_tasks, "TASK", "TASK_NAME")
        upd(all_dynamic, "DTABLE", "DYNAMIC_TABLE_NAME")
        upd(all_functions, "FUNCTION", "FUNCTION_NAME")
        upd(all_procedures, "PROCEDURE", "PROCEDURE_NAME")

        new_state = {
            "version": 1,
            "generated_at": _now_iso(),
            "objects": objects_state,
        }
        state_path.write_text(json.dumps(new_state, indent=2))

    return totals


def _load_rows(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    # Detect JSON vs JSONL by extension/name
    if path.suffix.lower() == ".jsonl":
        rows: List[Dict] = []
        with path.open("r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows
    else:
        try:
            data = json.loads(path.read_text())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def _find_catalog_file(root: Path, base: str) -> Optional[Path]:
    # Prefer .json, then .jsonl
    for ext in (".json", ".jsonl"):
        p = root / f"{base}{ext}"
        if p.exists():
            return p
    return None


def export_sql_from_catalog(
    input_dir: str, output_dir: Optional[str] = None, *, max_workers: int = 16
) -> Dict[str, int]:
    """Generate a categorized SQL tree from existing catalog JSON files.

    Layout: <output_dir>/sql/<asset_type>/<DB>/<SCHEMA>/<OBJECT>.sql
    Asset types: tables, views, materialized_views, tasks, dynamic_tables,
    functions, procedures.
    If a record lacks a `ddl` field, attempts to fetch via GET_DDL.
    """
    cli = SnowCLI()
    in_root = Path(input_dir)
    sql_root = Path(output_dir) if output_dir else in_root / "sql"
    sql_root.mkdir(parents=True, exist_ok=True)

    summary_path = in_root / "catalog_summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
            totals = (summary[0] if isinstance(summary, list) and summary else {}).get(
                "totals", {}
            )
            if all(int(totals.get(k, 0)) == 0 for k in ["schemas", "tables", "views"]):
                # Nothing to do
                return {"written": 0, "missing": 0}
        except Exception:
            pass

    from concurrent.futures import ThreadPoolExecutor, as_completed

    counts = {"written": 0, "missing": 0}

    def write(cat: str, dbn: str, schn: str, name: str, ddl: Optional[str]) -> int:
        if not ddl:
            return 0
        p = sql_root / cat / _safe_filename(dbn) / _safe_filename(schn)
        p.mkdir(parents=True, exist_ok=True)
        with (p / f"{_safe_filename(name)}.sql").open("w") as f:
            f.write(ddl)
        return 1

    # Helper to fetch DDL if missing
    def fetch_or_none(obj_type: str, fq: str, existing: Optional[str]) -> Optional[str]:
        if existing:
            return existing
        try:
            return _get_ddl(cli, obj_type, fq)
        except SnowCLIError:
            return None

    # Accumulate jobs: (category, obj_type, db, schema, name, fq, existing_ddl)
    jobs: List[Tuple[str, str, str, str, str, str, Optional[str]]] = []

    # Tables
    path = _find_catalog_file(in_root, "tables")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME") or r.get("TABLE_CATALOG")
            schn = r.get("TABLE_SCHEMA")
            name = r.get("TABLE_NAME")
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}"
            jobs.append(
                (
                    "tables",
                    "TABLE",
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Views
    path = _find_catalog_file(in_root, "views")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("TABLE_SCHEMA") or r.get("SCHEMA_NAME")
            name = r.get("TABLE_NAME") or r.get("name")
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}"
            jobs.append(
                (
                    "views",
                    "VIEW",
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Materialized views
    path = _find_catalog_file(in_root, "materialized_views")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("SCHEMA_NAME")
            name = r.get("MATERIALIZED_VIEW_NAME") or r.get("name")
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}"
            jobs.append(
                (
                    "materialized_views",
                    "VIEW",  # GET_DDL expects VIEW for mviews
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Tasks
    path = _find_catalog_file(in_root, "tasks")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("SCHEMA_NAME")
            name = r.get("TASK_NAME") or r.get("name")
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}"
            jobs.append(
                (
                    "tasks",
                    "TASK",
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Dynamic tables
    path = _find_catalog_file(in_root, "dynamic_tables")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("SCHEMA_NAME")
            name = r.get("DYNAMIC_TABLE_NAME") or r.get("name")
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}"
            jobs.append(
                (
                    "dynamic_tables",
                    "TABLE",  # GET_DDL expects TABLE for dynamic tables
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Functions
    path = _find_catalog_file(in_root, "functions")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("SCHEMA_NAME")
            name = r.get("FUNCTION_NAME") or r.get("name")
            sig = _extract_args_from_arguments_field(
                str(name) if name else "", r.get("arguments"), r.get("signature")
            )
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}" + (
                sig or ""
            )
            jobs.append(
                (
                    "functions",
                    "FUNCTION",
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Procedures
    path = _find_catalog_file(in_root, "procedures")
    if path:
        for r in _load_rows(path):
            dbn = r.get("DATABASE_NAME")
            schn = r.get("SCHEMA_NAME")
            name = r.get("PROCEDURE_NAME") or r.get("name")
            sig = _extract_args_from_arguments_field(
                str(name) if name else "", r.get("arguments"), r.get("signature")
            )
            if not (dbn and schn and name):
                continue
            fq = f"{_quote_ident(dbn)}.{_quote_ident(schn)}.{_quote_ident(name)}" + (
                sig or ""
            )
            jobs.append(
                (
                    "procedures",
                    "PROCEDURE",
                    str(dbn),
                    str(schn),
                    str(name),
                    fq,
                    r.get("ddl"),
                )
            )

    # Process jobs in parallel
    def worker(
        job: Tuple[str, str, str, str, str, str, Optional[str]],
    ) -> Tuple[int, int]:
        cat, obj_type, dbn, schn, name, fq, existing = job
        # Skip work if file already exists; idempotent export
        target_dir = sql_root / cat / _safe_filename(dbn) / _safe_filename(schn)
        target_file = target_dir / f"{_safe_filename(name)}.sql"
        if target_file.exists():
            return (0, 0)
        ddl = fetch_or_none(obj_type, fq, existing)
        if not ddl:
            return (0, 1)
        wrote = write(cat, dbn, schn, name, ddl)
        return (wrote, 0)

    if jobs:
        with ThreadPoolExecutor(max_workers=max(1, int(max_workers))) as ex:
            futures = [ex.submit(worker, j) for j in jobs]
            for fut in as_completed(futures):
                w, m = fut.result()
                counts["written"] += w
                counts["missing"] += m

    return counts
