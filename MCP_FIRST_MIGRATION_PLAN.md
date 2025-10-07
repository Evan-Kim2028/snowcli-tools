# MCP-First Architecture Migration Plan for snowcli-tools

**Version:** 2.0.0 Target
**Current Version:** 1.9.0
**Date:** 2025-10-07
**Status:** Planning Phase

---

## Executive Summary

This document provides a comprehensive technical implementation plan for migrating snowcli-tools from a dual CLI+MCP architecture to an **MCP-first architecture** with an optional thin CLI wrapper. The migration maintains backward compatibility during transition while establishing MCP as the single source of truth for all operations.

### Key Objectives

1. **Single Source of Truth**: MCP server becomes the canonical implementation
2. **Reduced Code Duplication**: Eliminate parallel CLI/MCP implementations
3. **Improved Maintainability**: One codebase path to maintain and test
4. **Backward Compatibility**: Gradual deprecation with clear migration path
5. **Better User Experience**: Consistent behavior across all interfaces

### Migration Philosophy

- **MCP-First, CLI-Optional**: MCP server is primary, CLI is a thin client
- **Graceful Deprecation**: Multi-version transition with clear warnings
- **User-Centric**: Comprehensive migration guides and tooling
- **Test-Driven**: Maintain or improve test coverage throughout

---

## Phase 0: Current State Analysis

### Architecture Overview

**Current Structure:**
```
snowcli-tools (v1.9.0)
├── CLI Layer (2,685 LOC across commands/)
│   ├── cli.py (138 LOC)
│   ├── commands/
│   │   ├── analyze.py (540 LOC) - lineage, dependencies
│   │   ├── discover.py (213 LOC) - catalog, export-sql
│   │   ├── query.py (318 LOC) - run, preview, parallel
│   │   ├── setup.py (401 LOC) - verify, test, config, mcp
│   │   └── registry.py (68 LOC)
│   └── Legacy aliases (catalog, depgraph, etc.)
│
├── MCP Layer (~780 LOC)
│   ├── mcp_server.py (780 LOC)
│   └── mcp/tools/ (10 tools, ~50 LOC each)
│       ├── execute_query.py
│       ├── preview_table.py
│       ├── build_catalog.py
│       ├── query_lineage.py
│       ├── build_dependency_graph.py
│       ├── health.py
│       ├── test_connection.py
│       └── get_catalog_summary.py
│
├── Service Layer (Shared) (~1,200 LOC)
│   ├── service_layer/
│   │   └── query.py (143 LOC)
│   ├── catalog/service.py
│   ├── dependency/service.py
│   └── lineage/queries.py
│
└── Core Infrastructure (~2,000 LOC)
    ├── config.py
    ├── profile_utils.py
    ├── session_utils.py
    ├── error_handling.py
    └── snow_cli.py (SnowCLI wrapper)
```

### Feature Parity Analysis

#### ✅ Features with Full MCP Parity

| CLI Command | MCP Tool | Status | Notes |
|-------------|----------|--------|-------|
| `catalog` | `build_catalog` | ✅ Full parity | Both use `CatalogService` |
| `depgraph` | `build_dependency_graph` | ✅ Full parity | Both use `DependencyService` |
| `lineage` | `query_lineage` | ✅ Full parity | Both use `LineageQueryService` |
| `query run` | `execute_query` | ✅ Full parity | Both use `QueryService` |
| `query preview` | `preview_table` | ✅ Full parity | Both use `QueryService` |
| `setup verify` | `test_connection` | ✅ Full parity | Both test connectivity |
| N/A | `health_check` | ✅ MCP-only | New in v1.9.0 |
| N/A | `get_catalog_summary` | ✅ MCP-only | New in v1.9.0 |

#### ⚠️ Features with Partial Parity

| CLI Command | MCP Equivalent | Gap | Impact |
|-------------|----------------|-----|--------|
| `query parallel` | None | No MCP tool for parallel batch queries | LOW - Advanced feature, rarely used |
| `export-sql` | None | No MCP tool for DDL export | MEDIUM - Useful for backups |
| `setup config` | None | No MCP tool to view config | LOW - Diagnostic only |
| `setup init_config` | None | No MCP tool to create config | LOW - One-time setup |

#### 🚫 CLI-Only Features (No MCP)

| CLI Command | Description | Usage | Recommendation |
|-------------|-------------|-------|----------------|
| `setup mcp` | Start MCP server | One-time startup | Keep as CLI-only |
| `setup_connection` | Create profile | One-time setup | Keep as CLI-only |
| `-v, --verbose` | Verbose logging | Development | Add to MCP context |
| `-c, --config` | Config file path | Override | Add to MCP args |

### Code Duplication Hotspots

**High Duplication Areas:**
1. **Query Execution Logic** (~200 LOC duplicated)
   - `commands/query.py::run_command()`
   - `mcp/tools/execute_query.py::execute()`
   - Both wrap `QueryService` but with different error handling

2. **Catalog Building Logic** (~150 LOC duplicated)
   - `commands/discover.py::catalog_command()`
   - `mcp/tools/build_catalog.py::execute()`
   - Different output formatting, same core logic

3. **Configuration/Profile Handling** (~100 LOC duplicated)
   - `cli.py` CLI config loading
   - `mcp_server.py` MCP config loading
   - Different validation approaches

4. **Error Handling & Formatting** (~80 LOC duplicated)
   - CLI uses `rich.Console` for output
   - MCP uses structured JSON responses
   - Could be unified with adapter pattern

**Total Duplication:** ~530 LOC (19% of combined CLI+MCP code)

### Dependencies Analysis

**Python Dependencies (from pyproject.toml):**
```toml
# Core dependencies (will remain)
snowflake-cli = ">=2.0.0"           # Profile management
sqlglot = ">=27.16.3"                # SQL parsing
pyyaml = ">=6.0.0"                   # Config files
pydantic = ">=2.7.0"                 # Data validation

# MCP dependencies (will remain)
mcp = ">=1.0.0"                      # MCP protocol
fastmcp = ">=2.8.1"                  # MCP server framework
snowflake-labs-mcp = ">=1.3.3"       # Upstream foundation

# CLI-specific (will deprecate)
click = ">=8.0.0"                    # CLI framework
rich = ">=13.0.0"                    # Terminal formatting
```

**Migration Impact:**
- `click` and `rich` can become optional dependencies in v2.0.0
- Thin wrapper will still need them for v1.x compatibility
- Save ~2MB in minimal MCP-only installations

---

## Phase 1: Preparation & Analysis (v1.9.1)

**Timeline:** 1 week
**Goal:** Audit, document, and prepare for migration without breaking changes

### 1.1 Comprehensive Feature Audit

**Deliverables:**
- ✅ Complete CLI vs MCP feature matrix (see above)
- ✅ Code duplication analysis (530 LOC identified)
- ✅ Dependency graph of shared code
- 📄 Breaking changes documentation

**Action Items:**

1. **Create Feature Parity Tracking Sheet**
   ```bash
   # Run automated analysis
   python scripts/analyze_cli_mcp_parity.py > FEATURE_PARITY.md
   ```

2. **Document Breaking Changes**
   - File: `/docs/v2.0.0_breaking_changes.md`
   - Include:
     - Removed CLI commands
     - Changed argument names
     - Output format changes
     - Environment variable changes

3. **Identify Consolidation Opportunities**
   - Services that can be unified
   - Error handling patterns
   - Configuration loading logic

### 1.2 Code Consolidation Plan

**Files to Modify:**

```python
# NEW: Unified service interface
src/snowcli_tools/service_layer/unified.py
"""
Single entry point for all operations.
Both CLI and MCP will call these functions.
"""

# NEW: CLI adapter layer
src/snowcli_tools/adapters/cli_adapter.py
"""
Converts service layer responses to CLI output format.
Handles rich.Console formatting, exit codes.
"""

# NEW: MCP adapter layer
src/snowcli_tools/adapters/mcp_adapter.py
"""
Converts service layer responses to MCP JSON format.
Already exists implicitly in mcp/tools/ but needs formalization.
"""
```

