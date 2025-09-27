# SNOWCLI-TOOLS

SNOWCLI-TOOLS is an ergonomic enhancement on top of the official Snowflake CLI (`snow`).
This project leverages your existing `snow` CLI profiles to add powerful, concurrent data tooling:

- **Automated Data Catalogue**: Generate a comprehensive JSON/JSONL catalogue of your Snowflake objects.
- **Dependency Graph Generation**: Generate object dependencies to understand data lineage.
- **Parallel Query Execution**: Run multiple queries concurrently for faster bulk workloads.
- **SQL Export from Catalog**: Generate a categorized SQL repo from your catalog JSON.

## 🆕 Advanced Lineage Features (v1.3.2)

- **Column-Level Lineage**: Track data flow at the column granularity through transformations
- **Transformation Tracking**: Capture and analyze data transformations with categorization
- **Cross-Database Lineage**: Build unified lineage graphs across multiple Snowflake databases
- **External Data Sources**: Map S3/Azure/GCS sources and track external dependencies
- **Impact Analysis**: Analyze the potential impact of changes before making them
- **Time-Travel Lineage**: Track lineage evolution over time with snapshots and comparisons

## Prerequisites

- Python 3.12+
- UV (recommended): https://docs.astral.sh/uv/
- The official [Snowflake CLI (`snow`)](https://docs.snowflake.com/en/user-guide/snowcli) (installed via UV below)

## Installation

Install from PyPI (recommended):

### Base Installation (Core CLI)
```bash
# Install the core package without MCP
uv pip install snowcli-tools

# Check the CLI entry point
snowflake-cli --help
```

### Full Installation (With MCP Server for AI Assistants)
```bash
# Install with MCP support for AI integrations
uv pip install snowcli-tools[mcp]
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/Evan-Kim2028/snowflake-cli-tools-py.git
cd snowflake-cli-tools-py

# Install project deps and the Snowflake CLI via UV
uv sync
uv add snowflake-cli

# Install MCP support for development
uv add --extra mcp
```

PyPI project page: https://pypi.org/project/snowcli-tools/


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

## Profile Configuration

### Profile Selection Precedence

Snowcli-tools uses the following precedence for profile selection:

1. CLI flag `--profile/-p` (highest priority)
2. `SNOWFLAKE_PROFILE` environment variable
3. Default connection in your `snow` config
4. First available profile (with validation)

### Profile Validation (Enhanced v1.4.4+)

Starting with v1.4.4, snowcli-tools includes robust profile validation that transforms the user experience:

- ✅ **Validates profiles at startup** - Catches configuration issues immediately
- ✅ **Provides clear error messages** - No more confusing timeout errors
- ✅ **Suggests specific fixes** - Actionable guidance for resolving issues
- ✅ **Real-time diagnostics** - New MCP tools for ongoing health monitoring
- ✅ **Structured error responses** - MCP-compliant error format with specific codes

#### Before vs After (v1.4.4+)

**Before v1.4.4 (Confusing Experience):**
```bash
$ snowflake-cli mcp
Starting MCP server...
# Server appears to start successfully, but first tool call fails with:
Connection timeout error after 30 seconds
```

**After v1.4.4 (Clear Feedback):**
```bash
$ snowflake-cli mcp
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: evan-oauth, mystenlabs-keypair
To fix this issue:
1. Set SNOWFLAKE_PROFILE environment variable to one of the available profiles
2. Or pass --profile <profile_name> when starting the server
3. Or run 'snow connection add' to create a new profile
```

#### New Diagnostic Capabilities

**Health monitoring through AI assistants:**
```
AI: "Check the MCP server health"
AI: "Validate my Snowflake profile configuration"
AI: "Are all MCP resources available?"
```

**Structured error responses with context:**
```json
{
  "error": {
    "code": -32004,
    "message": "Snowflake profile validation failed",
    "data": {
      "profile_name": "default",
      "available_profiles": ["evan-oauth", "mystenlabs-keypair"],
      "suggestion": "Set SNOWFLAKE_PROFILE environment variable"
    }
  }
}
```

### Profile Management Commands

Check your current profile configuration:
```bash
# List all available profiles
snow connection list

# Test a specific profile connection
snow connection test --connection-name my-profile

# Set a default profile
snow connection set-default my-profile

# Check profile status with snowcli-tools
snowflake-cli config status
```

### Troubleshooting Profile Issues

**No profiles found?**
```bash
# Create your first profile
snow connection add --connection-name my-profile
```

**Profile validation failed?**
```bash
# Check available profiles
snow connection list

# Set the correct profile
export SNOWFLAKE_PROFILE=your-profile-name
# Or pass it directly
snowflake-cli --profile your-profile-name <command>
```

**Connection test failing?**
```bash
# Test your profile connection
snow connection test --connection-name your-profile-name
```

### 📚 Additional Documentation

For comprehensive troubleshooting and configuration guidance, see:

- **[Profile Troubleshooting Guide](docs/profile_troubleshooting_guide.md)** - Detailed troubleshooting for all profile-related issues
- **[Profile Validation Quick-Start](docs/profile_validation_quickstart.md)** - Step-by-step setup guide with practical examples
- **[MCP Diagnostic Tools Reference](docs/mcp_diagnostic_tools.md)** - Complete reference for health monitoring tools
- **[MCP Server User Guide](docs/mcp_server_user_guide.md)** - Enhanced user guide with v1.4.4+ features

### Optional Helper

```bash
# Convenience only: creates a key‑pair profile via `snow connection add`
uv run snowflake-cli setup-connection
```

This helper is optional; you can always manage profiles directly with `snow`.

## Usage

All commands are run through the `snowflake-cli` entry point.

### Advanced Lineage Features

Build and analyze comprehensive data lineage with column-level tracking:

```python
from snowcli_tools.lineage import (
    ColumnLineageExtractor,
    ImpactAnalyzer,
    LineageHistoryManager,
    ChangeType
)

# Extract column-level lineage
extractor = ColumnLineageExtractor()
lineage = extractor.extract_column_lineage(sql_text, target_table="my_table")

# Analyze impact of changes
analyzer = ImpactAnalyzer(lineage_graph)
report = analyzer.analyze_impact("table_name", ChangeType.DROP)

# Track lineage over time
history = LineageHistoryManager()
snapshot = history.capture_snapshot(catalog_path, tag="v1.0")
```

See [Advanced Lineage Documentation](docs/advanced_lineage_features.md) for detailed examples.

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

### Lineage Analysis

Build and explore a cached lineage graph sourced from your catalog JSON/JSONL.

```bash
# 1) Ensure a fresh catalog exists (see catalog section for options)
uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue

# 2) Build the lineage cache (writes to ./lineage/<catalog-name>)
uv run snowflake-cli lineage rebuild --catalog-dir ./data_catalogue

# 3a) Inspect both upstream + downstream nodes around an object
uv run snowflake-cli lineage neighbors PIPELINE.RAW.VW_SAMPLE -d 3

# 3b) Export HTML (Pyvis) to a custom location
uv run snowflake-cli lineage upstream PIPELINE.RAW.VW_SAMPLE \
  --format html --output ./lineage/html/vw_sample_upstream.html

# 3c) Emit JSON for automation/diffing
uv run snowflake-cli lineage downstream PIPELINE.RAW.LOAD_TASK \
  --format json --output ./lineage/json/load_task_downstream.json

# 4) Review parsing coverage and unresolved references
uv run snowflake-cli lineage audit --format json
```

Key behaviors:
- `lineage rebuild` parses the catalog once and caches both the graph and audit metadata. Re-run with updated catalog content to refresh the cache.
- Query commands (`neighbors`, `upstream`, `downstream`) default to limited depth (3 or 5 levels) so the output stays focused on the most relevant upstream/downstream hops; use `-d/--depth` to widen or contract the traversal.
- Task nodes rely on catalog entries ending with `::task`; the CLI automatically normalizes keys so you can search with the base object name.
- JSON output mirrors the cached graph (nodes, edges, attributes) for tooling and regression checks; HTML produces an interactive visualization powered by Pyvis.
- `lineage audit` summarizes parse status, unresolved references, and coverage so you know when missing SQL or privileges limit the analysis.

Scope and expectations:
- The lineage graph reflects the SQL currently captured in your catalog. Update the catalog (and rebuild lineage) after schema or task changes to keep results accurate.
- Only objects present in the catalog and supported by the builder (tables, views, materialized views, dynamic tables, tasks, procedures/functions with SQL) appear in traversal results.
- The tool surfaces observed dependencies; it does not simulate hypothetical future changes beyond what exists in the catalog snapshot.

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

## MCP Server Integration

Snowcli-tools includes an MCP (Model Context Protocol) server that provides AI assistants with direct access to your Snowflake data and metadata.

### Starting the MCP Server

```bash
# Start the MCP server (recommended)
uv run snowflake-cli mcp

# If you rely on a different default profile, set
#   export SNOWCLI_DEFAULT_PROFILE=<profile-name>
# or pass --profile/--enable-cli-bridge as needed.

# Or run the example directly
uv run python examples/run_mcp_server.py
```

To expose the legacy Snowflake CLI bridge tool (which shells out to the `snow`
binary), pass `--enable-cli-bridge`. The FastMCP server defaults to the safer
in-process connector tools, so the bridge is opt-in for cases where you need parity with older scripts:

```bash
uv run snowflake-cli mcp --enable-cli-bridge
```

### MCP Client Configuration

#### VS Code / Cursor Configuration
Create or update your MCP configuration file (usually `~/.vscode/mcp.json` or similar):

```json
{
  "mcpServers": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowflake_connector_py"
    }
  }
}
```

#### Claude Code Configuration
Add to your Claude Code MCP settings:

```json
{
  "mcp": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowflake_connector_py"
    }
  }
}
```

### Available MCP Tools

The MCP server exposes these tools to AI assistants:

#### Core Data Tools
- **execute_query**: Run SQL queries against your Snowflake database
- **preview_table**: Preview table contents with optional filtering
- **build_catalog**: Generate comprehensive data catalogs from your Snowflake metadata
- **query_lineage**: Analyze data lineage and dependencies for any object
- **build_dependency_graph**: Create dependency graphs showing object relationships
- **get_catalog_summary**: Get summaries of existing catalog data
- **test_connection**: Verify your Snowflake connection is working
- **run_cli_query** *(optional)*: Execute SQL using the Snowflake CLI bridge
  when `--enable-cli-bridge` is supplied

#### Diagnostic & Health Monitoring Tools (v1.4.4+)
- **health_check**: Comprehensive server health status with component details
- **check_profile_config**: Validate profile configuration and get recommendations
- **get_resource_status**: Check availability of all MCP resources and dependencies
- **check_resource_dependencies**: Validate dependencies for specific resources

These diagnostic tools provide real-time insights into server health, profile configuration, and resource availability, making troubleshooting much more efficient.

### Usage Examples

Once configured, AI assistants can:

- "Show me the schema of the CUSTOMERS table"
- "Build a catalog of all tables in the SALES database"
- "What's the lineage for the USER_ACTIVITY view?"
- "Execute this query and show me the results"
- "Generate a dependency graph for my data warehouse"

The MCP server maintains context and provides structured responses, making it much more reliable than shell command parsing.

> **Note:** Snowcli-tools keeps Snowflake connection state isolated per tool
> invocation by snapshotting the shared FastMCP session (role, warehouse,
> database, schema) and restoring it after each call. This ensures overrides
> never leak into Snowflake's official toolset.

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
| `lineage`          | Build and query the cached lineage graph (rebuild/query/audit). |
| `config`           | Show the current tool configuration.                     |
| `setup-connection` | Helper to create a persistent `snow` CLI connection.     |
| `init-config`      | Create a local configuration file for this tool.         |
| `mcp`              | Start the MCP server for AI assistant integration.       |

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

# Lint code
uv run ruff check src/

# Format code
uv run black src/
```

## License

This project is licensed under the MIT License.
