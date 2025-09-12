# SNOWCLI-TOOLS v0.1.0 (Initial public positioning)

Highlights
- Bring-Your-Own Auth: uses official `snow` CLI profiles (no secrets here).
- Parallel queries: run multiple `snow sql` invocations concurrently.
- Data catalog: generate JSON/JSONL metadata from SHOW/INFORMATION_SCHEMA.
- Friendly CLI: standardized output (CSV/JSON), preview helper, and config utilities.

Changes
- Docs: README reframed to emphasize enhancement over Snowflake CLI.
- Naming: project name clarified as SNOWCLI-TOOLS in docs and banners.
- CLI: `setup-connection` labeled as optional convenience around `snow connection add`.
- Config: clarified that `config.py` holds only profile/context, not auth.
- Tooling: added `.flake8` (exclude venv, max line length 120, ignore E203/W503) and applied formatting.

Usage
- Create a profile with `snow connection add` (key‑pair, SSO, or OAuth) and run:
  - `uv run snowflake-cli -p <profile> query "SELECT 1"`
  - `uv run snowflake-cli catalog`
  - `uv run snowflake-cli parallel <objs> -t "...{object}..."`

Notes
- Tests: `pytest` passes locally.
- Security: all authentication handled by `snow`; this repo does not handle keys.

---

# SNOWCLI-TOOLS v1.0.0 (Dependency Graph feature)

Highlights
- New CLI command: `depgraph` to generate a Snowflake object dependency graph.
- Preferred source: `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` for broad coverage.
- Fallback: `INFORMATION_SCHEMA.VIEW_TABLE_USAGE` when ACCOUNT_USAGE is not available.
- Output formats: `json` (nodes/edges) and `dot` (Graphviz DOT).
- Example script added: `examples/run_depgraph.py`.

Usage
```bash
# Account-wide (requires appropriate role), DOT output
uv run snowflake-cli depgraph --account -f dot -o deps.dot

# Restrict to a database, JSON output
uv run snowflake-cli depgraph --database PIPELINE_V2_GROOT_DB -f json -o deps.json
```

Notes
- ACCOUNT_USAGE has ingestion latency and privilege requirements; when not accessible,
  the tool falls back to view→table dependencies from INFORMATION_SCHEMA.
- This release maintains the BYO-auth model (profiles via `snow`).
-
# SNOWCLI-TOOLS v1.0.2 (Remove polars to avoid native builds)

- Removed `polars` from base dependencies to avoid native builds on PyPy/macOS.
- Refactored parallel query path to operate on CSV/JSON rows from Snowflake CLI.
- Default `parallel` output switched to CSV; Parquet export now optional (warns if `polars` missing).
- Keeps `snowflake-cli` as a core dependency, no CPython requirement.

# SNOWCLI-TOOLS v1.0.1 (Docs emphasis on Catalog + DepGraph)

Changes
- README: stronger emphasis on Data Catalog and Dependency Graph as primary features.
- Quick Start: added dependency graph commands (DOT/JSON examples).
- CLI: updated version banner to 1.0.1 and clarified primary features in help text.
