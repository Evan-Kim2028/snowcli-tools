# SNOWCLI-TOOLS

SNOWCLI-TOOLS is an ergonomic enhancement on top of the official Snowflake CLI (`snow`).
This project leverages your existing `snow` CLI profiles to add powerful, concurrent data tooling:

- **Automated Data Catalogue**: Generate a comprehensive JSON/JSONL catalogue of your Snowflake objects.
- **Dependency Graph Generation**: Generate object dependencies to understand data lineage.
- **Parallel Query Execution**: Run multiple queries concurrently for faster bulk workloads.

## Prerequisites

- Python 3.12+
- UV (recommended): https://docs.astral.sh/uv/
- The official [Snowflake CLI (`snow`)](https://docs.snowflake.com/en/user-guide/snowcli) (installed via UV below)

## Installation

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

# 5) Generate a dependency graph (account-wide, DOT)
uv run snowflake-cli depgraph --account -f dot -o deps.dot

# Or restrict to a database and emit JSON
uv run snowflake-cli depgraph --database MY_DB -f json -o deps.json
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

Generate a data catalogue by introspecting database metadata (works with any Snowflake account). Outputs JSON by default; JSONL is available for ingestion-friendly workflows. DDL is optional and fetched concurrently when enabled.

```bash
# Build a catalog for the current database (default output: ./data_catalogue)
uv run snowflake-cli catalog

# Build for a specific database
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_db

# Build for the entire account
uv run snowflake-cli catalog --account --output-dir ./data_catalogue_all

# Include DDL (concurrent by default; opt-in)
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_ddled --include-ddl

# JSONL output
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue_jsonl --format jsonl
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

### Dependency Graph

Create a dependency graph of Snowflake objects using either
`SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` (preferred) or a fallback to
`INFORMATION_SCHEMA.VIEW_TABLE_USAGE`.

Examples:

```bash
# Account-wide (requires privileges), Graphviz DOT
uv run snowflake-cli depgraph --account -f dot -o deps.dot

# Restrict to a database, JSON output
uv run snowflake-cli depgraph --database PIPELINE_V2_GROOT_DB -f json -o deps.json
```

Notes:
- ACCOUNT_USAGE has latency and requires appropriate roles; if not accessible,
  the CLI falls back to view→table dependencies from INFORMATION_SCHEMA.
- Output formats: `json` (nodes/edges) and `dot` (render with Graphviz).

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
