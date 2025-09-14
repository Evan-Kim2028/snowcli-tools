# PRD: Parallel Catalog, Data Samples, and SQL Export

## Overview
Enhance `snowflake-cli catalog` to be parallel by default, optionally persist small data samples per object, and provide a flag to export a human-readable SQL repository alongside the JSON catalog. The CLI remains a thin wrapper over the official `snow` CLI.

## Goals
- Faster catalog builds with safe default concurrency.
- Optional samples for tables/materialized views/dynamic tables and linkage from the JSON catalog.
- Optional SQL export: folder of `.sql` files generated from captured DDLs.

## Non‑Goals
- Managing secrets or auth beyond `snow` profiles.
- Full data exports or bulk copy features.

## Users & Use Cases
- Data platform engineers: quick estate inventory; inspect DDL and a small slice of data.
- Analytics engineers: browse catalog in Git (SQL files) and programmatic JSON for tooling.

## UX / Flags
- Parallelism (default on): `--catalog-concurrency <int>` (default 16; env `CATALOG_CONCURRENCY`).
- DDL capture: on by default (existing `--include-ddl/--no-include-ddl`, default on).
- Samples (single flag): `--samples <value>` controls enablement, row count, and format with one option.
  - Defaults (when omitted): enabled, 10 rows, JSON files.
  - Accepted values:
    - `off` or `0` → disable samples
    - `N` → enable with `N` rows, JSON format
    - `N,csv` or `N,jsonl` or `N,json` → set rows and format
- SQL export: `--export-sql/--no-export-sql` (default off). Writes `.sql` tree under `<output_dir>/sql/>`.

## Outputs
- JSON/JSONL files unchanged, augmented with new fields:
  - In `tables.*` (and mviews/dynamic tables) records: `sample` object `{ path, rows, format }` when present.
- New files:
  - `<output_dir>/samples/<DB>/<SCHEMA>/<OBJECT>.(csv|jsonl)`
  - `<output_dir>/samples_index.json` mapping FQN → sample metadata.
  - `<output_dir>/sql/<DB>/<SCHEMA>/<OBJECT>.sql` (and signatures for routines).

## Success Metrics
- 3–5x speedup on medium estates (10–50 schemas) vs. current.
- Optional features do not regress base performance when disabled.
- Deterministic, restartable outputs; paths stable across runs.

## Acceptance Criteria
- Running `catalog` with defaults finishes successfully and is parallelized.
- With defaults, samples (10 rows, JSON) are created and linked in JSON.
- `--samples off` disables sampling.
- `--export-sql` produces `.sql` files using captured DDL, with clear warnings if missing.
- Backward compatibility: existing JSON consumers continue to work.

## Risks / Mitigations
- Snowflake concurrency/limits: cap concurrency; allow override.
- Large estates: bounded worker pools; streaming JSONL support retained.
- Identifier quoting: use existing `_quote_ident` helper.

## Example Commands
- Parallel default build (samples on, 10 rows JSON): `uv run snowflake-cli catalog -o ./data_catalogue`
- Change sampling to 5 rows: `uv run snowflake-cli catalog -o ./data_catalogue --samples 5`
- Switch sampling to CSV, 10 rows: `uv run snowflake-cli catalog -o ./data_catalogue --samples 10,csv`
- Disable samples: `uv run snowflake-cli catalog -o ./data_catalogue --samples off`
- Also export SQL: `uv run snowflake-cli catalog -o ./data_catalogue --export-sql`
- Tune parallelism: `uv run snowflake-cli catalog -o ./data_catalogue --catalog-concurrency 24`
