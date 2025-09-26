# Repository Guidelines

## Architecture Overview
- Theme: a thin Snowflake tooling layer that now rides on top of the official
  `snowflake-labs` FastMCP service.
- Core modules in `src/snowcli_tools/` register catalog/lineage/dependency tools
  against the upstream `SnowflakeService`; we snapshot/restore Snowflake session
  state so overrides never leak into Snowflake’s built-in tools.
- Optional CLI bridge (`--enable-cli-bridge`) exposes legacy subprocess-based
  helpers; it is disabled by default to keep governance aligned with the
  FastMCP connector.
- Primary features still include:
  - Dependency graph: builds nodes/edges from ACCOUNT_USAGE or INFORMATION_SCHEMA.
  - Data catalog: exports database/schema/table metadata (JSON/JSONL), with optional DDL.

## Project Structure
- `src/snowcli_tools/`: core modules — `cli.py` (Click commands), `snow_cli.py` (runner), `dependency.py`, `catalog.py`, `config.py`, `parallel.py`.
- `src/snowflake_connector/`: auxiliary package namespace (internal).
- `src/snowcli_tools/session_utils.py`: shared helpers for session snapshot/restore.
- `tests/`: pytest tests for modules and CLI.
- `data_catalogue/`, `dependencies/`: default output folders.
- `examples/`: example configs/usage.

## Build, Test, Run
- Setup: `uv sync` (creates `.venv` and installs deps).
- Profile: default `readonly-keypair` for local testing (set via `SNOWFLAKE_PROFILE=readonly-keypair` or `--profile readonly-keypair`).
- Run CLI: `uv run snowflake-cli --help` (use `--profile readonly-keypair` if not set via env).
- Dependency graph: `uv run snowflake-cli --profile readonly-keypair dependency --format dot -o ./dependencies`.
- Catalog: `uv run snowflake-cli --profile readonly-keypair catalog -o ./data_catalogue -a --format jsonl`.
- Tests: `uv run pytest -q` (unit suite stays offline).
- Smoke test: `uv run python local_sf_test/test_smoke.py --transport stdio`
  (requires real Snowflake creds, prints latest rows from `object_parquet2`).
- Build dist: `uv build`.

## Coding Style & Naming
- Python 3.12+, 4-space indent, type hints required in new/changed code.
- Format: `black` and `isort`; Lint: `flake8`; Types: `mypy`.
- Run all: `uv run black . && uv run isort . && uv run flake8 && uv run mypy src`.
- Modules and functions use `snake_case`; Click subcommands map 1:1 to function names.
- MCP tools should remain stateless and rely on FastMCP context injection; never
  mutate shared session state outside the snapshot/restore helpers.

## Testing Guidelines
- Framework: `pytest` (`tests/test_*.py`).
- Unit-test pure logic; mock `snowcli_tools.snow_cli.SnowCLI` to avoid real calls.
- Prefer small fixtures and golden samples for parsed outputs.

## Commit & PR Guidelines
- Use imperative, scoped messages (e.g., "catalog: add jsonl writer").
- PRs must include: summary, rationale, usage examples (commands), and output samples (`.dot`, JSON snippet).
- Link issues and update `README.md`/`examples/` when behavior or flags change.

## Security & Configuration
- Auth/config comes from `snow` profiles; never commit credentials.
- Respect env overrides: `SNOWFLAKE_PROFILE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, `SNOWFLAKE_ROLE`.
- Optional: set `SNOWCLI_DEFAULT_PROFILE` to provide a fallback profile for
  local FastMCP development without hard-coding values in code.
- Quick start: `uv run snowflake-cli init_config ./examples/config.yaml` then run with `--config` or `--profile`.
- Default Snowflake CLI profile for this repo: `readonly-keypair`. Use this for all local Snowflake testing unless a different profile is explicitly provided. Equivalent env: `export SNOWFLAKE_PROFILE=readonly-keypair`.