**Implementation Strategy:**

```python
# Example: Unified query execution
# src/snowcli_tools/service_layer/unified.py

from typing import Any, Dict, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    """Universal query request model."""
    statement: str
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None
    timeout_seconds: int = 120
    verbose_errors: bool = False

class QueryResponse(BaseModel):
    """Universal query response model."""
    statement: str
    rowcount: int
    rows: list[Dict[str, Any]]
    execution_time_ms: float
    warehouse_used: str

    # Optional metadata
    query_id: Optional[str] = None
    bytes_scanned: Optional[int] = None

class UnifiedServiceLayer:
    """Single source of truth for all operations."""

    def __init__(self, context: ServiceContext):
        self.context = context
        self.query_service = QueryService(context)
        self.catalog_service = CatalogService(context)
        # ... other services

    async def execute_query(self, req: QueryRequest) -> QueryResponse:
        """Execute query - used by both CLI and MCP."""
        # Single implementation, no duplication
        result = await self.query_service.execute(
            statement=req.statement,
            overrides={
                "warehouse": req.warehouse,
                "database": req.database,
                "schema": req.schema,
                "role": req.role,
            },
            timeout_seconds=req.timeout_seconds,
        )

        return QueryResponse(
            statement=req.statement,
            rowcount=len(result.rows),
            rows=result.rows,
            execution_time_ms=result.execution_time_ms,
            warehouse_used=result.warehouse_used,
        )
```

### 1.3 Test Coverage Analysis

**Current Test Coverage:**
```bash
# Run coverage analysis
pytest --cov=src/snowcli_tools --cov-report=html
pytest --cov=src/snowcli_tools --cov-report=term-missing

# Expected output (current state):
# src/snowcli_tools/              87%
# src/snowcli_tools/commands/     72%  ← Target for improvement
# src/snowcli_tools/mcp/          91%
# src/snowcli_tools/service_layer 94%
```

**Testing Strategy:**

1. **Maintain or Improve Coverage**
   - Current: 87% overall, 72% for CLI commands
   - Target: 90% overall, 85% for unified services

2. **Test Files to Create/Update:**
   ```
   tests/
   ├── test_unified_services.py       # NEW - Test unified service layer
   ├── test_cli_adapter.py            # NEW - Test CLI adapter
   ├── test_mcp_adapter.py            # NEW - Test MCP adapter
   ├── test_cli_commands.py           # Update - Use unified services
   ├── test_mcp_tools.py              # Update - Use unified services
   └── test_backwards_compat.py       # NEW - Ensure v1.x compat
   ```

3. **Contract Testing**
   - Ensure CLI and MCP produce equivalent outputs
   - Test: `test_cli_mcp_parity.py`

### 1.4 Documentation Planning

**New Documentation Files:**

```
docs/
├── migration/
│   ├── v2.0.0_migration_guide.md     # User-facing migration guide
│   ├── v2.0.0_breaking_changes.md    # Detailed breaking changes
│   ├── v2.0.0_deprecation_timeline.md # Deprecation schedule
│   └── mcp_first_quickstart.md       # Quick start for MCP-only users
├── architecture/
│   ├── mcp_first_architecture.md     # New architecture docs
│   └── unified_service_layer.md      # Service layer design
└── development/
    ├── contributing_mcp_first.md     # Updated contribution guide
    └── testing_guidelines_v2.md      # Updated testing guidelines
```

**Documentation Requirements:**

1. **Migration Guide Template:**
```markdown
# Migrating from CLI to MCP-First (v1.9.x → v2.0.0)

## For End Users

### What's Changing
- CLI commands deprecated in favor of MCP tools
- Thin wrapper CLI available for backward compatibility
- MCP server is now the primary interface

### Migration Paths

#### Option 1: Switch to MCP Server (Recommended)
```bash
# Before (CLI)
snowflake-cli --profile prod catalog -d MY_DB

# After (MCP via Claude Code)
# Just ask Claude: "Build catalog for MY_DB database"
```

#### Option 2: Use Thin Wrapper CLI (Transitional)
```bash
# Install thin wrapper (optional)
pip install snowcli-tools-cli  # Separate package

# Same commands work
snowflake-cli --profile prod catalog -d MY_DB
# → Calls MCP server internally
```

#### Option 3: Direct MCP Client
```python
# Use MCP client library
from mcp import ClientSession
from snowcli_tools.mcp import SnowcliToolsClient

async with SnowcliToolsClient("mystenlabs-keypair") as client:
    result = await client.build_catalog(database="MY_DB")
```

### Timeline
- **v1.9.1** (Now): Deprecation warnings added
- **v1.10.0** (Q1 2025): Thin wrapper CLI released
- **v2.0.0** (Q2 2025): CLI removed from main package
- **v2.1.0** (Q3 2025): Thin wrapper maintenance mode
```

---

## Phase 2: MCP Enhancement & Gap Closure (v1.10.0)

**Timeline:** 2-3 weeks
**Goal:** Ensure MCP server has 100% feature parity with CLI

### 2.1 Missing MCP Tools Implementation

**New MCP Tools to Implement:**

#### 2.1.1 Parallel Query Tool

```python
# src/snowcli_tools/mcp/tools/parallel_query.py

from typing import List, Dict, Any, Optional
from pydantic import Field
from typing_extensions import Annotated

from .base import MCPTool, MCPToolSchema

class ParallelQueryTool(MCPTool):
    """Execute multiple queries in parallel for batch operations."""

    async def execute(
        self,
        statements: Annotated[
            List[str],
            Field(description="List of SQL statements to execute in parallel")
        ],
        warehouse: Annotated[
            Optional[str],
            Field(description="Warehouse override", default=None)
        ] = None,
        max_workers: Annotated[
            int,
            Field(description="Maximum parallel workers", ge=1, le=10, default=4)
        ] = 4,
        ctx: Context | None = None,
    ) -> Dict[str, Any]:
        """Execute queries in parallel using asyncio.gather."""
        import asyncio
        from .execute_query import ExecuteQueryTool

        execute_tool = ExecuteQueryTool(self.config, self.snowflake_service)

        # Execute all queries in parallel
        tasks = [
            execute_tool.execute(
                statement=stmt,
                warehouse=warehouse,
                ctx=ctx
            )
            for stmt in statements
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = []
        failed = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({
                    "statement": statements[i],
                    "error": str(result),
                })
            else:
                successful.append(result)

        return {
            "total": len(statements),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful,
            "errors": failed,
        }
```

**Register in `mcp_server.py`:**
```python
parallel_query_inst = ParallelQueryTool(config, snowflake_service)

@server.tool(
    name="parallel_query",
    description="Execute multiple SQL queries in parallel"
)
async def parallel_query_tool(
    statements: Annotated[List[str], Field(description="SQL statements")],
    warehouse: Optional[str] = None,
    max_workers: int = 4,
    ctx: Context | None = None,
) -> Dict[str, Any]:
    return await parallel_query_inst.execute(
        statements=statements,
        warehouse=warehouse,
        max_workers=max_workers,
        ctx=ctx,
    )
```

#### 2.1.2 Export DDL Tool

