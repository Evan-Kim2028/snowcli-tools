# SNOWCLI-TOOLS v1.4.3 (FastMCP hardening)

Highlights
- **Session-safe overrides**: MCP tools now snapshot and restore the shared
  Snowflake session (role, warehouse, database, schema) so overrides stay scoped
  to each call and never leak into Snowflake’s official toolset.
- **Optional CLI bridge**: `snowflake-cli mcp --enable-cli-bridge` exposes the
  legacy `run_cli_query` tool for transitional workflows. By default the server
  uses the in-process connector to inherit upstream governance.
- **Local smoke harness**: `local_sf_test/test_smoke.py` runs
  `SELECT * FROM object_parquet2 ORDER BY timestamp_ms DESC LIMIT 2` and prints
  the most recent rows for quick visual verification after authentication.

Changes
- Argument parsing now treats missing defaults as `None`, preventing help-text
  strings from becoming accidental context overrides.
- Shared-session utilities live in `src/snowcli_tools/session_utils.py` so
  future pooling or metrics can build on a single helper module.
- Documentation, changelog, and version metadata bumped to **v1.4.3** and
  updated with the new flag, session model, and smoke-test instructions.

Usage
```bash
# Start FastMCP (stdio) with connector-backed tools
uv run snowflake-cli mcp

# Include the legacy CLI bridge (optional)
uv run snowflake-cli mcp --enable-cli-bridge

# Run the smoke test against your profile
uv run python local_sf_test/test_smoke.py --transport stdio
```

---

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
# SNOWCLI-TOOLS v0.1.0 (Initial public positioning)

# SNOWCLI-TOOLS v1.1.0 (Default deps dir + query fix)

- Default output directory for `depgraph` is now `./dependencies` when `-o/--output` is omitted. A default filename is chosen based on format.
- Fix ACCOUNT_USAGE query to use correct column names:
  - Use REFERENCING_DATABASE/REFERENCING_SCHEMA (not REFERENCING_OBJECT_*)
  - Use REFERENCED_DATABASE/REFERENCED_SCHEMA
- Map relationship using RELATIONSHIP with fallback to DEPENDENCY_TYPE.
- depgraph: accept a directory for -o/--output and write default filename
  (dependencies.json or dependencies.dot) into the directory.

# SNOWCLI-TOOLS v1.3.1 (MCP Server Integration)

🚀 **Major Release**: Full Model Context Protocol (MCP) server integration for AI assistants!

## Highlights
- **MCP Server**: New `snowflake-cli mcp` command runs a full-featured MCP server
- **AI Assistant Integration**: Compatible with VS Code, Cursor, Claude Code, and other MCP clients
- **7 MCP Tools**: execute_query, preview_table, build_catalog, query_lineage, build_dependency_graph, test_connection, get_catalog_summary
- **Optional Installation**: Use `pip install snowcli-tools[mcp]` for MCP dependencies
- **Complete Documentation**: New `/docs/mcp/` directory with architecture guides and examples
- **Real Sample Dataset**: DeFi trading pipeline examples with production DDL

## New MCP Tools
```bash
# Run MCP server (stdio transport with JSON-RPC 2.0)
uv run snowflake-cli mcp

# Install with MCP support
pip install snowcli-tools[mcp]
```

## Sample Dataset
- **dex_trades_stable**: Real DeFi trading pipeline (224M+ records)
- **Complete DDL**: Production table definitions with clustering and tags
- **Setup Script**: `/examples/sample_data/setup_sample_data.py` for easy installation
- **Documentation**: All examples now use real DeFi scenarios instead of generic data

## Technical Architecture
- **Protocol**: stdio transport with JSON-RPC 2.0 for AI assistant communication
- **Integration**: Works with existing SnowCLI and LineageQueryService infrastructure
- **Async**: Fully async MCP server implementation using `mcp.server.stdio`
- **Security**: Maintains BYO-auth model through official `snow` CLI profiles

## Repository Improvements
- **Fixed**: Moved `mcp_config.json` to `/examples/` as template
- **Fixed**: Added `lineage/` folder to `.gitignore` (generated outputs)
- **Added**: Comprehensive `CHANGELOG.md` following Keep a Changelog format
- **Enhanced**: All documentation updated with ASCII diagrams for GitHub compatibility

## Usage Examples
```json
// MCP Client Configuration (VS Code, Cursor, etc.)
{
  "mcpServers": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowcli-tools/project"
    }
  }
}
```

## Notes
- MCP server provides all existing snowcli-tools functionality through AI assistant integration
- Maintains full backward compatibility with CLI usage
- Real production DeFi dataset replaces generic examples throughout documentation
- Complete setup automation for sample data installation

---

# SNOWCLI-TOOLS v1.3.0 (Lineage search refinements)

Highlights
- Lineage CLI now supports partial name lookup with interactive disambiguation.
- HTML/JSON exports honor custom output paths and task keys resolve automatically.
- Documentation + examples cover the lineage workflow end-to-end.

Notes
- Run `snowflake-cli lineage rebuild` after refreshing your catalog to update the cache.
- Use partial names for quick lookups; the CLI will prompt when multiple candidates exist.

# SNOWCLI-TOOLS v1.2.0 (Incremental catalog + SQL export)

Highlights
- New standalone command: `export-sql` generates a categorized SQL repository from an existing catalog (JSON/JSONL).
- Parallel SQL export with `-w/--workers` and idempotent writes (skips existing files).
- Incremental catalog mode (`--incremental`):
  - Writes `catalog_state.json` and reuses embedded DDL for unchanged objects.
  - Skips GET_DDL fetch for unchanged objects; still writes full JSON outputs each run.
- DDL mapping improvements:
  - Materialized views: GET_DDL('VIEW', ...)
  - Dynamic tables: GET_DDL('TABLE', ...)
- Docs refreshed: README and PRD updated with incremental mode and SQL export usage; removed sampling from spec.

Usage
```bash
# Build catalog with embedded DDL and incremental state
uv run snowflake-cli catalog -o ./data_catalogue_inc --include-ddl --incremental

# Export SQL from catalog JSON (24 workers)
uv run snowflake-cli export-sql -i ./data_catalogue_inc -w 24

# JSON-only then export
uv run snowflake-cli catalog -o ./data_catalogue_json --no-include-ddl
uv run snowflake-cli export-sql -i ./data_catalogue_json -o ./data_catalogue_sql -w 24
```

Notes
- Some object DDL (e.g., tasks, procedures, secure objects) may require elevated privileges (MONITOR/OWNERSHIP) to retrieve.
- Re-running `export-sql` will skip existing files by default.
