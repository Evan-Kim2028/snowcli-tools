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
