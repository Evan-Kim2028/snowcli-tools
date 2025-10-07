# Repository Guidelines

## Architecture Overview
- Theme: Pure MCP (Model Context Protocol) server for Snowflake data operations.
- Core modules in `src/nanuk_mcp/` provide catalog/lineage/dependency tools
  through the MCP protocol; we snapshot/restore Snowflake session
  state so overrides never leak into Snowflake's built-in tools.
- **v2.0.0+**: CLI has been completely removed. This is an MCP-only architecture.
- Primary features:
  - Dependency graph: builds nodes/edges from ACCOUNT_USAGE or INFORMATION_SCHEMA.
  - Data catalog: exports database/schema/table metadata (JSON/JSONL), with optional DDL.
  - Lineage analysis: track table dependencies and data flow.

## Project Structure
- `src/nanuk_mcp/`: core modules — `mcp_server.py` (MCP server), `snow_cli.py` (Snowflake wrapper), `dependency.py`, `catalog.py`, `config.py`, `parallel.py`.
- `src/snowflake_connector/`: compatibility shim (deprecated, for backward compatibility only).
- `src/nanuk_mcp/lineage/`: lineage analysis modules.
- `tests/`: pytest tests for all modules.
- `data_catalogue/`, `dependencies/`: default output folders.
- `examples/`: example configs/usage.

## Build, Test, Run
- Setup: `uv sync` (creates `.venv` and installs deps).
- Profile: default `readonly-keypair` for local testing (set via `SNOWFLAKE_PROFILE=readonly-keypair`).
- Run MCP Server: `uv run nanuk-mcp` (uses profile from `SNOWFLAKE_PROFILE` env var).
- Tests: `uv run pytest -q` (unit suite stays offline).
- Build dist: `uv build`.

## Using MCP Tools
All functionality is exposed through MCP tools. Use with an MCP-compatible client (Claude Code, etc.):
- Dependency graph: `build_dependency_graph` tool
- Catalog: `build_catalog` tool
- Lineage: `query_lineage` tool
- Query execution: `execute_query` tool

## Coding Style & Naming
- Python 3.12+, 4-space indent, type hints required in new/changed code.
- Format: `black` and `isort`; Lint: `flake8`; Types: `mypy`.
- Run all: `uv run black . && uv run isort . && uv run flake8 && uv run mypy src`.
- Modules and functions use `snake_case`; Click subcommands map 1:1 to function names.
- MCP tools should remain stateless and rely on FastMCP context injection; never
  mutate shared session state outside the snapshot/restore helpers.

## Testing Guidelines
- Framework: `pytest` (`tests/test_*.py`).
- Unit-test pure logic; mock `nanuk_mcp.snow_cli.SnowCLI` to avoid real calls.
- Prefer small fixtures and golden samples for parsed outputs.

## Commit & PR Guidelines
- Use imperative, scoped messages (e.g., "catalog: add jsonl writer").
- PRs must include: summary, rationale, usage examples (commands), and output samples (`.dot`, JSON snippet).
- Link issues and update `README.md`/`examples/` when behavior or flags change.

## Security & Configuration
- Auth/config comes from `snow` profiles (Snowflake CLI); never commit credentials.
- Respect env overrides: `SNOWFLAKE_PROFILE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_ROLE`.
- MCP server configuration: Set `SNOWFLAKE_PROFILE` environment variable in your MCP client config.
- Default Snowflake CLI profile for this repo: `readonly-keypair`. Use this for all local Snowflake testing unless a different profile is explicitly provided. Equivalent env: `export SNOWFLAKE_PROFILE=readonly-keypair`.