```python
# src/snowcli_tools/mcp/tools/export_ddl.py

class ExportDDLTool(MCPTool):
    """Export DDL statements from catalog metadata."""

    async def execute(
        self,
        catalog_dir: Annotated[
            str,
            Field(description="Catalog directory", default="./data_catalogue")
        ] = "./data_catalogue",
        output_format: Annotated[
            str,
            Field(description="Output format (sql/zip)", default="sql")
        ] = "sql",
        include_schemas: Annotated[
            bool,
            Field(description="Include schema DDL", default=True)
        ] = True,
        include_tables: Annotated[
            bool,
            Field(description="Include table DDL", default=True)
        ] = True,
        include_views: Annotated[
            bool,
            Field(description="Include view DDL", default=True)
        ] = True,
    ) -> Dict[str, Any]:
        """Export DDL from cached catalog."""
        from pathlib import Path
        import json

        catalog_path = Path(catalog_dir)

        # Load catalog metadata
        if not catalog_path.exists():
            raise ValueError(f"Catalog directory not found: {catalog_dir}")

        # Read catalog files and extract DDL
        ddl_statements = []
        exported_objects = {
            "schemas": 0,
            "tables": 0,
            "views": 0,
        }

        # Process each catalog file
        for catalog_file in catalog_path.glob("*.json"):
            with catalog_file.open() as f:
                catalog_data = json.load(f)

            if include_schemas and "schemas" in catalog_data:
                for schema in catalog_data["schemas"]:
                    if schema.get("ddl"):
                        ddl_statements.append(schema["ddl"])
                        exported_objects["schemas"] += 1

            if include_tables and "tables" in catalog_data:
                for table in catalog_data["tables"]:
                    if table.get("ddl"):
                        ddl_statements.append(table["ddl"])
                        exported_objects["tables"] += 1

            if include_views and "views" in catalog_data:
                for view in catalog_data["views"]:
                    if view.get("ddl"):
                        ddl_statements.append(view["ddl"])
                        exported_objects["views"] += 1

        if output_format == "sql":
            # Return concatenated SQL
            return {
                "format": "sql",
                "ddl": "\n\n".join(ddl_statements),
                "exported_objects": exported_objects,
            }
        else:
            # Return base64-encoded zip
            import zipfile
            import io
            import base64

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for i, ddl in enumerate(ddl_statements):
                    zipf.writestr(f"object_{i:04d}.sql", ddl)

            zip_buffer.seek(0)
            zip_base64 = base64.b64encode(zip_buffer.read()).decode()

            return {
                "format": "zip",
                "ddl_zip_base64": zip_base64,
                "exported_objects": exported_objects,
            }
```

#### 2.1.3 Get Configuration Tool

```python
# src/snowcli_tools/mcp/tools/get_config.py

class GetConfigTool(MCPTool):
    """Get current configuration settings."""

    async def execute(
        self,
        include_sensitive: Annotated[
            bool,
            Field(description="Include sensitive fields (masked)", default=False)
        ] = False,
    ) -> Dict[str, Any]:
        """Return current configuration with optional sensitive field masking."""
        config_dict = self.config.model_dump()

        if not include_sensitive:
            # Mask sensitive fields
            sensitive_fields = ["private_key_path", "password", "token"]

            def mask_sensitive(obj, path=""):
                if isinstance(obj, dict):
                    return {
                        k: "***MASKED***" if k in sensitive_fields else mask_sensitive(v, f"{path}.{k}")
                        for k, v in obj.items()
                    }
                elif isinstance(obj, list):
                    return [mask_sensitive(item, f"{path}[{i}]") for i, item in enumerate(obj)]
                else:
                    return obj

            config_dict = mask_sensitive(config_dict)

        return {
            "config": config_dict,
            "profile": self.config.snowflake.profile,
            "config_source": "environment" if os.getenv("SNOWFLAKE_PROFILE") else "config_file",
        }
```

### 2.2 MCP Server Improvements

**Enhancements for Standalone Usage:**

#### 2.2.1 Better Error Messages

```python
# src/snowcli_tools/mcp/error_formatter.py

class MCPErrorFormatter:
    """Format errors for MCP clients with actionable guidance."""

    @staticmethod
    def format_profile_error(profile: str, available_profiles: List[str]) -> Dict[str, Any]:
        """Format profile not found error with clear next steps."""
        return {
            "error": "ProfileNotFound",
            "message": f"Snowflake profile '{profile}' not found",
            "available_profiles": available_profiles,
            "next_steps": [
                f"Set SNOWFLAKE_PROFILE to one of: {', '.join(available_profiles)}",
                "Or create a new profile: snow connection add --connection-name <name>",
                "See docs: https://docs.snowflake.com/en/developer-guide/snowflake-cli/",
            ],
            "error_code": "PROFILE_NOT_FOUND",
        }

    @staticmethod
    def format_query_error(
        statement: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format query execution error with debugging hints."""
        return {
            "error": "QueryExecutionFailed",
            "message": str(error),
            "statement": statement,
            "context": context,
            "debugging_hints": [
                "Check warehouse is running and accessible",
                "Verify role has permissions on target objects",
                "Review query syntax with SQLGlot parser",
                "Check Snowflake query history for detailed error",
            ],
            "error_code": "QUERY_FAILED",
        }
```

#### 2.2.2 Server Configuration Validation

```python
# src/snowcli_tools/mcp/validation.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class MCPServerConfig(BaseModel):
    """Validated MCP server configuration."""

    profile: str = Field(..., description="Snowflake profile name")
    warehouse: Optional[str] = Field(None, description="Default warehouse")
    database: Optional[str] = Field(None, description="Default database")
    schema: Optional[str] = Field(None, description="Default schema")
    role: Optional[str] = Field(None, description="Default role")

    timeout_seconds: int = Field(120, ge=1, le=3600)
    max_workers: int = Field(4, ge=1, le=20)

    enable_sql_validation: bool = Field(True)
    enable_circuit_breaker: bool = Field(True)

    @field_validator("profile")
    @classmethod
    def validate_profile_exists(cls, v: str) -> str:
        """Validate profile exists before starting server."""
        from ..profile_utils import get_available_profiles

        available = get_available_profiles()
        if v not in available:
            raise ValueError(
                f"Profile '{v}' not found. Available: {', '.join(available)}"
            )
        return v

    @field_validator("warehouse")
    @classmethod
    def validate_warehouse_uppercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure warehouse name is uppercase."""
        return v.upper() if v else None

def validate_server_config(args: argparse.Namespace) -> MCPServerConfig:
    """Validate server configuration before startup."""
    return MCPServerConfig(
        profile=args.profile or os.getenv("SNOWFLAKE_PROFILE", "default"),
        warehouse=args.warehouse,
        database=args.database,
        schema=args.schema,
        role=args.role,
        timeout_seconds=getattr(args, "timeout_seconds", 120),
        max_workers=getattr(args, "max_workers", 4),
    )
```

### 2.3 Testing MCP Feature Completeness

**Test Suite for MCP Parity:**

```python
# tests/test_mcp_feature_parity.py

import pytest
from typing import Dict, Any
from snowcli_tools.mcp_server import main as mcp_main
from snowcli_tools.cli import cli as cli_main

class TestMCPFeatureParity:
    """Ensure MCP tools have equivalent functionality to CLI commands."""

    @pytest.mark.asyncio
    async def test_catalog_build_parity(self, tmp_path):
        """Test catalog build produces same output via CLI and MCP."""
        output_dir = tmp_path / "catalog_test"

        # Execute via CLI
        cli_result = await run_cli_command([
            "catalog",
            "-d", "TEST_DB",
            "-o", str(output_dir / "cli")
        ])

        # Execute via MCP
        mcp_result = await call_mcp_tool("build_catalog", {
            "database": "TEST_DB",
            "output_dir": str(output_dir / "mcp")
        })

        # Compare outputs
        cli_catalog = load_catalog(output_dir / "cli")
        mcp_catalog = load_catalog(output_dir / "mcp")

        assert cli_catalog.keys() == mcp_catalog.keys()
        assert cli_catalog["tables"] == mcp_catalog["tables"]

    @pytest.mark.asyncio
    async def test_query_execution_parity(self):
        """Test query execution produces same results via CLI and MCP."""
        test_query = "SELECT CURRENT_VERSION() AS version"

        # Execute via CLI
        cli_result = await run_cli_command(["query", "run", test_query])

        # Execute via MCP
        mcp_result = await call_mcp_tool("execute_query", {
            "statement": test_query
        })

        # Compare results
        assert cli_result["rows"] == mcp_result["rows"]
        assert cli_result["rowcount"] == mcp_result["rowcount"]

    @pytest.mark.asyncio
    async def test_all_cli_commands_have_mcp_equivalents(self):
        """Verify every CLI command has an MCP tool equivalent."""
        from snowcli_tools.cli import cli
        from snowcli_tools.mcp_server import register_snowcli_tools

        # Extract CLI commands
        cli_commands = extract_commands(cli)

        # Extract MCP tools
        mcp_tools = extract_mcp_tools()

        # Define expected mappings
        expected_mappings = {
            "catalog": "build_catalog",
            "depgraph": "build_dependency_graph",
            "lineage": "query_lineage",
            "query.run": "execute_query",
            "query.preview": "preview_table",
            "query.parallel": "parallel_query",  # NEW in v1.10.0
            "export-sql": "export_ddl",  # NEW in v1.10.0
            "setup.verify": "test_connection",
            "setup.test": "test_connection",
            "setup.config": "get_config",  # NEW in v1.10.0
        }

        # Verify all mappings exist
        for cli_cmd, mcp_tool in expected_mappings.items():
            assert mcp_tool in mcp_tools, f"Missing MCP tool for CLI command: {cli_cmd}"
```

