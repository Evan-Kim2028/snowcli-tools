# SNOWCLI-TOOLS

SNOWCLI-TOOLS is an ergonomic enhancement on top of the official Snowflake CLI (`snow`).
This project leverages your existing `snow` CLI profiles to add powerful, concurrent data tooling:

- **Automated Data Catalogue**: Generate a comprehensive JSON/JSONL catalogue of your Snowflake objects.
- **Dependency Graph Generation**: Generate object dependencies to understand data lineage.
- **Parallel Query Execution**: Run multiple queries concurrently for faster bulk workloads.
 - **SQL Export from Catalog**: Generate a categorized SQL repo from your catalog JSON.

## Prerequisites

- Python 3.12+
- UV (recommended): https://docs.astral.sh/uv/
- The official [Snowflake CLI (`snow`)](https://docs.snowflake.com/en/user-guide/snowcli) (installed via UV below)

## Installation

Install from PyPI (recommended):

```bash
# Install the package
uv pip install snowcli-tools

# Check the CLI entry point
snowflake-cli --help

# Or run ad‑hoc without installing to your environment
uvx --from snowcli-tools snowflake-cli --version
```

PyPI project page: https://pypi.org/project/snowcli-tools/

```bash
# Clone the repository
git clone https://github.com/Evan-Kim2028/snowflake-cli-tools-py.git
cd snowflake-cli-tools-py

# Install project deps and the Snowflake CLI via UV
uv sync
uv add snowflake-cli
```


## Quick Start

```bash
# 1) Install deps + Snowflake CLI
uv sync
uv add snowflake-cli

# 2) Create or select a Snowflake CLI connection (one-time)
uv run snowflake-cli setup-connection

# 3) Smoke test
uv run snowflake-cli query "SELECT CURRENT_VERSION()"

# 4) Build a catalog (default output: ./data_catalogue)
uv run snowflake-cli catalog

# 5) Generate a dependency graph
# By default, outputs to ./dependencies (dependencies.json / dependencies.dot)
uv run snowflake-cli depgraph --account -f dot

# Or restrict to a database and emit JSON to the default directory
uv run snowflake-cli depgraph --database MY_DB -f json

# To choose a different directory or filename
uv run snowflake-cli depgraph --account -f json -o ./my_deps
uv run snowflake-cli depgraph --account -f json -o ./my_deps/graph.json
```

## Setup

This tool uses your `snow` CLI connection profiles.

Use the official `snow` CLI to create a profile with your preferred
authentication method. Two common examples:

Key‑pair (recommended for headless/automation):

```bash
snow connection add \
  --connection-name my-keypair \
  --account <account> \
  --user <user> \
  --authenticator SNOWFLAKE_JWT \
  --private-key /path/to/rsa_key.p8 \
  --warehouse <warehouse> \
  --database <database> \
  --schema <schema> \
  --role <role> \
  --default \
  --no-interactive
```

SSO via browser (Okta/External Browser):

```bash
snow connection add \
  --connection-name my-sso \
  --account <account> \
  --user <user> \
  --authenticator externalbrowser \
  --warehouse <warehouse> \
  --database <database> \
  --schema <schema> \
  --role <role> \
  --default
```

Profile selection precedence:

- CLI flag `--profile/-p`
- `SNOWFLAKE_PROFILE` env var
- Default connection in your `snow` config

Optional helper in this repo:

```bash
# Convenience only: creates a key‑pair profile via `snow connection add`
uv run snowflake-cli setup-connection
```

This helper is optional; you can always manage profiles directly with `snow`.

## Usage

All commands are run through the `snowflake-cli` entry point.

### Query Execution

Execute single queries with flexible output formats.

```bash
# Simple query with table output
uv run snowflake-cli query "SELECT * FROM my_table LIMIT 10"

# Execute and get JSON output
uv run snowflake-cli query "SELECT * FROM my_table LIMIT 10" --format json

# Preview a table's structure and content
uv run snowflake-cli preview my_table

# Execute a query from a .sql file
uv run snowflake-cli query "$(cat my_query.sql)"
```

### Data Cataloguing

Generate a data catalogue by introspecting database metadata (works with any Snowflake account). Outputs JSON by default; JSONL is available for ingestion-friendly workflows. DDL is optional and fetched concurrently when enabled. An incremental mode skips DDL re-fetch for unchanged objects between runs.

```bash
# Build a catalog for the current database (default output: ./data_catalogue)
uv run snowflake-cli catalog

# Build for a specific database
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_db

# Build for the entire account
uv run snowflake-cli catalog --account --output-dir ./data_catalogue_all

# Include DDL (concurrent fetches; opt-in)
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_ddled --include-ddl

# JSONL output
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_jsonl --format jsonl

# Incremental: skip DDL re-fetch for unchanged objects (writes catalog_state.json)
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_inc --include-ddl --incremental
```

Files created (per format):
- schemata.(json|jsonl)
- tables.(json|jsonl)
- columns.(json|jsonl)
- views.(json|jsonl)
- materialized_views.(json|jsonl)
- routines.(json|jsonl)
- functions.(json|jsonl)
- procedures.(json|jsonl)
- tasks.(json|jsonl)
- dynamic_tables.(json|jsonl)
- catalog_summary.json (counts)

### SQL Export (from existing catalog)

Generate a human‑readable SQL repository based on your catalog JSON/JSONL. Missing DDL will be fetched via GET_DDL in parallel.

```bash
# Two‑step workflow (recommended):
# 1) Build JSON catalog (fast, no DDL)
uv run snowflake-cli catalog -o ./data_catalogue_test_json --format json --no-include-ddl

# 2) Export SQL to a separate folder with 24 workers
uv run snowflake-cli export-sql -i ./data_catalogue_test_json -o ./data_catalogue_test_sql -w 24

# If your JSON already includes embedded DDL (--include-ddl), export runs mostly as file writes
uv run snowflake-cli export-sql -i ./data_catalogue_test_json -o ./data_catalogue_test_sql

Idempotence and state
- Re-running `catalog --incremental --include-ddl` reuses DDL for unchanged objects via `catalog_state.json` and prior JSON, minimizing GET_DDL calls.
- Re-running `export-sql` skips existing files by default; only new/missing objects are written.
```

Output layout (under the chosen output directory):
- tables/<DB>/<SCHEMA>/<OBJECT>.sql
- views/<DB>/<SCHEMA>/<OBJECT>.sql
- materialized_views/<DB>/<SCHEMA>/<OBJECT>.sql
- dynamic_tables/<DB>/<SCHEMA>/<OBJECT>.sql
- tasks/<DB>/<SCHEMA>/<OBJECT>.sql
- functions/<DB>/<SCHEMA>/<OBJECT>.sql
- procedures/<DB>/<SCHEMA>/<OBJECT>.sql

Notes and privileges:
- For best coverage of DDL, run with a role that has USAGE on the database/schema and sufficient object privileges.
- Materialized views and dynamic tables: GET_DDL expects types VIEW and TABLE respectively; MONITOR or OWNERSHIP may be required for DDL visibility.
- Functions/procedures: USAGE is required; OWNERSHIP may be needed for some definitions.
- Tune concurrency with `-w/--workers` to balance speed and Snowflake limits.

### Dependency Graph

Create a dependency graph of Snowflake objects using either
`SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` (preferred) or a fallback to
`INFORMATION_SCHEMA.VIEW_TABLE_USAGE`.

Examples:

```bash
# Account-wide (requires privileges), Graphviz DOT
uv run snowflake-cli depgraph --account -f dot

# Restrict to a database, JSON output
uv run snowflake-cli depgraph --database PIPELINE_V2_GROOT_DB -f json

# Save to a custom directory or file
uv run snowflake-cli depgraph --account -f json -o ./my_deps
uv run snowflake-cli depgraph --account -f dot -o ./my_deps/graph.dot
```

Notes:
- ACCOUNT_USAGE has latency and requires appropriate roles; if not accessible,
  the CLI falls back to view→table dependencies from INFORMATION_SCHEMA.
- Output formats: `json` (nodes/edges) and `dot` (render with Graphviz).
 - Default output directory is `./dependencies` when `-o/--output` is not provided.

### Parallel Queries

Execute multiple queries concurrently based on a template.

**Example 1: Templated Queries**
```bash
# Query multiple object types in parallel
uv run snowflake-cli parallel "type_a" "type_b" \
  --query-template "SELECT * FROM objects WHERE type = '{object}'" \
  --output-dir ./results
```

**Example 2: Executing from a File**

You can also execute a list of queries from a file using shell commands:
```bash
# queries.txt contains one query per line
# SELECT * FROM my_table;
# SELECT COUNT(*) FROM another_table;

cat queries.txt | xargs -I {} uv run snowflake-cli query "{}"
```

## CLI Commands

| Command            | Description                                              |
| ------------------ | -------------------------------------------------------- |
| `test`             | Test the current Snowflake CLI connection.               |
| `query`            | Execute a single SQL query (table/JSON/CSV output).      |
| `parallel`         | Execute multiple queries in parallel (spawns `snow`).    |
| `preview`          | Preview table contents.                                  |
| `catalog`          | Build a JSON/JSONL data catalog (use `--include-ddl` to add DDL). |
| `export-sql`       | Generate a categorized SQL repo from catalog JSON/JSONL. |
| `depgraph`         | Generate a dependency graph (DOT/JSON output).           |
| `config`           | Show the current tool configuration.                     |
| `setup-connection` | Helper to create a persistent `snow` CLI connection.     |
| `init-config`      | Create a local configuration file for this tool.         |

### Catalog design notes (portable by default)
- Uses SHOW commands where possible (schemas, materialized views, dynamic tables, tasks, functions, procedures) for broad visibility with minimal privileges.
- Complements SHOW with INFORMATION_SCHEMA (tables, columns, views) for standardized column-level details.
- Works with any Snowflake account because it only uses standard Snowflake metadata interfaces.
- Optional DDL capture uses GET_DDL per object and fetches concurrently for performance.

### Best practices
- Configure and test your Snowflake CLI connection first (key‑pair, Okta, OAuth are supported by `snow`).
- Run with a role that has USAGE on the target databases/schemas to maximize visibility.
- Prefer `--format jsonl` for ingestion and downstream processing; JSONL is line‑delimited and append‑friendly.
- When enabling `--include-ddl`, increase concurrency with `--max-ddl-concurrency` for large estates.
- Start with a database‑scoped run, then expand to `--account` if needed and permitted.

### Transparency and security
- This project never handles your secrets or opens browsers; it delegates all auth to your `snow` CLI.
- Use profiles appropriate for your environment (key‑pair for automation, SSO for interactive use).

## Development

```bash
# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/
```

## License

This project is licensed under the MIT License.
