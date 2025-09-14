# Technical Spec: Parallel Catalog, Samples, and SQL Export

## Current State
- `build_catalog()` iterates databases → schemas sequentially; only DDL fetch is parallelized.
- Outputs: JSON/JSONL entity files and `catalog_summary.json`.

## Proposed Changes
### Parallel Catalog (default on)
- Add worker pool for schema-level tasks.
- New arg: `catalog_concurrency: int = 16` (CLI `--catalog-concurrency`).
- Task granularity: per (DB, SCHEMA). Each task gathers: schemata, tables, columns, views, mviews, routines, tasks, dynamic tables, functions, procedures.
- Merge results thread-safely into shared lists (use local accumulators per task, then reduce in main thread).

### Data Samples
- Single option: `--samples <value>` bundles enablement, row count, and format.
  - Defaults when omitted: enabled, 10 rows, JSON format.
  - Accepted values: `off|0` (disable), `N` (JSON), `N,csv`, `N,jsonl`, `N,json`.
- For each TABLE, MATERIALIZED VIEW, DYNAMIC TABLE: run `SELECT * FROM <FQN> LIMIT <n>`.
- Write to `<output_dir>/samples/<DB>/<SCHEMA>/<OBJECT>.(json|jsonl|csv)`.
- Update corresponding records with a `sample` object: `{ "path": "samples/DB/SCHEMA/OBJECT.json", "rows": n, "format": "json" }`.
- Create `<output_dir>/samples_index.json`: `{ "<DB>.<SCHEMA>.<OBJECT>": { path, rows, format } }`.

### SQL Export
- New CLI flag: `--export-sql/--no-export-sql` (default off).
- Output tree: `<output_dir>/sql/<DB>/<SCHEMA>/<OBJECT>.sql`.
- Source text precedence: (1) captured `ddl` field from catalog; (2) on-demand `GET_DDL('<TYPE>', '<FQN>')` if not captured; (3) warn if unavailable.
- Naming for routines: include signature when known, normalize to filesystem-safe names (e.g., `FUNC__NUMBER_VARCHAR.sql`).

## API / CLI Surface
- `catalog(...)` in `cli.py`
  - Add options: `--catalog-concurrency`, `--samples`, `--export-sql`.
- `build_catalog(output_dir, *, database=None, account_scope=False, output_format='json', include_ddl=True, max_ddl_concurrency=8, catalog_concurrency=16, samples_spec='10,json', export_sql=False)` returns totals.
  - `samples_spec` grammar: `off|0|<N>|<N>,(json|jsonl|csv)`.

## Defaults
- Parallel catalog: enabled.
- DDL capture: enabled.
- Sampling: enabled, 10 rows per object, JSON format.

## Implementation Details
- Concurrency:
  - Build list of `(db, schema)` pairs, then `ThreadPoolExecutor(max_workers=catalog_concurrency)`.
  - Each worker uses a fresh `SnowCLI()`; Snowflake CLI calls are I/O-bound; threads are adequate.
  - Respect existing context and quoting via `_quote_ident`.
- Sampling:
  - CSV path: write DictWriter from parsed rows when `output_format='json'` isn’t available; otherwise use `--format csv` and write raw.
  - JSONL path: always write via line-by-line dump.
  - Handle empty tables gracefully; skip file creation if zero rows, but keep metadata with `rows: 0`.
- SQL export:
  - After catalog aggregation (and optional DDL fetch), walk records and materialize `.sql` files.
  - Ensure deterministic ordering; idempotent overwrites.

## Data Model Additions
- tables/views/mviews/dynamic_tables records may include:
  ```json
  "sample": { "path": "samples/DB/SCHEMA/OBJECT.csv", "rows": 50, "format": "csv" }
  ```
- `samples_index.json`: flat map for quick lookup.

## File Layout
- `<output_dir>/samples/<DB>/<SCHEMA>/<OBJECT>.(csv|jsonl)`
- `<output_dir>/sql/<DB>/<SCHEMA>/<OBJECT>.sql`
- Paths use original case; filenames sanitized to remove path-hostile chars.

## Performance & Limits
- Default `catalog_concurrency=16` (tunable). Provide env `CATALOG_CONCURRENCY`.
- Add small random jitter between tasks to reduce burstiness.
- Timeouts: reuse `SnowCLI.run_query(..., timeout=...)` for long DDL and big SHOWs.

## Testing Plan
- Unit: sampling path builder, filename sanitizer, JSON linking, SQL export writer.
- Integration (mock `SnowCLI`): simulate estates with multiple schemas; assert parallel invocation counts and outputs.
- CLI: Click runner tests for flags and combinations.

## Backward Compatibility
- JSON files remain valid; new `sample` field is additive.
- Flags default off for samples and SQL export; parallelism default on.

## Rollout
- Phase 1: implement parallel core without samples/export; release minor.
- Phase 2: add samples and SQL export; update README and examples.