---

## Phase 3: CLI Deprecation Strategy (v1.10.0 - v1.11.0)

**Timeline:** 2-3 weeks for initial implementation, 3-6 months for user transition
**Goal:** Gracefully deprecate CLI with clear migration path

### 3.1 Deprecation Warnings Implementation

**Approach:** Add deprecation warnings to all CLI commands

```python
# src/snowcli_tools/cli.py

import warnings
from functools import wraps
from typing import Callable

DEPRECATION_MESSAGE = """
┌─────────────────────────────────────────────────────────────┐
│                    DEPRECATION WARNING                       │
├─────────────────────────────────────────────────────────────┤
│ The CLI interface is deprecated and will be removed in v2.0 │
│                                                              │
│ 🔄 Migration Options:                                       │
│                                                              │
│  1. MCP Server (Recommended)                                │
│     - Install: Already included                             │
│     - Start: SNOWFLAKE_PROFILE=prod snowflake-cli mcp       │
│     - Use with: Claude Code, VS Code, Cursor                │
│                                                              │
│  2. Thin Wrapper CLI (Transitional)                         │
│     - Install: pip install snowcli-tools-cli                │
│     - Same commands work                                    │
│                                                              │
│ 📚 Migration Guide:                                         │
│    docs/migration/v2.0.0_migration_guide.md                 │
│                                                              │
│ ⏱️  Timeline:                                                │
│    - v1.10.0 (now): Warnings added                          │
│    - v1.11.0: Thin wrapper released                         │
│    - v2.0.0: CLI removed                                    │
└─────────────────────────────────────────────────────────────┘
"""

def deprecated_command(f: Callable) -> Callable:
    """Decorator to mark CLI commands as deprecated."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Show warning once per session
        if not hasattr(wrapper, "_warning_shown"):
            console.print(DEPRECATION_MESSAGE, style="yellow")
            wrapper._warning_shown = True

            # Also log to structured logger
            logger.warning(
                "deprecated_cli_command_used",
                command=f.__name__,
                migration_guide="docs/migration/v2.0.0_migration_guide.md"
            )

        return f(*args, **kwargs)
    return wrapper

# Apply to all commands
@cli.command()
@deprecated_command
def catalog(*args, **kwargs):
    """Build catalog (DEPRECATED - use MCP server)."""
    # ... existing implementation
```

**Environment Variable Override:**

```python
# Allow disabling warnings for CI/CD
SUPPRESS_DEPRECATION = os.getenv("SNOWCLI_SUPPRESS_DEPRECATION", "false").lower() == "true"

def deprecated_command(f: Callable) -> Callable:
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not SUPPRESS_DEPRECATION and not hasattr(wrapper, "_warning_shown"):
            console.print(DEPRECATION_MESSAGE, style="yellow")
            wrapper._warning_shown = True
        return f(*args, **kwargs)
    return wrapper
```

### 3.2 Thin CLI Wrapper Design

**Goal:** Provide a lightweight CLI that calls the MCP server internally

**Architecture:**
```
┌───────────────────────────────────────────┐
│  User runs: snowflake-cli catalog -d DB   │
└─────────────────┬─────────────────────────┘
                  │
                  v
┌───────────────────────────────────────────┐
│  Thin CLI Wrapper (snowcli-tools-cli)     │
│  - Parse arguments                        │
│  - Connect to MCP server                  │
│  - Format output for terminal             │
└─────────────────┬─────────────────────────┘
                  │ MCP Protocol
                  v
┌───────────────────────────────────────────┐
│  MCP Server (snowcli-tools)               │
│  - Execute actual logic                   │
│  - Return structured response             │
└───────────────────────────────────────────┘
```

**Implementation:**

```python
# NEW PACKAGE: snowcli-tools-cli (separate PyPI package)
# src/snowcli_tools_cli/main.py

import asyncio
import click
from typing import Any, Dict
from rich.console import Console
from rich.table import Table
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

console = Console()

class MCPClientCLI:
    """Thin CLI wrapper that calls MCP server."""

    def __init__(self, profile: str):
        self.profile = profile
        self.session: ClientSession | None = None

    async def connect(self):
        """Connect to local MCP server."""
        # Start MCP server as subprocess
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "snowcli_tools.mcp_server"],
            env={"SNOWFLAKE_PROFILE": self.profile}
        )

        self.stdio, self.write = await stdio_client(server_params)
        self.session = ClientSession(self.stdio, self.write)
        await self.session.initialize()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool and return result."""
        if not self.session:
            await self.connect()

        result = await self.session.call_tool(tool_name, arguments)
        return result.content[0].text  # Parse JSON from text response

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.session:
            await self.session.close()

# CLI commands that wrap MCP tools
@click.group()
@click.option("--profile", "-p", default="default")
@click.pass_context
def cli(ctx, profile: str):
    """SnowCLI Tools - Thin wrapper calling MCP server."""
    ctx.obj = MCPClientCLI(profile)

@cli.command()
@click.option("--database", "-d", help="Database to catalog")
@click.option("--output", "-o", default="./data_catalogue", help="Output directory")
@click.pass_obj
def catalog(client: MCPClientCLI, database: str, output: str):
    """Build Snowflake catalog."""

    async def _run():
        result = await client.call_tool("build_catalog", {
            "database": database,
            "output_dir": output,
        })

        # Format output for terminal (backward compatible)
        console.print(f"[green]✓[/green] Catalog built successfully")
        console.print(f"Database: {result['database']}")
        console.print(f"Tables: {result['object_counts']['tables']}")
        console.print(f"Views: {result['object_counts']['views']}")
        console.print(f"Output: {output}")

    asyncio.run(_run())

@cli.command()
@click.argument("statement")
@click.option("--warehouse", "-w", help="Warehouse override")
@click.pass_obj
def query(client: MCPClientCLI, statement: str, warehouse: str):
    """Execute SQL query."""

    async def _run():
        result = await client.call_tool("execute_query", {
            "statement": statement,
            "warehouse": warehouse,
        })

        # Format as table (backward compatible with old CLI)
        if result["rows"]:
            table = Table()
            for col in result["rows"][0].keys():
                table.add_column(col)
            for row in result["rows"]:
                table.add_row(*[str(v) for v in row.values()])
            console.print(table)
        else:
            console.print(f"Query executed: {result['rowcount']} rows affected")

    asyncio.run(_run())

# Add all other commands...

if __name__ == "__main__":
    cli()
```

**Package Structure:**

