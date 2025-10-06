# MCP Tools Complete Reference
**Version:** 1.10.0
**Total Tools:** 9

---

## Overview

SnowCLI Tools provides 9 MCP tools for AI-assisted Snowflake operations, organized into four categories:

1. **Core Query Tools** (2) - SQL execution and table inspection
2. **Discovery & Documentation** (1) - AI-powered table profiling
3. **Catalog & Lineage** (4) - Metadata extraction and dependency analysis
4. **Health & Diagnostics** (2) - System validation and monitoring

All tools are read-only by default with security features including SQL injection protection, query timeouts, and automatic validation.

---

## Quick Reference

| Tool | Category | Cost | Speed | Use Case |
|------|----------|------|-------|----------|
| [execute_query](#execute_query) | Core Query | Free* | Fast | Safe SQL execution |
| [preview_table](#preview_table) | Core Query | Free* | Fast | Quick table sampling |
| [profile_table](#profile_table) | Discovery | $0.01-$0.08 | 2-30s | AI-powered table understanding |
| [build_catalog](#build_catalog) | Catalog | Free* | 1-30min | Metadata extraction |
| [get_catalog_summary](#get_catalog_summary) | Catalog | Free | <50ms | Catalog statistics |
| [query_lineage](#query_lineage) | Lineage | Free | <500ms | Data flow tracing |
| [build_dependency_graph](#build_dependency_graph) | Lineage | Free* | 1-30min | Architecture mapping |
| [health_check](#health_check) | Diagnostics | Free | <1s | System validation |
| [test_connection](#test_connection) | Diagnostics | Free | <1s | Connectivity check |

*Free (uses Snowflake compute credits only)

---

## Tools by Category

### Core Query Tools

Tools for direct SQL execution and data access with security guardrails.

#### execute_query
**Execute safe SQL queries with validation and timeout controls**

**Parameters:**
- `statement` (required): SQL statement to execute
- `timeout_seconds` (optional): Query timeout (default: 120s, max: 3600s)
- `verbose_errors` (optional): Include optimization hints (default: false)
- `warehouse`, `database`, `schema`, `role` (optional): Session overrides

**Security Features:**
- Blocks DROP, DELETE, TRUNCATE, ALTER, CREATE by default
- SQL injection protection via sqlglot parsing
- Configurable timeout enforcement

**Use Cases:**
- Safe data exploration
- Metrics calculation
- Audit queries
- Ad-hoc analysis

**[Full Documentation →](tools/execute_query.md)**

---

#### preview_table
**Quick table inspection with automatic row limits**

**Parameters:**
- `table_name` (required): Table to preview
- `limit` (optional): Row limit (default: 100, max: 1000)
- `warehouse`, `database`, `schema`, `role` (optional): Session overrides

**Features:**
- Automatic LIMIT enforcement
- Schema information included
- No risk of large data transfer

**Use Cases:**
- Quick data sampling
- Schema validation
- Development/testing
- Table verification

**[Full Documentation →](tools/preview_table.md)**

---

### Discovery & Documentation Tools

AI-powered table profiling and documentation generation.

#### profile_table
**AI-powered table understanding with SQL profiling and Cortex Complete**

**Parameters:**
- `table_name` (required): Table or list of tables to profile
- `include_ai_analysis` (optional): Use AI for context inference (default: true)
- `include_relationships` (optional): Discover foreign keys (default: false)
- `output_format` (optional): "markdown" or "json" (default: markdown)
- `timeout_seconds` (optional): Execution timeout (default: 60s)
- `force_refresh` (optional): Bypass cache (default: false)
- `database`, `schema` (optional): Context overrides

**Cost Model:**
- SQL profiling only: ~$0.01 per table (2-5s)
- + AI analysis: ~$0.05 per table (15-20s)
- + Relationships: ~$0.08 per table (25-30s)

**Features:**
- Column statistics (cardinality, null rates, sample values)
- AI-powered business context inference
- PII detection via Cortex Complete
- Foreign key relationship discovery
- Automatic caching (1-hour TTL, DDL-based invalidation)
- Batch processing support

**Use Cases:**
- Database onboarding
- PII detection & compliance
- Data catalog generation
- Schema documentation
- Impact analysis preparation

**[Full Documentation →](tools/profile_table.md)**

**Note:** Renamed from `discover_table_purpose` in v1.10.0

---

### Catalog & Lineage Tools

Tools for metadata extraction, dependency analysis, and data flow tracing.

#### build_catalog
**Extract comprehensive metadata from Snowflake databases**

**Parameters:**
- `database` (optional): Specific database (null = all databases)
- `account` (optional): Include account-level metadata (default: false)
- `format` (optional): "json" or "jsonl" (default: json)
- `include_ddl` (optional): Include DDL definitions (default: true)
- `output_dir` (optional): Output directory (default: ./data_catalogue)

**Features:**
- Parallel metadata extraction
- Incremental builds (10-20x faster refreshes)
- DDL capture for all objects
- Supports tables, views, MVs, dynamic tables, functions, procedures, tasks

**Performance:**
- First build: ~5 min for 1000 tables
- Incremental refresh: ~30s for 100 changes

**Use Cases:**
- Data governance
- Catalog preparation for lineage
- Metadata backups
- Impact analysis setup

**[Full Documentation →](tools/build_catalog.md)**

---

#### get_catalog_summary
**Retrieve statistics from existing catalog**

**Parameters:**
- `catalog_dir` (optional): Catalog directory (default: ./data_catalogue)

**Features:**
- Fast local lookup (<50ms)
- No Snowflake queries
- Object counts by type
- Build metadata

**Returns:**
- Build date and type
- Databases included
- Object counts (tables, views, etc.)
- Total object count
- Catalog size

**Use Cases:**
- Catalog status checks
- Dashboard reporting
- Quick statistics
- Build verification

**[Full Documentation →](tools/get_catalog_summary.md)**

---

#### query_lineage
**Trace data flow and dependencies between objects**

**Parameters:**
- `object_name` (required): Object to analyze
- `direction` (optional): "upstream", "downstream", or "both" (default: both)
- `depth` (optional): Traversal depth 1-10 (default: 3)
- `format` (optional): "text" or "json" (default: text)
- `catalog_dir` (optional): Catalog directory (default: ./data_catalogue)
- `cache_dir` (optional): Lineage cache directory (default: ./lineage)

**Features:**
- Bidirectional traversal
- Fast cached lookups
- Multiple output formats
- Supports tables, views, MVs, dynamic tables, tasks

**Performance:**
- First query: ~2-5s (builds graph)
- Cached queries: <100ms

**Use Cases:**
- Impact analysis ("What breaks if I change this?")
- Source tracing ("Where does this data come from?")
- Refactoring planning
- Documentation generation

**[Full Documentation →](tools/query_lineage.md)**

---

#### build_dependency_graph
**Build complete object dependency graph**

**Parameters:**
- `database` (optional): Specific database (null = all)
- `schema` (optional): Specific schema (null = all)
- `account_scope` (optional): Use ACCOUNT_USAGE (default: true)
- `format` (optional): "json" or "dot" (default: json)

**Features:**
- Account-wide or scoped analysis
- JSON (programmatic) or DOT (Graphviz) output
- Circular dependency detection
- All object types included

**Performance:**
- Small (<100 objects): 10-30s
- Medium (100-1000): 1-5min
- Large (1000+): 5-30min

**Use Cases:**
- Architecture visualization
- Migration planning
- Circular dependency detection
- Cross-database analysis

**[Full Documentation →](tools/build_dependency_graph.md)**

---

### Health & Diagnostics Tools

System validation and connectivity monitoring.

#### health_check
**Comprehensive system health validation**

**Parameters:** None

**Checks:**
- Profile configuration
- Snowflake connectivity
- Cortex Complete availability (optional)
- Resource status

**Returns:**
- Overall health status
- Component-specific diagnostics
- Error details (if any)
- Recommendations

**Use Cases:**
- Deployment verification
- Troubleshooting
- Pre-flight checks
- Monitoring

**[Full Documentation →](tools/health_check.md)**

---

#### test_connection
**Quick Snowflake connectivity check**

**Parameters:** None

**Features:**
- Lightweight validation
- Fast response (<1s)
- Profile verification

**Returns:**
- Connection status
- Profile name
- Account info
- Database/warehouse context

**Use Cases:**
- Quick connectivity tests
- Profile validation
- Session verification
- Debug first step

**[Full Documentation →](tools/test_connection.md)**

---

## Common Workflows

### 1. Database Discovery Workflow

```
1. test_connection()
   ↓ Verify connectivity
2. build_catalog(database="ANALYTICS")
   ↓ Extract metadata
3. get_catalog_summary()
   ↓ Check object counts
4. profile_table(table_name=["TABLE1", "TABLE2", ...])
   ↓ Understand key tables
5. query_lineage(object_name="IMPORTANT_VIEW", direction="both")
   ↓ Map dependencies
```

**Use Case:** Onboard to unfamiliar database

---

### 2. PII Detection Workflow

```
1. build_catalog(database="PROD_DB")
   ↓ Extract all tables
2. get_catalog_summary()
   ↓ Get table list
3. profile_table(
     table_name=[all_tables],
     include_ai_analysis=True,
     output_format="json"
   )
   ↓ Batch profile with PII detection
4. [Parse JSON for PII columns]
   ↓ Identify sensitive data
```

**Use Case:** Compliance audit, PII inventory

---

### 3. Impact Analysis Workflow

```
1. query_lineage(object_name="TABLE_TO_CHANGE", direction="downstream", depth=5)
   ↓ Find all consumers
2. [For each downstream object]:
     profile_table(table_name=object)
   ↓ Understand affected objects
3. build_dependency_graph(database="ANALYTICS", format="dot")
   ↓ Visualize complete impact
```

**Use Case:** Pre-migration planning, schema changes

---

### 4. Quick Schema Inspection

```
1. preview_table(table_name="CUSTOMERS", limit=10)
   ↓ Quick peek at data
2. profile_table(table_name="CUSTOMERS", include_ai_analysis=False)
   ↓ Fast schema details
3. execute_query(statement="SELECT COUNT(*) FROM CUSTOMERS WHERE ...")
   ↓ Targeted analysis
```

**Use Case:** Development, ad-hoc exploration

---

## Tool Selection Guide

### "I need to..."

#### ...understand a table I've never seen before
→ `profile_table(table_name="MYSTERY_TABLE", include_ai_analysis=True)`

#### ...run a safe SQL query
→ `execute_query(statement="SELECT ...", timeout_seconds=120)`

#### ...see what breaks if I change this table
→ `query_lineage(object_name="TABLE", direction="downstream", depth=5)`

#### ...find all PII in my database
→ `profile_table(table_name=[all_tables], include_ai_analysis=True)`

#### ...document my entire database
→ `build_catalog(database="DB", include_ddl=True)`

#### ...visualize my data architecture
→ `build_dependency_graph(database="DB", format="dot")`

#### ...check if my setup is working
→ `health_check()` or `test_connection()`

#### ...get quick statistics about my catalog
→ `get_catalog_summary()`

#### ...see a few sample rows from a table
→ `preview_table(table_name="TABLE", limit=100)`

---

## Version History

### v1.10.0 (Current)
- ✅ Tool renamed: `discover_table_purpose` → `profile_table`
- ✅ Simplified parameters: Boolean flags instead of depth enum
- ✅ Automatic caching with DDL-based invalidation
- ✅ 40% reduction in MCP token usage

### v1.9.0
- ✅ Tool consolidation: 11 → 9 tools (removed v1.4.4 health tools)
- ✅ Incremental catalog building (10-20x faster)
- ✅ Introduced `profile_table` (as `discover_table_purpose`)

### v1.8.0
- Initial MCP tool extraction and modularization

---

## Security Features

All tools include:

- **Read-Only by Default**: Blocks destructive operations (DROP, DELETE, TRUNCATE, ALTER, CREATE)
- **SQL Injection Protection**: Input validation and safe query parsing
- **Query Timeouts**: Agent-controlled execution limits (default 120s, max 3600s)
- **Safe Execution**: Built on official Snowflake authentication
- **Permission Validation**: Profile verification before execution

---

## Support

- **Documentation**: See individual tool documentation for detailed usage
- **Troubleshooting**: Check [Troubleshooting Guide](../troubleshooting.md)
- **Security**: Review [Security Guide](../security.md)
- **Workflows**: See [Workflows Guide](../workflows.md)
- **Quick Start**: Follow [MCP Quick Start](../mcp_quick_start.md)

---

**Last Updated:** 2025-10-06
**Version:** 1.10.0
**Total Tools:** 9 (2 core + 1 discovery + 4 catalog/lineage + 2 diagnostics)
