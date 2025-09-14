# PRD: Parallel Catalog, Incremental Mode, and SQL Export

## Overview
Enhance `snowflake-cli catalog` to be parallel by default, add an incremental refresh mode, and provide both an inline flag and a standalone command to export a human-readable SQL repository alongside the JSON catalog. The CLI remains a thin wrapper over the official `snow` CLI.

## Goals
- Faster catalog builds with safe default concurrency.
- Optional SQL export: folder of `.sql` files generated from captured DDLs.

## Non‑Goals
- Managing secrets or auth beyond `snow` profiles.
- Full data exports or bulk copy features.

## Users & Use Cases
- Data platform engineers: quick estate inventory; inspect DDL.
- Analytics engineers: browse catalog in Git (SQL files) and programmatic JSON for tooling.

## UX / Flags
- Parallelism (default on): `--catalog-concurrency <int>` (default 16; env `CATALOG_CONCURRENCY`).
- Incremental refresh: `--incremental` (default off). Uses LAST_ALTERED/CREATED timestamps to skip unchanged objects and reduce DDL fetches.
- DDL capture: on by default (existing `--include-ddl/--no-include-ddl`, default on). When `--incremental` is set, DDL fetch is skipped for unchanged objects.
- SQL export: `--export-sql/--no-export-sql` (default off). Writes `.sql` tree under `<output_dir>/sql/>`.
- Standalone SQL export command: `export-sql -i <catalog_dir> [-o <out_dir>] [-w <workers>]` to generate a categorized SQL tree directly from JSON/JSONL.

## Outputs
- New files:
  - `<output_dir>/sql/<DB>/<SCHEMA>/<OBJECT>.sql` (and signatures for routines).
  - `<output_dir>/catalog_state.json` (when `--incremental` is enabled) stores per-object change state (normalized timestamps and optional DDL hash) keyed by object identity.

## Success Metrics
- 3–5x speedup on medium estates (10–50 schemas) vs. current.
- Optional features do not regress base performance when disabled.
- Deterministic, restartable outputs; paths stable across runs.
- Incremental mode reduces DDL fetches by ≥80% on subsequent runs with low change rates.

## Acceptance Criteria
- Running `catalog` with defaults finishes successfully and is parallelized.
- `--export-sql` produces `.sql` files using captured DDL, with clear warnings if missing.
- Backward compatibility: existing JSON consumers continue to work.
- With `--incremental`, unchanged objects are skipped for DDL re-fetch; JSON entity files remain complete and deterministic.

## Incremental Design

### Object Identity
- Key format: `<TYPE>|<DB>|<SCHEMA>|<NAME>` (uppercase, unquoted). For functions/procedures, include a normalized signature, e.g. `FUNCTION|DB|SCHEMA|NAME(NUMBER,VARCHAR)`.

### Change Detection Sources
- Tables/Views: INFORMATION_SCHEMA.TABLES/VIEWs → `LAST_ALTERED`, `CREATED`.
- Columns: driven by table changes; regenerate columns for changed tables.
- Materialized Views: `SHOW MATERIALIZED VIEWS` (normalize last modified to `last_altered`).
- Dynamic Tables: `SHOW DYNAMIC TABLES` (normalize to `last_altered`).
- Tasks: `SHOW TASKS` (normalize to `last_altered`).
- Functions/Procedures: `SHOW USER FUNCTIONS` / `SHOW PROCEDURES` (normalize to `last_altered` when present; otherwise treat as changed conservatively).

### State File
- Path: `<output_dir>/catalog_state.json`.
- Structure:
  - `version`: integer, reserved for schema evolution.
  - `generated_at`: ISO-8601 timestamp.
  - `objects`: map of identity key → `{ last_altered: str, created?: str, ddl_hash?: str }`.
- `ddl_hash` is computed over normalized DDL (e.g., sha256) when DDL capture is enabled; used to detect drift beyond timestamps.

### Algorithm (high level)
1) Load previous state when `--incremental` set; else start with empty state.
2) Build current metadata lists (parallel) using SHOW/INFORMATION_SCHEMA.
3) For each object, normalize identity and timestamps, then compare with state:
   - Not in state or newer `last_altered` → mark as changed.
   - Same timestamps (and optional `ddl_hash`) → mark as unchanged.
4) Write JSON entity files from current metadata (complete set).
5) If DDL capture enabled: enqueue GET_DDL jobs only for changed objects (and any without existing DDL in prior JSON). Fetch concurrently with `--max-ddl-concurrency`.
6) Update `catalog_state.json` with new timestamps and `ddl_hash` for objects whose DDL was captured.

### Deletions & Pruning
- JSON outputs reflect current metadata; removed objects naturally disappear.
- Optional future flag `--prune-sql` would delete SQL files for objects missing from the latest catalog.

### Error Handling & Fallbacks
- Missing timestamps → treat as changed.
- State file unreadable → ignore and run as non-incremental for this execution; rewrite fresh state after.
- Permissions errors on GET_DDL → skip and continue; count surfaced in summary.

## Risks / Mitigations
- Snowflake concurrency/limits: cap concurrency; allow override.
- Large estates: bounded worker pools; streaming JSONL support retained.
- Identifier quoting: use existing `_quote_ident` helper.

## Example Commands
- Parallel default build: `uv run snowflake-cli catalog -o ./data_catalogue`
- Also export SQL: `uv run snowflake-cli catalog -o ./data_catalogue --export-sql`
- Tune parallelism: `uv run snowflake-cli catalog -o ./data_catalogue --catalog-concurrency 24`
- Incremental refresh (skip unchanged DDL): `uv run snowflake-cli catalog -o ./data_catalogue --incremental`
- Standalone SQL export from existing JSON: `uv run snowflake-cli export-sql -i ./data_catalogue -w 24`
