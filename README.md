# Snowflake CLI Tools

An ergonomic Python wrapper for the official Snowflake CLI (`snow`), providing parallel query execution, data cataloging, and an improved user experience.

## Core Concept

This tool is a wrapper around the official `snow` CLI. It leverages your existing `snow` connection profiles to execute commands, offering several key advantages over using the `snow` CLI directly:

-   **Parallel Query Execution**: The `parallel` command uses a thread pool to run multiple `snow sql` processes concurrently. This significantly speeds up bulk data retrieval tasks that would otherwise run sequentially.
-   **Automated Data Cataloging**: The `catalog` command introspects your database's `INFORMATION_SCHEMA` to generate a comprehensive metadata catalog in JSON format—a feature not available in the standard CLI.
-   **Simplified User Experience**: Provides an improved interface for common operations, such as the `preview` command for quickly inspecting tables and the `setup-connection` helper for interactive configuration.
-   **Standardized Output**: Ensures consistent and machine-readable output formats (JSON, CSV), simplifying integration with other scripts and tools.

In short, this tool enhances the official Snowflake CLI with powerful features for automation, performance, and ease of use.

## Prerequisites

-   Python 3.12+
-   UV (recommended): https://docs.astral.sh/uv/
-   The official [Snowflake CLI (`snow`)](https://docs.snowflake.com/en/user-guide/snowcli) (installed via UV below)

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
```

## Setup

This tool uses the connection profiles from your `snow` CLI configuration.

**1. Configure the Snowflake CLI**

If you have not already configured the `snow` CLI, please follow the official Snowflake documentation to set up a connection.

**2. Use the Setup Helper (Optional)**

This tool includes a helper command to create or update a `snow` CLI connection profile, which is useful for key-pair authentication.

```bash
# Run the interactive setup helper
uv run snowflake-cli setup-connection
```

This will guide you through creating a named connection that this tool and the `snow` CLI can use.

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
```

### Parallel Queries

Execute multiple queries concurrently based on a template.

```bash
# Query multiple object types in parallel
uv run snowflake-cli parallel "type_a" "type_b" \
  --query-template "SELECT * FROM objects WHERE type = '{object}'" \
  --output-dir ./results
```

### Data Cataloging

Generate a data catalog by introspecting database metadata (works with any Snowflake account). Outputs JSON by default; JSONL is available for ingestion-friendly workflows. DDL is optional and fetched concurrently when enabled.

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

## CLI Commands

| Command            | Description                                              |
| ------------------ | -------------------------------------------------------- |
| `test`             | Test the current Snowflake CLI connection.               |
| `query`            | Execute a single SQL query (table/JSON/CSV output).      |
| `parallel`         | Execute multiple queries in parallel (spawns `snow`).    |
| `preview`          | Preview table contents.                                  |
| `catalog`          | Build a JSON/JSONL data catalog (use `--include-ddl` to add DDL). |
| `config`           | Show the current tool configuration.                     |
| `setup-connection` | Helper to create a persistent `snow` CLI connection.     |
| `init-config`      | Create a local configuration file for this tool.         |

### Catalog design notes (portable by default)
- Uses SHOW commands where possible (schemas, materialized views, dynamic tables, tasks, functions, procedures) for broad visibility with minimal privileges.
- Complements SHOW with INFORMATION_SCHEMA (tables, columns, views) for standardized column-level details.
- Works with any Snowflake account because it only uses standard Snowflake metadata interfaces.
- Optional DDL capture uses GET_DDL per object and fetches concurrently for performance.

### Best practices
- Configure and test your Snowflake CLI connection first (key‑pair, OAuth, Okta are all supported by `snow`).
- Run with a role that has USAGE on the target databases/schemas to maximize visibility.
- Prefer `--format jsonl` for ingestion and downstream processing; JSONL is line‑delimited and append‑friendly.
- When enabling `--include-ddl`, increase concurrency with `--max-ddl-concurrency` for large estates.
- Start with a database‑scoped run, then expand to `--account` if needed and permitted.

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
