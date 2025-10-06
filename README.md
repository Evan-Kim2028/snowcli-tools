# SnowCLI Tools

> **AI-Powered Snowflake Discovery & Data Operations**

Transform your Snowflake data operations with automated cataloging, advanced lineage analysis, SQL safety validation, and seamless AI assistant connectivity through MCP (Model Context Protocol).

[![PyPI version](https://badge.fury.io/py/snowcli-tools.svg)](https://pypi.org/project/snowcli-tools/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

---
### 🧠 **AI-Powered Discovery**
Automatically understand tables using Snowflake Cortex Complete:
- **Business Purpose**: "Customer master data with contact info" (not just column names)
- **PII Detection**: Identifies sensitive data with 95%+ accuracy
- **Relationship Discovery**: Finds foreign keys even without constraints
- **Smart Documentation**: Generates readable docs with confidence indicators

### 🎛️ **Simplified Interface**
Control every aspect independently:
```python
# Full control with boolean flags
profile_table(
    "CUSTOMERS",
    include_ai_analysis=True,      # AI business context ($0.05)
    include_relationships=True,     # FK discovery ($0.03 more)
    force_refresh=False             # Use cache when available
)

# Quick profiling without AI (2-5s, $0.01)
profile_table("HUGE_TABLE", include_ai_analysis=False)

# Batch profiling with automatic caching
profile_table(["CUSTOMERS", "ORDERS", "PRODUCTS"])
```

### 🚀 **Built on Snowflake Labs Official MCP**
```
┌──────────────────────────────────┐
│   Your AI Assistant (Claude)    │  ← Natural language queries
├──────────────────────────────────┤
│  SnowCLI Tools (This Package)   │  ← Discovery, Catalog, Lineage
├──────────────────────────────────┤
│  Snowflake Labs MCP Server       │  ← Official auth & queries
├──────────────────────────────────┤
│  Snowflake Data Cloud            │  ← Your data warehouse
└──────────────────────────────────┘
```

**Benefits:**
- ✅ Secure: Uses official Snowflake authentication
- ✅ Maintained: Stays in sync with Snowflake updates
- ✅ Integrated: Single MCP endpoint for AI assistants
- ✅ Zero Vendoring: Imports upstream, doesn't fork

---

## 🚀 Quick Start (3 minutes)

### 1. Install
```bash
uv install snowcli-tools
```

### 2. Configure Snowflake Profile
```bash
# Using key-pair authentication (recommended)
snow connection add --connection-name "my-profile" \
  --account "myorg-myaccount" \
  --user "analyst" \
  --private-key-file "~/.ssh/snowflake_key.p8" \
  --database "ANALYTICS" \
  --warehouse "COMPUTE_WH"

# Verify connection
snowflake-cli verify -p my-profile
```

### 3. Start Discovering
```bash
# Connect to AI assistant (Claude, VS Code, Cursor)
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp

# Now in your AI assistant, try:
# "Discover and document the CUSTOMERS table"
# "What tables have PII?"
# "Show me relationships for ORDER_ITEMS"
```

---

## 🎨 Core Features

### 🔍 Discovery Assistant
**AI-powered table understanding**

| Mode | What You Get | Cost | Speed |
|------|-------------|------|-------|
| **Quick** | SQL profiling, patterns, stats | $0.01 | 2-5s |
| **Standard** (default) | + AI purpose analysis, PII detection | $0.05 | 15-20s |
| **Deep** | + Relationship discovery, FK mapping | $0.08 | 25-30s |

**Features:**
- ✅ 75-85% accuracy on table purpose inference
- ✅ 95%+ PII detection (email, phone, SSN patterns)
- ✅ Multi-strategy relationship discovery (name + value overlap)
- ✅ Automatic caching (1-hour TTL, DDL invalidation)
- ✅ Qualitative confidence: "confirmed", "likely", "possibly"
- ✅ Batch processing for multiple tables

### 📊 Data Catalog
**Complete metadata extraction**
```bash
# Build full catalog
snowflake-cli catalog -p prod -o ./catalog

# Incremental refresh (10-20x faster)
snowflake-cli catalog -p prod -o ./catalog --incremental
```

**Features:**
- ✅ Database, schema, table, column metadata
- ✅ DDL extraction for recreating objects
- ✅ Incremental updates (only changed objects)
- ✅ JSON/JSONL output formats

### 🔗 Lineage & Dependencies
**Understand data flows**
```bash
# Column-level lineage
snowflake-cli lineage CUSTOMER_ORDERS -p prod

# Dependency graph (DOT format for Graphviz)
snowflake-cli depgraph -p prod --format dot
```

**Features:**
- ✅ Direct table dependencies
- ✅ Circular dependency detection
- ✅ Impact analysis (what breaks if I change this?)
- ✅ Visual dependency graphs

### 🛡️ SQL Safety (v1.7.0)
**Prevent data disasters**
```python
# Destructive operations are blocked
>>> execute_query("DROP TABLE customers")
Error: Destructive operation blocked. Use execute_query_unsafe() if intentional.

# Safe alternatives suggested
>>> execute_query("DELETE FROM orders WHERE id = 123")
Suggestion: Consider using MERGE or UPDATE for targeted changes.
```

### 🤖 AI Assistant Integration
**Natural language Snowflake operations**

Chat with your data using Claude, VS Code, or Cursor:
- "What's in the CUSTOMERS table?"
- "Show me tables that join with ORDERS"
- "Find all tables containing PII"
- "Generate a data quality report for PRODUCTS"

---

## 💡 Common Workflows

### Onboard to a New Database
```python
# 1. Profile all tables
results = profile_table([
    "CUSTOMERS", "ORDERS", "PRODUCTS", "ORDER_ITEMS"
])

# 2. Generate documentation
print(results.to_markdown())

# 3. Export for wiki
with open("data_dictionary.md", "w") as f:
    f.write(results.to_markdown())
```

### Find Undocumented PII
```python
# Scan all tables for PII
for table in get_all_tables():
    result = profile_table(table)
    if result.first().analysis.pii_columns:
        print(f"⚠️ PII found in {table}: {result.first().analysis.pii_columns}")
```

### Understand Table Relationships
```python
# Map relationships for data modeling
result = profile_table(
    "FACT_SALES",
    include_relationships=True
)

for rel in result.first().relationships:
    print(f"{rel.from_column} → {rel.to_table}.{rel.to_column} ({rel.confidence:.0%})")
```

---

## 📚 Documentation

- **[Getting Started](docs/getting-started.md)** - Detailed setup guide
- **[Discovery Assistant Guide](docs/discovery-assistant.md)** - AI-powered discovery walkthrough
- **[MCP Server Setup](docs/mcp/mcp_server_user_guide.md)** - AI assistant integration
- **[Architecture](docs/architecture.md)** - Technical design & patterns
- **[API Reference](docs/api/TOOLS_INDEX.md)** - Complete API documentation
- **[Migration Guide](CHANGELOG.md)** - Upgrading from older versions

---

## 🛠️ Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12+ | Required for modern syntax |
| Snowflake CLI | Latest | `pip install snowflake-cli` |
| Snowflake Account | Any tier | Need `SELECT` on `INFORMATION_SCHEMA` |
| Cortex Complete | Optional | Required for AI discovery features |

**Permissions Needed:**
- `USAGE` on warehouse, database, schema
- `SELECT` on `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS`
- `SELECT` on target tables for profiling
- Cortex Complete access for AI features

---

## 🔄 Version History

### v1.10.0 (Current) - Discovery Assistant UX Simplification
- ✅ Simplified boolean parameters (remove depth enum)
- ✅ Automatic caching with LRU + TTL
- ✅ Qualitative confidence indicators
- ✅ 40% reduction in MCP token usage

### v1.9.0 - Code Simplification
- ✅ 94% code reduction in lineage module
- ✅ Incremental catalog building (10-20x faster)
- ✅ Consolidated health tools

### v1.7.0 - SQL Safety & Error Handling
- ✅ Destructive operation blocking
- ✅ Intelligent error messages (70% token reduction)
- ✅ Agent-controlled timeouts

[See full changelog](CHANGELOG.md)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built on top of:
- [Snowflake Labs MCP Server](https://github.com/Snowflake-Labs/mcp-servers) - Official Snowflake MCP integration
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework
- [Snowflake Python Connector](https://github.com/snowflakedb/snowflake-connector-python) - Official connector
---

<div align="center">

**Made with ❤️ for data engineers and analysts**

[Report Bug](link-to-issues) · [Request Feature](link-to-issues) · [Documentation](docs/)

</div>