```
snowcli-tools-cli/  (NEW separate package)
├── pyproject.toml
│   [project]
│   name = "snowcli-tools-cli"
│   version = "1.10.0"
│   dependencies = [
│       "snowcli-tools>=1.10.0",  # Main package with MCP server
│       "click>=8.0.0",
│       "rich>=13.0.0",
│       "mcp>=1.0.0",
│   ]
│
├── src/snowcli_tools_cli/
│   ├── __init__.py
│   ├── main.py           # CLI wrapper implementation
│   ├── formatters.py     # Output formatting (tables, JSON, etc.)
│   └── compat.py         # Backward compatibility layer
│
├── tests/
│   └── test_cli_wrapper.py
│
└── README.md
    # Thin CLI Wrapper for SnowCLI Tools

    This package provides backward-compatible CLI commands that internally
    call the MCP server. It's a transitional package for users migrating
    from CLI to MCP-first architecture.

    ## Installation
    ```bash
    pip install snowcli-tools-cli
    ```

    ## Usage
    Same commands as before:
    ```bash
    snowflake-cli --profile prod catalog -d MY_DB
    snowflake-cli --profile prod query "SELECT * FROM orders LIMIT 10"
    ```

    ## Migration
    This package will be maintained through v1.x but is deprecated.
    Please migrate to MCP server for the best experience.
```

### 3.3 Migration Messaging Strategy

**Communication Channels:**

1. **In-App Messages** (v1.10.0+)
   - Deprecation warnings on every CLI command
   - `--help` output includes migration notice
   - Error messages reference MCP alternative

2. **PyPI Package Description** (v1.10.0+)
   ```markdown
   # snowcli-tools

   ⚠️ **CLI DEPRECATED**: The command-line interface is deprecated and will be
   removed in v2.0.0. Please migrate to the MCP server for the best experience.

   See migration guide: [docs/migration/v2.0.0_migration_guide.md]
   ```

3. **GitHub README** (v1.10.0+)
   ```markdown
   # ⚠️ Important Notice: CLI Deprecation

   The CLI interface (`snowflake-cli` command) is deprecated as of v1.10.0
   and will be removed in v2.0.0.

   **Recommended Migration Path:**
   - Use MCP server with Claude Code, VS Code, or Cursor
   - See [Migration Guide](docs/migration/v2.0.0_migration_guide.md)

   **Transitional Option:**
   - Install thin wrapper: `pip install snowcli-tools-cli`
   - Same commands work during transition period
   ```

4. **Release Notes** (every release)
   ```markdown
   ## [1.10.0] - 2025-Q1

   ### ⚠️ Breaking Changes Ahead

   This release adds deprecation warnings to all CLI commands. The CLI will be
   removed in v2.0.0 (Q2 2025).

   **Action Required:**
   - Review migration guide: docs/migration/v2.0.0_migration_guide.md
   - Test MCP server integration: SNOWFLAKE_PROFILE=prod snowflake-cli mcp
   - Install thin wrapper if needed: pip install snowcli-tools-cli
   ```

5. **Email/Blog Post** (for registered users, if applicable)
   - Announcement of deprecation
   - Benefits of MCP-first architecture
   - Step-by-step migration tutorial
   - Q&A / FAQ

### 3.4 Version Numbering Strategy

**Semantic Versioning Approach:**

```
v1.9.0  (Current) - Last stable CLI+MCP dual architecture
v1.9.1  (Phase 1)  - Preparation, documentation, no breaking changes
v1.10.0 (Phase 2)  - MCP enhancements, CLI deprecation warnings added
v1.10.1-v1.10.x    - Bug fixes for v1.10.0
v1.11.0 (Phase 3)  - Thin wrapper CLI released as separate package
v1.11.1-v1.11.x    - Bug fixes, extended deprecation period if needed
v2.0.0  (Phase 4)  - CLI removed from main package, MCP-first official
v2.0.1-v2.0.x      - Bug fixes for v2.0.0
v2.1.0  (Future)   - New MCP-first features
```

**Version Support Policy:**

| Version | Status | Support Period | Notes |
|---------|--------|----------------|-------|
| v1.9.x | Stable | Until v2.0.0 | Last version without deprecation warnings |
| v1.10.x | Deprecated | 3-6 months | CLI works but shows warnings |
| v1.11.x | Transitional | 3-6 months | Thin wrapper available |
| v2.0.x | Stable | Ongoing | MCP-first, no CLI in main package |

---

## Phase 4: Code Cleanup & Consolidation (v2.0.0)

**Timeline:** 2-3 weeks
**Goal:** Remove deprecated code, consolidate to single source of truth

### 4.1 File Removal Plan

**Files to Remove:**

```bash
# CLI command implementations (2,685 LOC)
src/snowcli_tools/commands/
├── analyze.py           # REMOVE - 540 LOC
├── discover.py          # REMOVE - 213 LOC
├── query.py             # REMOVE - 318 LOC
├── setup.py             # KEEP MINIMAL - 50 LOC (only mcp command)
├── registry.py          # REMOVE - 68 LOC
└── utils.py             # REMOVE - 27 LOC

# Legacy CLI entrypoint
src/snowcli_tools/cli.py # REMOVE - 138 LOC (replace with minimal MCP launcher)

# CLI-specific dependencies
# In pyproject.toml:
# click>=8.0.0            # MOVE to optional
# rich>=13.0.0            # MOVE to optional
```

**Files to Keep/Modify:**

```python
# KEEP - MCP server (primary interface)
src/snowcli_tools/mcp_server.py  # 780 LOC

# KEEP - Service layer (shared logic)
src/snowcli_tools/service_layer/
├── __init__.py
├── query.py
└── unified.py  # NEW in Phase 2

# KEEP - Core services
src/snowcli_tools/
├── catalog/service.py
├── dependency/service.py
├── lineage/queries.py
└── profile_utils.py

# KEEP - MCP tools
src/snowcli_tools/mcp/tools/  # All tools
```

### 4.2 Code Consolidation Checklist

**Step-by-Step Removal Process:**

```bash
# 1. Create backup branch
git checkout -b pre-v2-backup
git push origin pre-v2-backup

# 2. Create v2.0 branch
git checkout -b v2.0-dev

# 3. Remove CLI commands
git rm src/snowcli_tools/commands/analyze.py
git rm src/snowcli_tools/commands/discover.py
git rm src/snowcli_tools/commands/query.py
git rm src/snowcli_tools/commands/registry.py
git rm src/snowcli_tools/commands/utils.py

# 4. Update setup.py entry point
sed -i '' 's/snowflake-cli = "snowcli_tools.cli:main"/snowflake-cli-mcp = "snowcli_tools.mcp_server:main"/' pyproject.toml

# 5. Move CLI deps to optional
# Edit pyproject.toml manually

# 6. Update imports across codebase
# Use automated refactoring tool
python scripts/update_imports_v2.py

# 7. Run full test suite
pytest tests/ --cov=src/snowcli_tools --cov-report=html

# 8. Update documentation
python scripts/update_docs_v2.py

# 9. Build and test package
uv build
pip install dist/snowcli_tools-2.0.0-*.whl
python -m snowcli_tools.mcp_server --help
```

**Automated Refactoring Script:**

```python
# scripts/update_imports_v2.py

import re
from pathlib import Path

def update_imports(file_path: Path):
    """Update imports to remove CLI references."""
    with file_path.open("r") as f:
        content = f.read()

    # Remove CLI command imports
    content = re.sub(
        r"from \.commands import.*\n",
        "",
        content
    )

    # Update cli.py references
    content = re.sub(
        r"from \.cli import.*\n",
        "# CLI removed in v2.0.0 - use MCP server\n",
        content
    )

    # Update entrypoint references
    content = re.sub(
        r"snowflake-cli",
        "snowflake-cli-mcp",
        content
    )

    with file_path.open("w") as f:
        f.write(content)

def main():
    """Update all Python files."""
    src_dir = Path("src/snowcli_tools")

    for py_file in src_dir.rglob("*.py"):
        if "commands" not in py_file.parts:
            print(f"Updating {py_file}")
            update_imports(py_file)

if __name__ == "__main__":
    main()
```

### 4.3 New Package Structure (v2.0.0)

