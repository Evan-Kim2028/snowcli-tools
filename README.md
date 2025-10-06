# SnowCLI Tools

> **Security-First Snowflake MCP Server for AI Agents**

A hardened MCP server extending official Snowflake Labs MCP with read-only-by-default design, SQL injection protection, query timeouts for safer agentic native workflows.

[![PyPI version](https://badge.fury.io/py/snowcli-tools.svg)](https://pypi.org/project/snowcli-tools/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)


### 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (Claude, etc.)                  │
│              "Show me tables with PII in CUSTOMERS"         │
└────────────────────────────┬────────────────────────────────┘
                             │ MCP Protocol (JSON-RPC 2.0)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              SnowCLI Tools MCP Server (This Package)        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Security Layer (SQL Validation & Safety Guards)     │  │
│  │  • SQL injection detection (sqlglot parsing)         │  │
│  │  • Destructive operation blocking (DROP/DELETE/etc)  │  │
│  │  • Query timeout enforcement (120s default)          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  9 MCP Tools:                                        │  │
│  │  • execute_query      → Safe SQL execution           │  │
│  │  • preview_table      → Quick table inspection       │  │
│  │  • profile_table      → AI-powered discovery         │  │
│  │  • build_catalog      → Metadata extraction          │  │
│  │  • get_catalog_summary → Catalog stats              │  │
│  │  • query_lineage      → Data flow analysis           │  │
│  │  • build_dependency_graph → Object relationships     │  │
│  │  • health_check       → System validation            │  │
│  │  • test_connection    → Connectivity check           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ Extends & Reuses
                             ↓
┌─────────────────────────────────────────────────────────────┐
│          Snowflake Labs Official MCP Server                 │
│  • Authentication & connection management                   │
│  • Session context handling                                 │
│  • Base Snowflake operations                                │
└────────────────────────────┬────────────────────────────────┘
                             │ Snowflake Python Connector
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                   Snowflake Data Cloud                      │
│  • Your tables, views, and data                             │
│  • Cortex Complete (AI analysis)                            │
│  • Information Schema (metadata)                            │
└─────────────────────────────────────────────────────────────┘
```

**How It Works:**
1. **Agent Request**: AI assistant receives natural language query from user
2. **Tool Selection**: Agent selects appropriate MCP tool(s) based on intent
3. **Security Validation**: Request passes through security layer (SQL validation, timeout checks)
4. **Execution**: Tool executes using official Snowflake connection (read-only by default)
5. **Response**: Results formatted and returned to agent for user presentation

**Security Features:**
- 🔒 **Read-Only by Default**: Prevents destructive operations (DROP, DELETE, TRUNCATE)
- 🛡️ **SQL Injection Protection**: Input validation and parameterized queries
- ⏱️ **Query Timeouts**: Agent-controlled execution limits (default 120s)
- ✅ **Safe Execution**: Built on official Snowflake authentication

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

## 🤖 Agent-First MCP Tools

All tools designed for safe, intelligent AI agent interaction with Snowflake.

### Core Query Tools

**`execute_query`** - Secure SQL execution with safety guardrails
- **Security**: Blocks DROP, DELETE, TRUNCATE, ALTER, CREATE by default
- **Validation**: SQL injection protection via sqlglot parsing
- **Timeouts**: Configurable limits (default 120s, max 3600s)
- **Use Cases**: Safe data exploration, metrics calculation, audit queries

**`preview_table`** - Quick table inspection
- **Limit**: Max 1000 rows to prevent memory issues
- **Smart Defaults**: Uses session database/schema context
- **Use Cases**: Quick data sampling, schema validation

### Discovery & Documentation Tools

**`profile_table`** - AI-powered table understanding
- **SQL Profiling**: Column stats, patterns, sample data (2-5s, $0.01)
- **AI Analysis**: Business purpose, PII detection via Cortex Complete (15-20s, $0.05)
- **Relationships**: Foreign key discovery via name + value overlap (25-30s, $0.08)
- **Caching**: LRU cache with DDL-based invalidation (1-hour TTL)
- **Use Cases**: Database onboarding, documentation generation, compliance audits

### Catalog & Lineage Tools

**`build_catalog`** - Metadata extraction
- **Incremental**: 10-20x faster refreshes (only changed objects)
- **DDL Capture**: Full object definitions for recreation
- **Use Cases**: Data governance, impact analysis preparation

**`get_catalog_summary`** - Catalog statistics
- **Fast Lookup**: Pre-computed catalog metadata
- **Use Cases**: Quick database overview, object counts

**`query_lineage`** - Data flow analysis
- **Directions**: Upstream (dependencies), downstream (consumers), both
- **Depth Control**: Configurable traversal (default 3 levels)
- **Formats**: Text, JSON, HTML visualization
- **Use Cases**: Impact analysis, data flow documentation

**`build_dependency_graph`** - Object relationships
- **Graph Formats**: JSON (programmatic), DOT (Graphviz visualization)
- **Circular Detection**: Identifies dependency cycles
- **Use Cases**: Migration planning, refactoring analysis

### Health & Diagnostics Tools

**`health_check`** - System validation
- **Components**: Profile config, Snowflake connectivity, Cortex availability
- **Proactive**: Validates setup before query execution
- **Use Cases**: Troubleshooting, deployment verification

**`test_connection`** - Quick connectivity check
- **Lightweight**: Fast profile validation
- **Use Cases**: Connection debugging, profile switching

---

## 💡 Agent Workflow Examples

### Safe Data Exploration
```
Agent: "What's in the CUSTOMERS table?"
→ Uses: preview_table(table_name="CUSTOMERS", limit=100)
→ Returns: Safe sample with schema info, no risk of large data transfer
```

### Intelligent Discovery
```
Agent: "Document all tables with PII"
→ Uses: profile_table(tables=["USERS", "ORDERS", "PAYMENTS"], include_ai_analysis=True)
→ Returns: Business purpose, PII columns identified, cached for 1 hour
```

### Impact Analysis
```
Agent: "What breaks if I change the ORDERS table?"
→ Uses: query_lineage(object_name="ORDERS", direction="downstream", depth=5)
→ Returns: All downstream views, tables, tasks that depend on ORDERS
```

### Secure Metrics
```
Agent: "Calculate monthly revenue"
→ Uses: execute_query("SELECT DATE_TRUNC('month', order_date), SUM(total) FROM orders GROUP BY 1", timeout_seconds=60)
→ Returns: Results with automatic timeout protection, no destructive ops possible
```

---

## 🔄 Version History

### v1.10.0 (Unreleased) - Security Hardening & Discovery Assistant
- 🔒 Read-only by default (blocks DROP, DELETE, TRUNCATE)
- 🛡️ SQL injection protection with sqlglot validation
- ⏱️ Query timeout controls (default 120s, configurable)
- ✅ Simplified boolean parameters (remove depth enum)
- ✅ Automatic caching with LRU + TTL
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

## 📚 Documentation

### Getting Started
- **[Getting Started Guide](docs/getting_started.md)** - 5-minute setup for AI assistants (Claude, VS Code, Cursor)
- **[Security Guide](docs/security.md)** - Safety features and read-only protections
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### Tool Reference
- **[All MCP Tools](docs/api/TOOLS_REFERENCE.md)** - Complete API reference for all 9 tools
- **[profile_table](docs/api/tools/profile_table.md)** - AI-powered table profiling and discovery
- **[query_lineage](docs/api/tools/query_lineage.md)** - Data flow and impact analysis
- **[build_dependency_graph](docs/api/tools/build_dependency_graph.md)** - Object relationship mapping

### Workflows & Guides
- **[Common Workflows](docs/workflows.md)** - Database onboarding, PII detection, impact analysis
- **[Migration Guide](CHANGELOG.md)** - Upgrading from older versions
- **[Documentation Index](docs/INDEX.md)** - Browse all documentation

---

## 🛠️ Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.12+ | Required for modern syntax |
| Snowflake Account | Any tier | Read permissions sufficient |
| Cortex Complete | Optional | For AI-powered `profile_table` analysis |

**Minimum Permissions (Read-Only):**
- `USAGE` on warehouse, database, schema
- `SELECT` on `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS`
- `SELECT` on target tables for data access
- `USAGE` on Cortex Complete (optional, for AI features)

**Why These Permissions Are Safe:**
- No `CREATE`, `DROP`, `DELETE`, `UPDATE` required
- Agent cannot modify data or schema
- Perfect for production read-only analyst workflows

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built on top of:
- [Snowflake Labs MCP Server](https://github.com/Snowflake-Labs/mcp-servers) - Official Snowflake MCP integration
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework
- [Snowflake Python Connector](https://github.com/snowflakedb/snowflake-connector-python) - Official connector

---

<div align="center">

**Security-First Data Tools for AI Agents**

[GitHub](https://github.com/Evan-Kim2028/snowcli-tools) · [PyPI](https://pypi.org/project/snowcli-tools/) · [Documentation](docs/mcp/mcp_server_user_guide.md)

</div>
