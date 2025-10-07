# Breaking Changes: v2.0.0 Migration Guide

## Migration from snowcli-tools to nanuk-mcp

Version 2.0.0 represents a **major architectural shift** from a dual CLI/MCP package to a **pure MCP-first architecture**. This change reflects our commitment to AI-first workflows and eliminates maintenance overhead from the legacy CLI interface.

---

## Executive Summary

| Change Category | Impact Level | Users Affected |
|----------------|--------------|----------------|
| **Package Rename** | BREAKING | 100% - All users |
| **CLI Removal** | BREAKING | ~5% - CLI users only |
| **MCP Configuration** | MODERATE | 95% - MCP users |
| **Import Paths** | BREAKING | ~10% - Library users |
| **CI/CD Scripts** | BREAKING | ~15% - Automation users |

**Timeline:**
- **v2.0.0 Release:** Q2 2025
- **v1.x Maintenance:** Until Q4 2025
- **v1.x End of Life:** December 31, 2025

---

## Table of Contents

1. [What's Removed](#1-whats-removed)
2. [What's Changed](#2-whats-changed)
3. [Migration Paths](#3-migration-paths)
4. [User Segment Impact Analysis](#4-user-segment-impact-analysis)
5. [Migration Tools & Automation](#5-migration-tools--automation)
6. [Side-by-Side Comparison](#6-side-by-side-comparison)
7. [Frequently Asked Questions](#7-frequently-asked-questions)
8. [Communication Templates](#8-communication-templates)

---

## 1. What's Removed

### Complete CLI Interface (BREAKING)

All command-line interface functionality has been removed in favor of the MCP server interface.

#### Removed CLI Commands

**Discovery Commands:**
- `snowflake-cli catalog` - Build data catalog
- `snowflake-cli export-sql` - Export SQL files from catalog
- `snowflake-cli discover catalog` - Grouped version
- `snowflake-cli discover export-sql` - Grouped version

**Analysis Commands:**
- `snowflake-cli depgraph` - Generate dependency graph
- `snowflake-cli lineage` - Query lineage information
- `snowflake-cli analyze dependencies` - Grouped version
- `snowflake-cli analyze lineage` - Grouped version

**Query Commands:**
- `snowflake-cli query` - Execute SQL queries
- `snowflake-cli parallel` - Parallel query execution
- `snowflake-cli preview` - Preview table data

**Setup Commands:**
- `snowflake-cli verify` - Verify connection
- `snowflake-cli test` - Test connection with overrides
- `snowflake-cli config` - Display configuration
- `snowflake-cli init_config` - Initialize configuration file
- `snowflake-cli mcp` - Start MCP server (no longer needed)
- `snowflake-cli setup_connection` - Create Snowflake profile

#### Removed Dependencies

The following CLI-specific dependencies are no longer required:

```python
# REMOVED in v2.0
click>=8.0.0          # CLI framework
rich>=13.0.0          # Terminal formatting
```

These dependencies are **still available** in the MCP server for internal use but are not exposed through a CLI interface.

#### Removed Files & Modules

```
src/snowcli_tools/cli.py                 # Main CLI entry point
src/snowcli_tools/commands/              # All CLI command modules
  ├── __init__.py
  ├── analyze.py
  ├── discover.py
  ├── query.py
  ├── setup.py
  ├── registry.py
  └── utils.py
src/snowcli_tools/snow_cli.py           # Snow CLI wrapper (if CLI bridge disabled)
```

#### Removed Script Entry Points

```toml
# REMOVED from pyproject.toml [project.scripts]
snowflake-cli = "snowcli_tools.cli:main"
nanuk = "snowcli_tools.cli:main"  # Legacy alias
```

---

## 2. What's Changed

### Package Name (BREAKING)

| Aspect | v1.x (snowcli-tools) | v2.0 (nanuk-mcp) |
|--------|---------------------|------------------|
| **PyPI Package** | `snowcli-tools` | `nanuk-mcp` |
| **Import Path** | `from snowcli_tools` | `from nanuk_mcp` |
| **CLI Command** | `snowflake-cli` | ❌ **REMOVED** |
| **MCP Server** | `snowflake-cli mcp` | `nanuk-mcp` |
| **GitHub Repo** | `Evan-Kim2028/snowcli-tools` | `Evan-Kim2028/nanuk-mcp` |

### Installation Changes

```bash
# OLD (v1.x)
pip install snowcli-tools

# NEW (v2.0)
pip install nanuk-mcp
```

### MCP Configuration Changes

#### Claude Desktop / MCP Clients

**Old Configuration (`config.json`):**
```json
{
  "mcpServers": {
    "snowflake-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**New Configuration (`config.json`):**
```json
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "nanuk-mcp",
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

### Import Path Changes (Library Users Only)

If you're using snowcli-tools as a Python library (rare, ~10% of users):

```python
# OLD (v1.x)
from snowcli_tools.catalog import CatalogService
from snowcli_tools.lineage import LineageQueryService
from snowcli_tools.mcp_server import main

# NEW (v2.0)
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.lineage import LineageQueryService
from nanuk_mcp.mcp_server import main
```

### Version Detection

```python
# OLD (v1.x)
import snowcli_tools
print(snowcli_tools.__version__)  # "1.9.0"

# NEW (v2.0)
import nanuk_mcp
print(nanuk_mcp.__version__)  # "2.0.0"
```

---

## 3. Migration Paths

### For MCP Users (95% of users) - RECOMMENDED

**Impact:** Configuration update only
**Effort:** 5-10 minutes
**Automation:** Automated script available

#### Step 1: Uninstall Old Package

```bash
pip uninstall snowcli-tools
```

#### Step 2: Install New Package

```bash
pip install nanuk-mcp
```

#### Step 3: Update MCP Configuration

Update your MCP client configuration (Claude Desktop, VS Code, Cursor):

```bash
# Location of config file:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%/Claude/claude_desktop_config.json
# Linux: ~/.config/Claude/claude_desktop_config.json

# Update the configuration:
{
  "mcpServers": {
    "nanuk-mcp": {  // ← CHANGED from "snowflake-tools"
      "command": "nanuk-mcp",  // ← CHANGED from "python -m snowcli_tools.mcp_server"
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

#### Step 4: Restart MCP Client

Restart Claude Desktop, VS Code, or your MCP client to load the new configuration.

#### Step 5: Verify

Test the connection in your AI assistant:

```
User: "Test the Snowflake connection using nanuk-mcp"

Expected Response:
✓ Connection successful
✓ MCP server: nanuk-mcp v2.0.0
✓ Profile: my-profile
```

---

### For CLI Users (5% of users) - MIGRATION REQUIRED

**Impact:** Complete workflow change
**Effort:** 1-2 hours for migration + learning
**Automation:** CLI→MCP translation script available

All CLI commands have direct MCP equivalents. The primary difference is that you'll interact through an AI assistant or MCP client instead of direct terminal commands.

#### Option 1: Use with AI Assistant (RECOMMENDED)

This is the **preferred approach** for most users transitioning from the CLI.

##### Before (v1.x CLI):
```bash
# Build catalog
snowflake-cli --profile my-profile catalog --database ANALYTICS_DB --output ./catalog

# Query lineage
snowflake-cli --profile my-profile lineage CUSTOMER_ORDERS --depth 3

# Generate dependency graph
snowflake-cli --profile my-profile depgraph --database ANALYTICS_DB --format json
```

##### After (v2.0 MCP with Claude Code):

1. Configure nanuk-mcp in your MCP client (see MCP Users section)
2. Use natural language with your AI assistant:

```
User: "Build a catalog for the ANALYTICS_DB database and save it to ./catalog"

AI Assistant (using nanuk-mcp):
- Calls build_catalog tool with database="ANALYTICS_DB", output_dir="./catalog"
- Returns: ✓ Catalog built successfully - 145 tables, 12 views, 1,284 columns

User: "Show me the lineage for CUSTOMER_ORDERS table with depth 3"

AI Assistant:
- Calls query_lineage tool with object_name="CUSTOMER_ORDERS", depth=3
- Returns: Lineage graph with 15 upstream dependencies, 8 downstream consumers

User: "Generate a dependency graph for ANALYTICS_DB in JSON format"

AI Assistant:
- Calls build_dependency_graph tool with database="ANALYTICS_DB", format="json"
- Returns: Dependency graph with 203 nodes, 487 edges
```

**Benefits of this approach:**
- Natural language interface - no memorization of flags
- AI assistant handles error recovery and suggestions
- Conversational workflow with context
- Can chain multiple operations in one request

---

#### Option 2: Use MCP CLI Tools (Advanced)

For programmatic/scripting use, you can use MCP CLI tools directly:

```bash
# Install MCP CLI (if not already installed)
npm install -g @modelcontextprotocol/cli

# Run commands through MCP
mcp run nanuk-mcp build_catalog database=ANALYTICS_DB output_dir=./catalog

mcp run nanuk-mcp query_lineage object_name=CUSTOMER_ORDERS depth=3

mcp run nanuk-mcp build_dependency_graph database=ANALYTICS_DB format=json
```

---

#### Option 3: Python API (For Automation)

Use nanuk-mcp as a library in your Python scripts:

```python
# OLD (v1.x) - Using CLI wrapper
import subprocess
result = subprocess.run([
    "snowflake-cli", "--profile", "my-profile",
    "catalog", "--database", "ANALYTICS_DB"
], capture_output=True)

# NEW (v2.0) - Direct Python API
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.context import create_service_context

context = create_service_context()
service = CatalogService(context=context)
result = await service.build_catalog(database="ANALYTICS_DB", output_dir="./catalog")
print(f"Catalog built: {result.totals.tables} tables, {result.totals.views} views")
```

---

### Complete CLI → MCP Command Mapping

#### Discovery Commands

| v1.x CLI Command | v2.0 MCP Tool | Notes |
|-----------------|--------------|-------|
| `snowflake-cli catalog -d DB -o ./cat` | `build_catalog(database="DB", output_dir="./cat")` | Same functionality |
| `snowflake-cli catalog --account` | `build_catalog(account=True)` | Account-wide catalog |
| `snowflake-cli catalog --incremental` | `build_catalog()` - Always incremental | Incremental is now default |
| `snowflake-cli export-sql -i ./cat` | Embedded in `build_catalog` | Auto-exports SQL when DDL available |

**Example conversation:**
```
User: "Build a catalog for my entire Snowflake account"

AI: Calls build_catalog(account=True)
✓ Scanned 15 databases, 143 schemas, 2,847 tables
✓ Catalog saved to ./data_catalogue
```

---

#### Analysis Commands

| v1.x CLI Command | v2.0 MCP Tool | Notes |
|-----------------|--------------|-------|
| `snowflake-cli depgraph -d DB` | `build_dependency_graph(database="DB")` | Same functionality |
| `snowflake-cli depgraph --format dot` | `build_dependency_graph(format="dot")` | Supports json/dot |
| `snowflake-cli lineage TABLE` | `query_lineage(object_name="TABLE")` | Must build catalog first |
| `snowflake-cli lineage TABLE --depth 5` | `query_lineage(object_name="TABLE", depth=5)` | Same depth control |
| `snowflake-cli lineage TABLE --direction up` | `query_lineage(object_name="TABLE", direction="upstream")` | upstream/downstream/both |

**Example conversation:**
```
User: "What tables depend on CUSTOMER_DIM?"

AI: Calls query_lineage(object_name="CUSTOMER_DIM", direction="downstream", depth=3)
Found 12 downstream dependencies:
- CUSTOMER_ORDERS (view)
- SALES_REPORT (materialized view)
- DAILY_METRICS (dynamic table)
...
```

---

#### Query Commands

| v1.x CLI Command | v2.0 MCP Tool | Notes |
|-----------------|--------------|-------|
| `snowflake-cli query "SELECT ..."` | `execute_query(statement="SELECT ...")` | Same functionality |
| `snowflake-cli query "..." --warehouse WH` | `execute_query(statement="...", warehouse="WH")` | Context overrides supported |
| `snowflake-cli preview TABLE` | `preview_table(table_name="TABLE")` | Same functionality |
| `snowflake-cli preview TABLE --limit 50` | `preview_table(table_name="TABLE", limit=50)` | Default limit: 100 |
| `snowflake-cli parallel DB SCHEMA` | Not directly supported | Use AI to orchestrate multiple execute_query calls |

**Example conversation:**
```
User: "Show me the first 20 rows of USERS table"

AI: Calls preview_table(table_name="USERS", limit=20)
Returns formatted table with 20 rows, 8 columns

User: "Count how many users were created last week"

AI: Calls execute_query(statement="SELECT COUNT(*) FROM USERS WHERE created_at >= DATEADD(week, -1, CURRENT_DATE)")
Returns: 1,247 users
```

---

#### Setup/Verification Commands

| v1.x CLI Command | v2.0 MCP Tool | Notes |
|-----------------|--------------|-------|
| `snowflake-cli verify` | `test_connection()` | Same functionality |
| `snowflake-cli test` | `test_connection()` | Merged into single tool |
| `snowflake-cli config` | `health_check()` | Shows config + health |
| `snowflake-cli mcp` | `nanuk-mcp` command | Direct server start |
| `snowflake-cli init_config` | Manual config file creation | See configuration docs |

**Example conversation:**
```
User: "Test my Snowflake connection"

AI: Calls test_connection()
✓ Connected to account: xy12345.us-west-2
✓ Current warehouse: COMPUTE_WH
✓ Current database: ANALYTICS_DB
✓ Current role: ANALYST
```

---

## 4. User Segment Impact Analysis

### Segment 1: AI Assistant Users (95% of users)

**Who:** Users who interact via Claude Code, VS Code MCP extensions, or other AI assistants

**Impact:** **LOW** - Configuration update only

**Migration Steps:**
1. Uninstall `snowcli-tools`
2. Install `nanuk-mcp`
3. Update MCP configuration file
4. Restart AI assistant

**Estimated Time:** 5-10 minutes

**Risk Level:** Very Low

**Support:** Automated migration script available

---

### Segment 2: Direct CLI Users (5% of users)

**Who:** Users who run `snowflake-cli` commands directly in terminal

**Impact:** **HIGH** - Complete workflow change required

**Migration Steps:**
1. Choose migration path (AI assistant, MCP CLI, or Python API)
2. Update scripts/workflows
3. Learn new interaction model
4. Test thoroughly

**Estimated Time:** 1-2 hours for initial migration, 1 week to adjust workflows

**Risk Level:** Moderate to High

**Support:**
- Detailed command mapping (see Section 3)
- Migration scripts for common patterns
- Extended v1.x support until Dec 2025

**Recommended Path:** Adopt AI assistant workflow for interactive use

---

### Segment 3: CI/CD Automation Users (15% of users)

**Who:** Users with automated scripts calling CLI commands

**Impact:** **MODERATE to HIGH** - Script updates required

**Migration Options:**

**Option A: Python API (Recommended)**
```python
# Before (v1.x bash script)
#!/bin/bash
snowflake-cli --profile prod catalog --database ANALYTICS_DB
snowflake-cli --profile prod depgraph --database ANALYTICS_DB

# After (v2.0 Python script)
import asyncio
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.dependency import DependencyService
from nanuk_mcp.context import create_service_context

async def main():
    context = create_service_context()

    # Build catalog
    catalog_service = CatalogService(context=context)
    await catalog_service.build_catalog(database="ANALYTICS_DB")

    # Build dependency graph
    dep_service = DependencyService(context=context)
    await dep_service.build_graph(database="ANALYTICS_DB")

asyncio.run(main())
```

**Option B: MCP CLI Tools**
```bash
# Using MCP CLI wrapper
mcp run nanuk-mcp build_catalog database=ANALYTICS_DB
mcp run nanuk-mcp build_dependency_graph database=ANALYTICS_DB
```

**Option C: Keep v1.x Until EOL**
- Continue using `snowcli-tools` v1.9.x
- Plan migration before December 2025
- Security patches only, no new features

**Estimated Time:** 2-4 hours per automation pipeline

**Risk Level:** Moderate

**Support:** Example CI/CD migration scripts provided

---

### Segment 4: Library/SDK Users (10% of users)

**Who:** Developers importing `snowcli_tools` modules in Python code

**Impact:** **MODERATE** - Import path changes only

**Migration:**
```python
# Find and replace in codebase
# OLD imports
from snowcli_tools.catalog import CatalogService
from snowcli_tools.lineage import LineageQueryService
from snowcli_tools.mcp_server import main
from snowcli_tools.config import load_config

# NEW imports
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.lineage import LineageQueryService
from nanuk_mcp.mcp_server import main
from nanuk_mcp.config import load_config
```

**Breaking Changes:**
- Package name: `snowcli-tools` → `nanuk-mcp`
- Module path: `snowcli_tools` → `nanuk_mcp`
- **No API changes** - All function signatures remain the same

**Migration Tool:**
```bash
# Automated import replacement script
python scripts/migrate_imports.py /path/to/your/codebase
```

**Estimated Time:** 15-30 minutes for small codebases, 1-2 hours for large codebases

**Risk Level:** Low (automated tools available)

---

## 5. Migration Tools & Automation

### Automated Configuration Updater

A migration script to update MCP configuration files automatically:

```bash
# Download migration script
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_mcp_config.py

# Run migration (auto-detects OS and config location)
python migrate_mcp_config.py

# Output:
# ✓ Found MCP configuration at: ~/Library/Application Support/Claude/claude_desktop_config.json
# ✓ Backed up existing configuration to: claude_desktop_config.json.backup
# ✓ Updated server configuration: snowflake-tools → nanuk-mcp
# ✓ Migration complete! Restart your MCP client.
```

The script:
1. Detects your OS and locates MCP configuration
2. Creates backup of existing configuration
3. Updates package references
4. Validates new configuration
5. Provides rollback instructions if needed

---

### Import Path Migration Script

For Python library users to update import statements:

```bash
# Download import migration script
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_imports.py

# Run on your codebase
python migrate_imports.py /path/to/your/project

# With dry-run to preview changes
python migrate_imports.py /path/to/your/project --dry-run

# Output:
# Scanning /path/to/your/project...
# Found 47 Python files
#
# Changes to be made:
# - src/analytics/pipeline.py: 3 imports updated
# - src/analytics/catalog_builder.py: 5 imports updated
# - tests/test_lineage.py: 2 imports updated
#
# Total: 10 imports in 3 files
#
# Apply changes? [y/N]: y
# ✓ Migration complete!
```

---

### CLI Command Translator

Interactive tool to translate v1.x CLI commands to v2.0 MCP equivalents:

```bash
# Download translator tool
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/translate_cli_to_mcp.py

# Run interactively
python translate_cli_to_mcp.py

# Example session:
Enter v1.x command (or 'quit' to exit): snowflake-cli catalog --database ANALYTICS_DB --output ./catalog

v2.0 MCP Equivalent:
══════════════════════════════════════════════════════════════
Natural Language (Claude Code):
  "Build a catalog for ANALYTICS_DB database and save to ./catalog"

MCP Tool Call:
  build_catalog(
    database="ANALYTICS_DB",
    output_dir="./catalog"
  )

Python API:
  from nanuk_mcp.catalog import CatalogService
  from nanuk_mcp.context import create_service_context

  context = create_service_context()
  service = CatalogService(context=context)
  result = await service.build_catalog(
      database="ANALYTICS_DB",
      output_dir="./catalog"
  )

MCP CLI:
  mcp run nanuk-mcp build_catalog database=ANALYTICS_DB output_dir=./catalog
══════════════════════════════════════════════════════════════
```

---

### Batch Script Migrator

For CI/CD pipelines, migrate entire bash scripts:

```bash
# Process a shell script
python scripts/migrate_bash_script.py my_pipeline.sh

# Generates:
# - my_pipeline_v2.py (Python equivalent using nanuk_mcp API)
# - my_pipeline_v2_mcp.sh (Using MCP CLI)
# - migration_report.md (Detailed changes and notes)
```

---

## 6. Side-by-Side Comparison

### Package Installation

| Aspect | v1.x (snowcli-tools) | v2.0 (nanuk-mcp) |
|--------|---------------------|------------------|
| **PyPI Package** | `pip install snowcli-tools` | `pip install nanuk-mcp` |
| **Source Install** | `git clone .../snowcli-tools` | `git clone .../nanuk-mcp` |
| **Dependencies** | Click, Rich (required) | MCP, FastMCP (required) |
| **CLI Command** | `snowflake-cli` | ❌ Removed |
| **MCP Server** | `snowflake-cli mcp` | `nanuk-mcp` |
| **Python Module** | `python -m snowcli_tools` | `python -m nanuk_mcp` |

---

### Import Statements

```python
# v1.x (snowcli-tools)
from snowcli_tools.catalog import CatalogService
from snowcli_tools.lineage import LineageQueryService
from snowcli_tools.dependency import DependencyService
from snowcli_tools.mcp_server import main
from snowcli_tools.config import load_config, get_config

# v2.0 (nanuk-mcp)
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.lineage import LineageQueryService
from nanuk_mcp.dependency import DependencyService
from nanuk_mcp.mcp_server import main
from nanuk_mcp.config import load_config, get_config
```

**Note:** Only the package prefix changes - all class names, function names, and APIs remain identical.

---

### MCP Configuration

```json
{
  "// v1.x Configuration": "",
  "mcpServers": {
    "snowflake-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  },

  "// v2.0 Configuration": "",
  "mcpServers": {
    "nanuk-mcp": {
      "command": "nanuk-mcp",
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**Changes:**
1. Server name: `snowflake-tools` → `nanuk-mcp`
2. Command: `python -m snowcli_tools.mcp_server` → `nanuk-mcp` (simpler!)
3. Args: Removed (cleaner configuration)

---

### Common Operations Comparison

#### Build Catalog

```bash
# v1.x CLI
snowflake-cli --profile prod catalog --database ANALYTICS_DB --output ./catalog

# v2.0 Natural Language (Claude Code)
"Build a catalog for ANALYTICS_DB and save to ./catalog"

# v2.0 MCP CLI
mcp run nanuk-mcp build_catalog database=ANALYTICS_DB output_dir=./catalog

# v2.0 Python API
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.context import create_service_context

context = create_service_context()
service = CatalogService(context=context)
result = await service.build_catalog(database="ANALYTICS_DB", output_dir="./catalog")
```

---

#### Query Lineage

```bash
# v1.x CLI
snowflake-cli --profile prod lineage CUSTOMER_ORDERS --depth 3 --direction both

# v2.0 Natural Language
"Show me the lineage for CUSTOMER_ORDERS table, 3 levels deep, both upstream and downstream"

# v2.0 MCP CLI
mcp run nanuk-mcp query_lineage object_name=CUSTOMER_ORDERS depth=3 direction=both

# v2.0 Python API
from nanuk_mcp.lineage import LineageQueryService
from pathlib import Path

service = LineageQueryService(catalog_dir=Path("./catalog"), cache_root=Path("./lineage"))
result = service.object_subgraph("CUSTOMER_ORDERS", direction="both", depth=3)
```

---

#### Execute Query

```bash
# v1.x CLI
snowflake-cli --profile prod query "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'"

# v2.0 Natural Language
"Count users created after January 1, 2024"

# v2.0 MCP CLI
mcp run nanuk-mcp execute_query statement="SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'"

# v2.0 Python API (via MCP server)
# Use MCP client to call execute_query tool
```

---

### CI/CD Pipeline Comparison

```bash
# v1.x Bash Script
#!/bin/bash
set -e

export SNOWFLAKE_PROFILE=prod

# Build catalog
snowflake-cli catalog --database ANALYTICS_DB --output ./artifacts/catalog

# Build dependency graph
snowflake-cli depgraph --database ANALYTICS_DB --output ./artifacts/dependencies.json

# Export SQL
snowflake-cli export-sql --input-dir ./artifacts/catalog --output-dir ./artifacts/sql

echo "Pipeline complete!"
```

```python
# v2.0 Python Script
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.dependency import DependencyService
from nanuk_mcp.context import create_service_context

async def main():
    context = create_service_context()
    artifacts_dir = Path("./artifacts")

    # Build catalog
    catalog_service = CatalogService(context=context)
    catalog_result = await catalog_service.build_catalog(
        database="ANALYTICS_DB",
        output_dir=artifacts_dir / "catalog"
    )
    print(f"✓ Catalog built: {catalog_result.totals.tables} tables")

    # Build dependency graph
    dep_service = DependencyService(context=context)
    dep_result = await dep_service.build_graph(database="ANALYTICS_DB")

    # Save dependency graph
    (artifacts_dir / "dependencies.json").write_text(dep_result.model_dump_json(indent=2))
    print(f"✓ Dependency graph: {len(dep_result.nodes)} nodes")

    # SQL export is automatic in build_catalog when DDL is available
    print("Pipeline complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

**Benefits of v2.0 approach:**
- Better error handling
- Type safety
- Programmatic result processing
- Async/await for parallelization
- No subprocess overhead

---

## 7. Frequently Asked Questions

### General Questions

#### Why rename to nanuk-mcp?

**Short Answer:** The name reflects our MCP-first architecture and Snowflake's arctic theme.

**Long Answer:**
1. **Clarity**: The old name `snowcli-tools` implied CLI-first functionality, which no longer applies
2. **Branding**: "Nanuk" (Inuit for "polar bear") fits Snowflake's arctic theme and is memorable
3. **Positioning**: `-mcp` suffix clearly identifies this as an MCP server package
4. **Future-proof**: Name doesn't lock us into specific interface paradigms
5. **Uniqueness**: Stands out in the growing MCP ecosystem

#### Why remove the CLI?

**Reasons:**
1. **Usage Data**: 95% of users interact via MCP; CLI accounts for only 5% of usage
2. **Maintenance Burden**: Dual interfaces (CLI + MCP) require 2x documentation, testing, and bug fixes
3. **AI-First Future**: The industry is moving toward AI-assisted workflows, not CLI commands
4. **Code Complexity**: Removing CLI reduces codebase by ~30%, improving maintainability
5. **Better UX**: Natural language > memorizing flags and options

**Migration Support:**
- v1.x maintained until Dec 2025 (18 months)
- Comprehensive migration tools and documentation
- All CLI functionality available via MCP with better UX

---

### Migration Questions

#### How do I migrate my scripts?

**For Interactive Use:**
- Switch to AI assistant workflow with natural language
- Use provided CLI→MCP translation tool
- See Section 3 for detailed command mapping

**For Automation/CI/CD:**
- **Option A (Recommended)**: Convert to Python API (more robust)
- **Option B**: Use MCP CLI tools (simpler conversion)
- **Option C**: Keep using v1.x until EOL (Dec 2025)

**Tools Available:**
- Automated bash→Python migration script
- CLI command translator
- Example CI/CD pipeline templates

#### Will v1.x still work?

**Yes, with caveats:**

| Aspect | Status | Timeline |
|--------|--------|----------|
| **Installation** | ✓ Available | Until Dec 2025 |
| **Bug Fixes** | ✓ Supported | Until Dec 2025 |
| **Security Patches** | ✓ Supported | Until Dec 2025 |
| **New Features** | ❌ No new features | Only critical fixes |
| **Documentation** | ✓ Archived | Available as historical reference |
| **Support** | ✓ Community support | Best-effort basis |

**Recommendation:** Start migration planning now, complete by Q4 2025

---

#### What about automation/CI/CD?

**You have three options:**

**Option 1: Python API (Best for complex pipelines)**
```python
# More robust, better error handling, type safety
from nanuk_mcp.catalog import CatalogService
# ... (see Section 6 for full examples)
```

**Pros:** Type safety, better errors, programmatic processing
**Cons:** More code changes required

**Option 2: MCP CLI (Best for simple scripts)**
```bash
# Direct CLI replacement
mcp run nanuk-mcp build_catalog database=MYDB
```

**Pros:** Minimal script changes
**Cons:** Requires MCP CLI installation

**Option 3: Stay on v1.x (Temporary)**
```bash
# Keep using snowcli-tools until EOL
pip install snowcli-tools==1.9.0
```

**Pros:** No immediate changes
**Cons:** Must migrate by Dec 2025

**Migration Support:**
- Automated bash→Python conversion script
- CI/CD migration examples in `/examples/ci-cd-migration/`
- Community support in GitHub Discussions

---

### Technical Questions

#### When does v1.x lose support?

**Timeline:**

| Date | Milestone |
|------|-----------|
| **Q2 2025** | v2.0.0 release; v1.9.x enters maintenance mode |
| **Q4 2025** | Final v1.x security patch (v1.9.1) |
| **Dec 31, 2025** | v1.x end of life; no further updates |
| **Q1 2026** | v1.x removed from PyPI (archived) |

**During Maintenance (Q2-Q4 2025):**
- Critical security vulnerabilities patched
- Breaking bugs fixed
- No new features or enhancements
- Limited support (community-driven)

**After EOL (Jan 2026+):**
- No updates or patches
- PyPI package archived (read-only)
- Documentation moved to archive
- Support via community only

---

#### How do I update my MCP configuration?

**Automated (Recommended):**
```bash
# Download and run migration script
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_mcp_config.py
python migrate_mcp_config.py

# Script automatically:
# 1. Locates your MCP config file
# 2. Creates backup
# 3. Updates configuration
# 4. Validates changes
```

**Manual:**
1. Locate your MCP configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Edit the file:
```json
{
  "mcpServers": {
    "nanuk-mcp": {           // ← Change from "snowflake-tools"
      "command": "nanuk-mcp", // ← Change from "python -m snowcli_tools.mcp_server"
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

3. Restart your MCP client (Claude Code, VS Code, etc.)

4. Test the connection:
```
User: "Test Snowflake connection"
AI: ✓ nanuk-mcp v2.0.0 connected successfully
```

---

#### Are there any API breaking changes?

**Good News:** If you're using nanuk-mcp as a Python library, **there are NO API breaking changes**.

**What Changed:**
- Package name: `snowcli-tools` → `nanuk-mcp`
- Import path: `snowcli_tools` → `nanuk_mcp`

**What Stayed the Same:**
- All class names (e.g., `CatalogService`, `LineageQueryService`)
- All method signatures
- All function parameters
- All return types
- All configuration formats

**Example - This code works in both versions:**
```python
# Just change the import
# from snowcli_tools.catalog import CatalogService  # v1.x
from nanuk_mcp.catalog import CatalogService  # v2.0

# Everything else is identical
context = create_service_context()
service = CatalogService(context=context)
result = await service.build_catalog(database="MY_DB")
```

**For MCP Users:**
- Tool names unchanged (e.g., `build_catalog`, `execute_query`)
- Tool parameters unchanged
- Response formats unchanged
- Only MCP configuration file needs updating

---

#### What if I can't migrate by Dec 2025?

**You have several options:**

**Option 1: Plan Now, Execute Q4 2025**
- Continue using v1.x until Q4 2025
- Use automated migration tools closer to deadline
- Migrate 1-2 months before EOL for safety buffer

**Option 2: Hybrid Approach**
- Migrate MCP users immediately (5-10 min effort)
- Keep CLI workflows on v1.x temporarily
- Gradually convert CLI automation to Python API

**Option 3: Fork v1.x (Not Recommended)**
- Fork `snowcli-tools` repository
- Maintain your own fork
- **Cons**: Full maintenance burden, security risks, no upstream improvements

**Option 4: Request Extension (Enterprise Only)**
- Contact maintainers for enterprise support
- Potential paid extended support agreement
- Only for organizations with critical dependencies

**Recommendation:** Start migrating MCP users now (minimal effort), then tackle automation/scripts gradually over next 6 months.

---

#### Can I use both versions simultaneously?

**Technically yes, but not recommended:**

```bash
# You can install both in different environments
python3 -m venv venv-v1
venv-v1/bin/pip install snowcli-tools==1.9.0

python3 -m venv venv-v2
venv-v2/bin/pip install nanuk-mcp==2.0.0
```

**Why it's problematic:**
1. **Confusion**: Hard to remember which environment to activate
2. **Configuration**: Both use same Snowflake profiles, potential conflicts
3. **Maintenance**: Need to maintain two separate setups
4. **Migration Debt**: Delays inevitable migration work

**When it makes sense:**
- **Testing/Validation**: Run v2.0 in test environment while production uses v1.x
- **Gradual Rollout**: Migrate teams/pipelines incrementally
- **Fallback**: Keep v1.x as emergency fallback during initial v2.0 deployment

**Better approach:**
- Commit to v2.0 migration
- Use automated tools to speed up process
- Test thoroughly before removing v1.x

---

## 8. Communication Templates

### GitHub Issue/Discussion Template

```markdown
# 🚨 Breaking Changes: snowcli-tools → nanuk-mcp v2.0

## Summary

Version 2.0 represents a major architectural shift:
- **Package renamed** from `snowcli-tools` to `nanuk-mcp`
- **CLI interface removed** in favor of pure MCP architecture
- **95% of users** (MCP-only) minimally impacted
- **5% of users** (CLI) require migration

## Timeline

- **Q2 2025**: v2.0.0 release
- **Q4 2025**: v1.x final security patch
- **Dec 31, 2025**: v1.x end of life

## Migration Resources

- 📖 [Complete Migration Guide](BREAKING_CHANGES_V2.0.md)
- 🤖 [Automated Migration Scripts](https://github.com/Evan-Kim2028/nanuk-mcp/tree/main/scripts)
- 💬 [Discussion Forum](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
- 🐛 [Report Migration Issues](https://github.com/Evan-Kim2028/nanuk-mcp/issues/new?template=migration-issue.md)

## Quick Migration Steps

### For MCP Users (95%)
1. `pip uninstall snowcli-tools && pip install nanuk-mcp`
2. Update MCP config: Change `snowflake-tools` → `nanuk-mcp`
3. Restart MCP client
4. **Done!** (~5 minutes)

### For CLI Users (5%)
- **Recommended**: Adopt AI assistant workflow
- **Alternative 1**: Use MCP CLI tools
- **Alternative 2**: Use Python API directly
- **Temporary**: Stay on v1.x until Dec 2025

## Why This Change?

1. **Focus**: 95% of usage is via MCP, CLI adds 2x maintenance overhead
2. **Quality**: Single interface = better testing, docs, and reliability
3. **Future**: AI-first approach aligns with industry direction
4. **Naming**: "nanuk-mcp" clearly identifies package purpose

## Questions?

- 💬 Ask in [Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
- 📧 Email: ekcopersonal@gmail.com
- 📚 Read [Full Migration Guide](BREAKING_CHANGES_V2.0.md)
```

---

### PyPI Description Update

**For nanuk-mcp (NEW package):**

```markdown
# Nanuk MCP - Snowflake MCP Server

🐻‍❄️ **AI-first Snowflake operations via Model Context Protocol**

Nanuk (Inuit for "polar bear") brings powerful Snowflake data operations to your AI assistants.

## Features

- 🔍 SQL query execution with safety validation
- 📊 Table profiling and catalog building
- 🔗 Data lineage tracking and impact analysis
- 📚 Metadata extraction and documentation
- 🤖 Native integration with Claude Code, VS Code, Cursor

## Quick Start

```bash
pip install nanuk-mcp
```

Configure in your MCP client:
```json
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "nanuk-mcp",
      "env": {"SNOWFLAKE_PROFILE": "my-profile"}
    }
  }
}
```

## Migration from snowcli-tools

This package replaces `snowcli-tools`. See [Migration Guide](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/BREAKING_CHANGES_V2.0.md).

**Quick migration:**
```bash
pip uninstall snowcli-tools
pip install nanuk-mcp
# Update MCP config (see migration guide)
```

## Documentation

- [Getting Started](https://github.com/Evan-Kim2028/nanuk-mcp#readme)
- [MCP Integration Guide](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/docs/mcp/mcp_server_user_guide.md)
- [API Reference](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/docs/api/README.md)
- [Migration from snowcli-tools](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/BREAKING_CHANGES_V2.0.md)
```

**For snowcli-tools (DEPRECATED package):**

```markdown
# snowcli-tools (DEPRECATED)

⚠️ **This package has been renamed to `nanuk-mcp`**

## Migration Required

`snowcli-tools` is deprecated and will receive no updates after Dec 31, 2025.

**Migrate to nanuk-mcp:**
```bash
pip uninstall snowcli-tools
pip install nanuk-mcp
```

See [Migration Guide](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/BREAKING_CHANGES_V2.0.md) for complete instructions.

## Why the Change?

- **Better Name**: "nanuk-mcp" clearly identifies purpose (MCP server for Snowflake)
- **CLI Removed**: v2.0 is pure MCP architecture (no CLI interface)
- **Focus**: Single interface = better quality and maintenance

## Support Timeline

| Version | Support Until |
|---------|---------------|
| v1.9.x | December 31, 2025 |
| v2.0+ | Use nanuk-mcp instead |

## Resources

- [nanuk-mcp on PyPI](https://pypi.org/project/nanuk-mcp/)
- [Migration Guide](https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/BREAKING_CHANGES_V2.0.md)
- [GitHub Repository](https://github.com/Evan-Kim2028/nanuk-mcp)
```

---

### Email Template (For Known Users)

**Subject:** Action Required: snowcli-tools → nanuk-mcp Migration

```markdown
Hi there,

We're reaching out regarding an important change to snowcli-tools.

## What's Changing

**snowcli-tools is being renamed to nanuk-mcp** with version 2.0, scheduled for Q2 2025.

## Impact on You

Based on our records, you're using snowcli-tools for [MCP integration / CLI tools / API].

**Your Action Required:**
- **MCP Users**: Simple config update (~5 minutes) - [See Instructions](link)
- **CLI Users**: Migration to MCP workflow required - [See Guide](link)
- **API Users**: Import path changes only - [See Details](link)

## Timeline

- **Today**: Announcement, documentation available
- **Q2 2025**: v2.0.0 (nanuk-mcp) release
- **Dec 31, 2025**: snowcli-tools v1.x end of life

## Migration Support

We've created comprehensive migration tools:

1. **Automated Scripts**: One-command migration for most users
2. **Migration Guide**: Complete instructions with examples
3. **Support**: Email ekcopersonal@gmail.com or use GitHub Discussions

## Why This Change?

- **95% of users** interact via MCP (not CLI)
- **Simpler maintenance** = better quality and faster improvements
- **Clearer naming** = nanuk-mcp clearly identifies purpose
- **AI-first future** = aligned with industry direction

## Next Steps

1. Read the [Migration Guide](link)
2. Choose your migration path
3. Use automated tools when ready
4. Reach out if you need help

## Questions?

- 📧 Email: ekcopersonal@gmail.com
- 💬 GitHub: [Discussions](link)
- 📚 Docs: [Migration Guide](link)

Thank you for using snowcli-tools. We're excited about nanuk-mcp's future!

Best regards,
The nanuk-mcp Team
```

---

### Social Media Announcement

**Twitter/X:**
```
🚨 Exciting News: snowcli-tools → nanuk-mcp v2.0! 🐻‍❄️

✨ What's new:
• Pure MCP architecture (CLI removed)
• Clearer naming (nanuk = polar bear 🇮🇸)
• Better focus = higher quality

📅 Timeline:
• Q2 2025: v2.0 launch
• Dec 2025: v1.x EOL

🔗 Migration guide: [link]

#Snowflake #MCP #AI
```

**LinkedIn:**
```
Announcing nanuk-mcp v2.0: The Evolution of snowcli-tools

After analyzing usage patterns, we discovered 95% of users interact via Model Context Protocol (MCP), while only 5% use the CLI directly.

To focus our efforts and deliver higher quality, we're making two major changes:

1. Package rename: snowcli-tools → nanuk-mcp
   • Clearer purpose (MCP server for Snowflake)
   • Memorable branding (Nanuk = polar bear in Inuit)

2. CLI removal: Pure MCP architecture
   • Better maintenance and quality
   • AI-first approach
   • Natural language > command flags

Migration Impact:
• MCP users: ~5 minutes (config update)
• CLI users: 1-2 hours (workflow change)
• API users: ~15 minutes (import changes)

We've built comprehensive migration tools and documentation to make this transition smooth.

v1.x will be maintained until Dec 31, 2025, giving everyone 18+ months to migrate.

Read the full migration guide: [link]

#DataEngineering #Snowflake #AI #MCP
```

---

### In-App Deprecation Warning (v1.9.x)

Add to CLI output in v1.9.x:

```python
# In cli.py main() function
def main() -> None:
    console.print("[yellow]⚠ DEPRECATION WARNING[/yellow]")
    console.print("snowcli-tools CLI is deprecated and will be removed in v2.0 (Q2 2025)")
    console.print("Please migrate to nanuk-mcp: https://github.com/Evan-Kim2028/nanuk-mcp/blob/main/BREAKING_CHANGES_V2.0.md")
    console.print("This warning can be suppressed with: export SNOWCLI_SUPPRESS_DEPRECATION=1\n")

    # ... rest of CLI code
```

---

## Conclusion

The migration from `snowcli-tools` to `nanuk-mcp` v2.0 represents a strategic shift toward AI-first workflows and improved maintainability. While this is a breaking change, we've designed a comprehensive migration path with:

✅ **18-month migration window** (Q2 2025 - Dec 2025)
✅ **Automated migration tools** for all user segments
✅ **Comprehensive documentation** with real examples
✅ **Multiple migration paths** (AI assistant, MCP CLI, Python API)
✅ **Continued v1.x support** for critical fixes

### Key Takeaways

| User Type | Impact | Effort | Recommendation |
|-----------|--------|--------|----------------|
| **MCP Users (95%)** | Low | 5-10 min | Migrate now |
| **CLI Users (5%)** | High | 1-2 hours | Adopt AI workflow |
| **CI/CD Users (15%)** | Moderate | 2-4 hours | Convert to Python API |
| **Library Users (10%)** | Low | 15-30 min | Update imports |

### Migration Checklist

- [ ] Read complete migration guide
- [ ] Choose migration path for your use case
- [ ] Download automated migration tools
- [ ] Test migration in development environment
- [ ] Update production configurations
- [ ] Verify functionality with test connection
- [ ] Update documentation/runbooks
- [ ] Train team on new workflows (if applicable)
- [ ] Remove v1.x dependencies
- [ ] Celebrate successful migration! 🎉

### Support Resources

- 📖 **Documentation**: [github.com/Evan-Kim2028/nanuk-mcp](https://github.com/Evan-Kim2028/nanuk-mcp)
- 🤖 **Migration Scripts**: [github.com/Evan-Kim2028/nanuk-mcp/tree/main/scripts](https://github.com/Evan-Kim2028/nanuk-mcp/tree/main/scripts)
- 💬 **Discussion Forum**: [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
- 🐛 **Issue Tracker**: [GitHub Issues](https://github.com/Evan-Kim2028/nanuk-mcp/issues)
- 📧 **Email**: ekcopersonal@gmail.com

### Thank You

Thank you for being part of the snowcli-tools community. We're excited about nanuk-mcp's future and look forward to continuing to serve your Snowflake automation needs with improved focus and quality.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-07
**Author**: Nanuk MCP Team
**Status**: DRAFT (Pending v2.0 Release)