```
snowcli-tools/  (Main package - MCP server only)
├── pyproject.toml
│   [project]
│   name = "snowcli-tools"
│   version = "2.0.0"
│   dependencies = [
│       "mcp>=1.0.0",
│       "fastmcp>=2.8.1",
│       "snowflake-labs-mcp>=1.3.3",
│       "pydantic>=2.7.0",
│       "sqlglot>=27.16.3",
│       # click, rich moved to optional
│   ]
│
│   [project.optional-dependencies]
│   cli = ["click>=8.0.0", "rich>=13.0.0"]  # For thin wrapper
│
│   [project.scripts]
│   snowflake-cli-mcp = "snowcli_tools.mcp_server:main"
│
├── src/snowcli_tools/
│   ├── __init__.py
│   ├── mcp_server.py         # Main entrypoint (780 LOC)
│   │
│   ├── mcp/                   # MCP implementation
│   │   ├── __init__.py
│   │   ├── tools/             # 10 MCP tools
│   │   ├── error_formatter.py # NEW - Better errors
│   │   └── validation.py      # NEW - Config validation
│   │
│   ├── service_layer/         # Shared business logic
│   │   ├── __init__.py
│   │   ├── query.py
│   │   └── unified.py         # NEW - Single source of truth
│   │
│   ├── catalog/               # Catalog service
│   ├── dependency/            # Dependency service
│   ├── lineage/               # Lineage service
│   │
│   └── core/                  # Core infrastructure
│       ├── config.py
│       ├── profile_utils.py
│       ├── session_utils.py
│       └── error_handling.py
│
├── tests/                     # Test suite
│   ├── test_mcp_server.py
│   ├── test_mcp_tools.py
│   ├── test_services.py
│   └── test_unified_layer.py
│
└── docs/                      # Documentation
    ├── migration/
    │   └── v2.0.0_migration_guide.md
    ├── mcp/
    │   └── mcp_server_user_guide.md
    └── api/
        └── mcp_tools_reference.md
```

### 4.4 Updated `pyproject.toml` (v2.0.0)

```toml
[project]
name = "snowcli-tools"
version = "2.0.0"
description = "Snowflake MCP Server with catalog, lineage, and dependency analysis"
readme = "README.md"
authors = [
    { name = "Evan Kim", email = "ekcopersonal@gmail.com" }
]
requires-python = ">=3.12"
dependencies = [
    # Core MCP dependencies
    "mcp>=1.0.0",
    "fastmcp>=2.8.1",
    "snowflake-labs-mcp>=1.3.3",

    # Data validation & parsing
    "pydantic>=2.7.0",
    "sqlglot>=27.16.3",
    "pyyaml>=6.0.0",

    # Snowflake integration
    "snowflake-cli>=2.0.0",

    # Visualization
    "pyvis>=0.3.2",
    "networkx>=3.0",

    # Async support
    "websockets>=15.0.1",
]

[project.optional-dependencies]
# Optional CLI wrapper support (for thin wrapper package)
cli = [
    "click>=8.0.0",
    "rich>=13.0.0",
]

# Development dependencies
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.10.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.6.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
# Primary entrypoint - MCP server
snowflake-cli-mcp = "snowcli_tools.mcp_server:main"

# Deprecated - removed in v2.0.0
# snowflake-cli = "snowcli_tools.cli:main"  # Use snowcli-tools-cli package

[project.urls]
Homepage = "https://github.com/Evan-Kim2028/snowcli-tools"
Repository = "https://github.com/Evan-Kim2028/snowcli-tools"
Documentation = "https://github.com/Evan-Kim2028/snowcli-tools#readme"
"Migration Guide" = "https://github.com/Evan-Kim2028/snowcli-tools/blob/main/docs/migration/v2.0.0_migration_guide.md"

[build-system]
requires = ["uv_build>=0.8.15,<0.9.0"]
build-backend = "uv_build"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F"]
ignore = []
```

### 4.5 Documentation Updates

**Files to Update:**

```markdown
# README.md (v2.0.0)

# SnowCLI Tools - MCP Server

> **MCP-first Snowflake operations with AI assistant integration**

## ⚠️ Breaking Changes in v2.0.0

The CLI interface has been removed. Please use the MCP server or thin wrapper.

See [Migration Guide](docs/migration/v2.0.0_migration_guide.md) for details.

## Quick Start

```bash
# 1. Install
pip install snowcli-tools

# 2. Set up profile
snow connection add --connection-name "my-profile" \
  --account "account.region" --user "user" \
  --private-key-file "/path/to/key.p8"

# 3. Start MCP server
SNOWFLAKE_PROFILE=my-profile python -m snowcli_tools.mcp_server

# 4. Use with AI assistants
# - Claude Code: Configure in .mcp.json
# - VS Code: Install MCP extension
# - Cursor: Add to MCP settings
```

## For CLI Users (Transitional)

If you need backward-compatible CLI commands:

```bash
# Install thin wrapper (separate package)
pip install snowcli-tools-cli

# Same commands work
snowflake-cli --profile prod catalog -d MY_DB
```

Note: The thin wrapper is in maintenance mode and will be deprecated in v2.1.0.

## Features

- 🚀 **MCP Server**: First-class MCP protocol support
- 📊 **Data Catalog**: Automated metadata extraction
- 🔗 **Lineage Tracking**: Column-level lineage analysis
- 📈 **Dependency Graphs**: Visual object relationships
- 🧠 **AI Integration**: Works with Claude Code, VS Code, Cursor
- 🛡️ **SQL Safety**: Blocks destructive operations
- ⚡ **High Performance**: Incremental catalog builds (10-20x faster)

## MCP Tools

| Tool | Description |
|------|-------------|
| `execute_query` | Execute SQL queries |
| `preview_table` | Preview table contents |
| `build_catalog` | Build metadata catalog |
| `query_lineage` | Analyze object lineage |
| `build_dependency_graph` | Generate dependency graphs |
| `parallel_query` | Execute parallel batch queries |
| `export_ddl` | Export DDL statements |
| `health_check` | Server health diagnostics |
| `test_connection` | Validate connectivity |
| `get_config` | View configuration |

## Documentation

- [Migration Guide](docs/migration/v2.0.0_migration_guide.md) - Upgrade from v1.x
- [MCP Server Guide](docs/mcp/mcp_server_user_guide.md) - Server setup and usage
- [API Reference](docs/api/mcp_tools_reference.md) - Complete tool documentation
- [Architecture](docs/architecture.md) - Technical design

## Support

- **Issues**: [GitHub Issues](https://github.com/Evan-Kim2028/snowcli-tools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Evan-Kim2028/snowcli-tools/discussions)
- **Documentation**: [/docs](docs/)

## License

[License Type] - see [LICENSE](LICENSE) file

---

**Version 2.0.0** | MCP-First Architecture
```

---

## Phase 5: Testing & Quality Assurance

### 5.1 Testing Strategy

**Test Coverage Goals:**

| Component | Current Coverage | Target Coverage | Priority |
|-----------|------------------|-----------------|----------|
| MCP Server | 91% | 95% | High |
| MCP Tools | 91% | 95% | High |
| Service Layer | 94% | 95% | Medium |
| Unified API | N/A (new) | 90% | High |
| CLI Wrapper | N/A (new pkg) | 85% | Medium |

**Test Categories:**

1. **Unit Tests** (tests/unit/)
   - Individual service methods
   - MCP tool logic
   - Error handling

2. **Integration Tests** (tests/integration/)
   - End-to-end MCP flows
   - Database connectivity
   - Profile management

3. **Contract Tests** (tests/contract/)
   - CLI vs MCP equivalence
   - Backward compatibility
   - API stability

4. **Performance Tests** (tests/performance/)
   - Query execution speed
   - Catalog build performance
   - MCP server responsiveness

5. **Regression Tests** (tests/regression/)
   - v1.x compatibility
   - Thin wrapper behavior
   - Migration scenarios

### 5.2 Continuous Integration Updates

**GitHub Actions Workflow:**

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [ main, v2.0-dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync --all-extras

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src/snowcli_tools --cov-report=xml

    - name: Run integration tests
      run: pytest tests/integration/ -v
      env:
        SNOWFLAKE_PROFILE: ${{ secrets.SNOWFLAKE_TEST_PROFILE }}

    - name: Run contract tests (v1.x compatibility)
      run: pytest tests/contract/ -v

    - name: Check code coverage
      run: |
        coverage report --fail-under=90

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml

  test-thin-wrapper:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Install main package
      run: pip install .

    - name: Install thin wrapper
      run: pip install ./snowcli-tools-cli

    - name: Test CLI commands
      run: |
        snowflake-cli --version
        snowflake-cli --help

    - name: Test backward compatibility
      run: pytest tests/wrapper/ -v
```

### 5.3 User Acceptance Testing

**Beta Testing Program:**

1. **Recruit Beta Testers**
   - Post announcement on GitHub Discussions
   - Email existing users (if contact info available)
   - Reach out to known heavy CLI users

2. **Beta Testing Checklist**
   ```markdown
   # Beta Testing Checklist (v2.0.0-beta.1)

   ## Migration Testing
   - [ ] Install v1.9.x and create catalog
   - [ ] Upgrade to v2.0.0-beta.1
   - [ ] Verify catalog still works
   - [ ] Test MCP server startup
   - [ ] Test AI assistant integration

   ## Thin Wrapper Testing
   - [ ] Install snowcli-tools-cli
   - [ ] Run catalog command
   - [ ] Run query command
   - [ ] Run lineage command
   - [ ] Verify output matches v1.x

   ## Feature Parity Testing
   - [ ] Execute queries via MCP
   - [ ] Build catalog via MCP
   - [ ] Query lineage via MCP
   - [ ] Build dependency graph via MCP
   - [ ] Compare with v1.x CLI output

   ## Performance Testing
   - [ ] Measure catalog build time
   - [ ] Measure query execution time
   - [ ] Measure MCP server startup time
   - [ ] Compare with v1.x baseline

   ## Documentation Testing
   - [ ] Follow migration guide
   - [ ] Test MCP server setup
   - [ ] Verify examples work
   - [ ] Report documentation issues
   ```

3. **Feedback Collection**
   ```markdown
   # Beta Testing Feedback Form

   ## About You
   - How do you use snowcli-tools? (CLI / MCP / Both)
   - What features do you use most?
   - What's your typical use case?

   ## Migration Experience
   - Did the migration guide work for you? (Y/N)
   - How long did migration take? (minutes)
   - What issues did you encounter?

   ## MCP Server Experience
   - MCP server startup: (Easy / Medium / Hard)
   - AI assistant integration: (Working / Issues / Not tested)
   - Overall experience: (Better / Same / Worse than CLI)

   ## Thin Wrapper Experience (if tested)
   - Did CLI commands work as expected? (Y/N)
   - Performance: (Faster / Same / Slower than v1.x)
   - Output format: (Correct / Issues)

   ## Overall
   - Would you recommend v2.0.0 to others? (Y/N)
   - What's the best improvement?
   - What needs more work?
   ```

---

## Phase 6: Rollout & Monitoring (v2.0.0 Release)

### 6.1 Release Timeline

```
Week 1-2: v1.9.1 Release
- Preparation phase complete
- Documentation published
- Feature parity verified

Week 3-4: v1.10.0-beta.1 Release
- MCP enhancements deployed
- Beta testers recruited
- Feedback collection started

Week 5-6: v1.10.0 Release
- Deprecation warnings added
- Thin wrapper published
- Migration guide live

Week 7-14: Transition Period (1.10.x → 1.11.x)
- User migration support
- Bug fixes
- Documentation improvements

Week 15-16: v2.0.0-beta.1 Release
- CLI removed
- Beta testing
- Performance validation

Week 17-18: v2.0.0 Release
- Official MCP-first release
- Press/blog announcement
- Community celebration 🎉
```

### 6.2 Monitoring & Metrics

**Key Metrics to Track:**

1. **Adoption Metrics**
   - PyPI download stats (v1.x vs v2.x)
   - MCP server usage (telemetry if opt-in)
   - Thin wrapper downloads
   - GitHub stars/forks growth

2. **Quality Metrics**
   - Bug reports per version
   - Issue resolution time
   - Test coverage %
   - Performance benchmarks

3. **Community Metrics**
   - GitHub Issues (new vs closed)
   - Discussions activity
   - Pull request contributions
   - Documentation page views

**Monitoring Dashboard:**

```python
# scripts/monitor_metrics.py

import requests
from datetime import datetime, timedelta

def get_pypi_downloads(package: str, days: int = 30):
    """Fetch PyPI download stats."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    url = f"https://pypistats.org/api/packages/{package}/recent"
    response = requests.get(url)
    data = response.json()

    return data["data"]["last_month"]

def get_github_metrics(repo: str):
    """Fetch GitHub repository metrics."""
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    data = response.json()

    return {
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
    }

def print_dashboard():
    """Print monitoring dashboard."""
    # PyPI downloads
    v1_downloads = get_pypi_downloads("snowcli-tools")
    v2_downloads = get_pypi_downloads("snowcli-tools-cli")

    # GitHub metrics
    github_metrics = get_github_metrics("Evan-Kim2028/snowcli-tools")

    print("=" * 60)
    print("SnowCLI Tools - Monitoring Dashboard")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    print("PyPI Downloads (Last 30 days)")
    print(f"  snowcli-tools:     {v1_downloads:,}")
    print(f"  snowcli-tools-cli: {v2_downloads:,}")
    print()
    print("GitHub Metrics")
    print(f"  Stars:        {github_metrics['stars']:,}")
    print(f"  Forks:        {github_metrics['forks']:,}")
    print(f"  Open Issues:  {github_metrics['open_issues']:,}")
    print("=" * 60)

if __name__ == "__main__":
    print_dashboard()
```

### 6.3 Post-Release Support

**Support Resources:**

1. **GitHub Issues Template**
   ```markdown
   ---
   name: v2.0 Migration Issue
   about: Report issues migrating from v1.x to v2.0
   labels: migration, v2.0
   ---

   ## Migration Context
   - **Previous version**: (e.g., v1.9.0)
   - **New version**: (e.g., v2.0.0)
   - **Migration path**: (MCP server / Thin wrapper / Other)

   ## Issue Description
   [Clear description of the issue]

   ## Steps to Reproduce
   1. [First step]
   2. [Second step]
   3. [...]

   ## Expected Behavior
   [What you expected to happen]

   ## Actual Behavior
   [What actually happened]

   ## Environment
   - OS: [e.g., macOS 14.0]
   - Python version: [e.g., 3.12.0]
   - Installation method: [pip / uv / conda]

   ## Additional Context
   [Any other relevant information]
   ```

2. **Migration FAQ**
   ```markdown
   # v2.0 Migration FAQ

   ## Q: Can I still use CLI commands?
   A: Yes, install the thin wrapper: `pip install snowcli-tools-cli`

   ## Q: Will v1.x still work?
   A: Yes, v1.9.x will continue to receive bug fixes for 6 months.

   ## Q: How do I start the MCP server?
   A: Run: `SNOWFLAKE_PROFILE=prod python -m snowcli_tools.mcp_server`

   ## Q: My catalog broke after upgrading
   A: Catalogs from v1.x are compatible. Try rebuilding: `build_catalog` tool

   ## Q: How do I integrate with Claude Code?
   A: See guide: docs/mcp/mcp_server_user_guide.md

   ## Q: Performance seems slower
   A: MCP server has ~10ms overhead but benefits from persistent connections

   ## Q: Can I rollback to v1.x?
   A: Yes: `pip install snowcli-tools==1.9.0`
   ```

3. **Deprecation Timeline Reminder**
   ```markdown
   # Deprecation Timeline

   | Version | Status | Support End | Notes |
   |---------|--------|-------------|-------|
   | v1.9.x | Stable | 2025-Q4 | Last CLI+MCP dual version |
   | v1.10.x | Deprecated | 2025-Q3 | CLI with warnings |
   | v1.11.x | Transitional | 2025-Q3 | Thin wrapper available |
   | v2.0.x | Current | Ongoing | MCP-first |

   ## Support Policy
   - **Critical bugs**: Fixed in all versions
   - **Security issues**: Fixed in all versions
   - **New features**: Only in v2.x+
   - **Documentation**: Updated for v2.x, maintained for v1.x
   ```

---

## Implementation Checklist

### Phase 1: Preparation (v1.9.1) ✅
- [ ] Complete feature parity analysis
- [ ] Document all breaking changes
- [ ] Identify code consolidation opportunities
- [ ] Create migration guide template
- [ ] Set up testing infrastructure
- [ ] Review and update documentation structure

### Phase 2: MCP Enhancement (v1.10.0)
- [ ] Implement missing MCP tools (parallel_query, export_ddl, get_config)
- [ ] Add better error messages and formatting
- [ ] Implement server configuration validation
- [ ] Create MCP tool contract tests
- [ ] Update MCP server documentation
- [ ] Release v1.10.0-beta.1 for testing

### Phase 3: CLI Deprecation (v1.10.0 - v1.11.0)
- [ ] Add deprecation warnings to all CLI commands
- [ ] Implement thin CLI wrapper package
- [ ] Update PyPI package descriptions
- [ ] Update README with migration notices
- [ ] Send migration announcements
- [ ] Release thin wrapper as separate package
- [ ] Monitor adoption metrics

### Phase 4: Code Cleanup (v2.0.0)
- [ ] Remove CLI command implementations
- [ ] Update pyproject.toml (move CLI deps to optional)
- [ ] Run automated refactoring scripts
- [ ] Update all documentation
- [ ] Remove legacy aliases
- [ ] Consolidate duplicated code
- [ ] Update tests for new structure

### Phase 5: Testing & QA
- [ ] Achieve 90%+ test coverage
- [ ] Run contract tests (CLI vs MCP equivalence)
- [ ] Recruit and onboard beta testers
- [ ] Collect and analyze feedback
- [ ] Fix identified issues
- [ ] Performance benchmarking
- [ ] Security audit

### Phase 6: Release & Monitoring (v2.0.0)
- [ ] Release v2.0.0-beta.1
- [ ] Monitor beta tester feedback
- [ ] Release v2.0.0 stable
- [ ] Publish blog post/announcement
- [ ] Update all external documentation
- [ ] Set up monitoring dashboard
- [ ] Provide ongoing support

---

## Risk Assessment & Mitigation

### High Priority Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Users unaware of deprecation** | High | Medium | Clear warnings, multiple communication channels, extended transition period |
| **Thin wrapper has bugs** | High | Medium | Extensive testing, beta program, quick hotfix releases |
| **Performance regression** | Medium | Low | Benchmark tests, performance monitoring, optimize critical paths |
| **Documentation insufficient** | Medium | Medium | Beta tester feedback, iterative improvements, video tutorials |
| **Breaking changes missed** | High | Low | Comprehensive contract tests, automated compatibility checks |

### Mitigation Strategies

1. **Extended Transition Period**
   - 6+ months between v1.10.0 (warnings) and v2.0.0 (removal)
   - Multiple intermediate releases for feedback
   - Maintain v1.x bug fix branch

2. **Comprehensive Communication**
   - In-app warnings (every CLI command)
   - PyPI package description updates
   - GitHub README banner
   - Email/blog announcements
   - Migration FAQ

3. **Thin Wrapper Safety Net**
   - Separate package for backward compatibility
   - Maintained through v2.0.x
   - Allows gradual migration

4. **Rollback Plan**
   - Keep v1.9.x branch active
   - Document downgrade procedure
   - Maintain v1.x documentation

5. **Beta Testing Program**
   - Recruit diverse user base
   - Comprehensive testing checklist
   - Quick iteration on feedback

---

## Success Criteria

### Phase 1: Preparation (v1.9.1)
✅ **Complete when:**
- Feature parity matrix documented
- Breaking changes list finalized
- Migration guide draft complete
- Code consolidation plan approved

### Phase 2: MCP Enhancement (v1.10.0)
✅ **Complete when:**
- All CLI features have MCP equivalents
- Test coverage >90% for MCP tools
- Beta testers report no major issues
- Performance benchmarks meet targets

### Phase 3: CLI Deprecation (v1.11.0)
✅ **Complete when:**
- Deprecation warnings visible in all CLI commands
- Thin wrapper package published and tested
- Migration guide tested by 10+ users
- Support resources in place

### Phase 4: Code Cleanup (v2.0.0)
✅ **Complete when:**
- CLI code removed from main package
- Test coverage maintained >90%
- Documentation updated and reviewed
- Package size reduced by >20%

### Overall Success Metrics (v2.0.0)
✅ **Success defined as:**
- MCP server adoption >70% of active users
- <10 critical bugs in v2.0.0 release
- User satisfaction >80% (from surveys)
- Documentation rated "helpful" by >85%
- Performance maintained or improved vs v1.x

---

## Appendix

### A. File Size Analysis

```bash
# Current codebase (v1.9.0)
src/snowcli_tools/
├── cli.py                          138 LOC
├── commands/                     2,685 LOC  ← To be removed
├── mcp_server.py                   780 LOC
├── mcp/tools/                      500 LOC
├── service_layer/                1,200 LOC
└── core/                         2,000 LOC
                                  -------
                                  7,303 LOC total

# After cleanup (v2.0.0 target)
src/snowcli_tools/
├── mcp_server.py                   780 LOC
├── mcp/                            650 LOC  (+150 for new tools)
├── service_layer/                1,300 LOC  (+100 for unified API)
└── core/                         2,000 LOC
                                  -------
                                  4,730 LOC total (-35% reduction)
```

### B. Migration Path Decision Tree

```
User wants to upgrade to v2.0.0
│
├─ Uses CLI heavily?
│  ├─ Yes → Install thin wrapper (snowcli-tools-cli)
│  │        ├─ Works? → Gradually migrate to MCP
│  │        └─ Issues? → Report bug, stay on v1.9.x
│  │
│  └─ No → Direct MCP server usage
│           ├─ Has AI assistant? → Configure MCP in assistant
│           ├─ Wants programmatic access? → Use MCP client library
│           └─ Needs CLI occasionally? → Install thin wrapper
│
└─ Automated workflows/CI?
   ├─ Dockerfile → Update to use MCP server
   ├─ Scripts → Rewrite to use MCP client library
   └─ GitHub Actions → Update to use thin wrapper or MCP
```

### C. Version Comparison Matrix

| Feature | v1.9.0 (Current) | v1.10.0 (Deprecated) | v2.0.0 (MCP-First) |
|---------|------------------|----------------------|--------------------|
| CLI Commands | ✅ Full support | ⚠️ Deprecated (works) | ❌ Removed (use wrapper) |
| MCP Tools | ✅ 8 tools | ✅ 11 tools | ✅ 11 tools |
| Package Size | 7,303 LOC | 7,453 LOC | 4,730 LOC (-35%) |
| Dependencies | click, rich required | click, rich required | click, rich optional |
| Test Coverage | 87% | 90% | 95% |
| Documentation | Good | Excellent | Excellent |
| AI Integration | Good | Excellent | Excellent |
| Maintenance Burden | High (dual paths) | High | Low (single path) |

---

## Conclusion

This migration plan provides a comprehensive, phased approach to transitioning snowcli-tools from a dual CLI+MCP architecture to an MCP-first architecture. Key highlights:

1. **Gradual Transition**: 6+ month deprecation period with clear communication
2. **Backward Compatibility**: Thin wrapper CLI for transitional needs
3. **Code Quality**: 35% code reduction, improved maintainability
4. **User-Centric**: Comprehensive migration guides and support
5. **Risk Mitigation**: Beta testing, rollback plans, extended support for v1.x

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 (Preparation) immediately
3. Set target dates for each phase
4. Assign team members to each phase
5. Kick off with feature parity audit

**Questions? Feedback?**
- Open a GitHub Discussion
- Comment on the migration tracking issue
- Reach out to maintainers

---

**Document Version:** 1.0
**Last Updated:** 2025-10-07
**Status:** Draft for Review
**Next Review:** After Phase 1 completion
