# SnowCLI Tools Documentation

> **Complete documentation for v1.10.0 - Security-First Snowflake MCP Server for AI Agents**

Welcome to the SnowCLI Tools documentation! This is your central hub for learning, configuring, and using the MCP server with AI assistants.

---

## Quick Navigation

### 🚀 Getting Started (Start Here!)
- **[5-Minute Quick Start](mcp_quick_start.md)** - Get up and running immediately
- **[Installation Guide](getting-started.md)** - Detailed setup instructions
- **[First Steps Tutorial](#first-steps-tutorial)** - Your first queries

### 📖 Core Documentation
- **[MCP Tools Reference](api/TOOLS_REFERENCE.md)** - Complete tool catalog (all 9 tools)
- **[Security Guide](security.md)** - Read-only defaults, SQL injection protection
- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
- **[Workflows Guide](workflows.md)** - End-to-end use cases

### 🔧 Advanced Topics
- **[Architecture Overview](architecture.md)** - System design and service layer
- **[Features Overview](features_overview.md)** - Comprehensive feature inventory
- **[MCP Architecture](mcp/mcp_architecture.md)** - Technical MCP implementation

---

## Documentation by User Journey

### For First-Time Users

**Goal: Get MCP server running in 5 minutes**

1. **[MCP Quick Start](mcp_quick_start.md)** (5 min)
   - Install package
   - Configure Snowflake connection
   - Set up MCP configuration
   - Verify connection

2. **Try These Commands**
   ```
   "Test my Snowflake connection"
   "Show me tables in my database"
   "Profile the CUSTOMERS table"
   ```

**Next:** [Common Workflows](#for-workflow-users)

---

### For Workflow Users

**Goal: Accomplish specific tasks**

#### Database Discovery
**Onboard to unfamiliar database**

- [Workflow: Database Discovery](workflows.md#database-discovery)
- Tools: `test_connection` → `build_catalog` → `profile_table`
- Time: 5-15 minutes

#### PII Detection
**Find sensitive data for compliance**

- [Workflow: PII Detection](workflows.md#pii-detection)
- Tools: `build_catalog` → `profile_table` (batch, AI analysis)
- Time: 10-30 minutes

#### Impact Analysis
**Understand dependencies before changes**

- [Workflow: Impact Analysis](workflows.md#impact-analysis)
- Tools: `query_lineage` → `build_dependency_graph`
- Time: 1-5 minutes

**Next:** [Individual Tool Documentation](#for-tool-users)

---

### For Tool Users

**Goal: Master individual MCP tools**

#### Core Query Tools
| Tool | Purpose | Doc Link |
|------|---------|----------|
| `execute_query` | Safe SQL execution | [→](api/tools/execute_query.md) |
| `preview_table` | Quick table sampling | [→](api/tools/preview_table.md) |

#### Discovery Tools
| Tool | Purpose | Doc Link |
|------|---------|----------|
| `profile_table` | AI-powered table profiling | [→](api/tools/profile_table.md) |

#### Catalog & Lineage Tools
| Tool | Purpose | Doc Link |
|------|---------|----------|
| `build_catalog` | Metadata extraction | [→](api/tools/build_catalog.md) |
| `get_catalog_summary` | Catalog statistics | [→](api/tools/get_catalog_summary.md) |
| `query_lineage` | Data flow tracing | [→](api/tools/query_lineage.md) |
| `build_dependency_graph` | Architecture mapping | [→](api/tools/build_dependency_graph.md) |

#### Diagnostics Tools
| Tool | Purpose | Doc Link |
|------|---------|----------|
| `health_check` | System validation | [→](api/tools/health_check.md) |
| `test_connection` | Connectivity check | [→](api/tools/test_connection.md) |

**Next:** [Advanced Configuration](#for-advanced-users)

---

### For Advanced Users

**Goal: Customize and optimize**

#### Configuration
- [Advanced MCP Configuration](mcp/mcp_server_user_guide.md)
- [Environment Variables](mcp_quick_start.md#configuration-options)
- [Service Config Files](mcp_quick_start.md#advanced-mcp-server-configuration)

#### Performance Optimization
- [Incremental Catalog Guide](incremental_catalog_guide.md) - 10-20x faster refreshes
- [Caching Strategies](api/tools/profile_table.md#caching-behavior)
- [Query Optimization](api/tools/execute_query.md#performance-tips)

#### Security Hardening
- [Security Guide](security.md) - Complete security reference
- [SQL Injection Protection](security.md#sql-injection-protection)
- [Permission Requirements](security.md#permission-requirements)

#### Architecture & Design
- [Service Layer Architecture](architecture.md)
- [MCP Server Architecture](mcp/mcp_architecture.md)
- [Technical Implementation Guide](mcp/mcp_server_technical_guide.md)

**Next:** [Troubleshooting](#troubleshooting-quick-reference)

---

## First Steps Tutorial

### Step 1: Verify Installation

```bash
# Check version
python -c "from snowcli_tools import __version__; print(__version__)"
# Expected: 1.10.0
```

### Step 2: Test Connection

In your AI assistant:
```
Can you test the Snowflake connection?
```

Expected tool usage: `test_connection()`

### Step 3: Explore Your Database

```
What tables are in my database?
```

Expected tool usage: `execute_query(statement="SHOW TABLES")`

### Step 4: Profile a Table

```
Profile the CUSTOMERS table
```

Expected tool usage: `profile_table(table_name="CUSTOMERS")`

**Success!** You're now ready to use SnowCLI Tools. Try the [workflows](#for-workflow-users) next.

---

## Troubleshooting Quick Reference

### MCP Server Not Showing Up
**Symptom:** AI assistant doesn't recognize Snowflake commands

**Quick Fix:**
1. Verify `.mcp.json` exists: `cat .mcp.json | python -m json.tool`
2. Check Python path: `which python`
3. Restart AI assistant completely
4. **[Full Guide →](troubleshooting.md#mcp-server-not-showing-up)**

---

### Snowflake Connection Failed
**Symptom:** "Profile not found" or "Connection timeout"

**Quick Fix:**
1. List profiles: `snow connection list`
2. Test profile: `snow connection test --connection "my-profile"`
3. Set environment: `export SNOWFLAKE_PROFILE=my-profile`
4. **[Full Guide →](troubleshooting.md#connection-issues)**

---

### Permission Denied
**Symptom:** "Access denied" or "Insufficient privileges"

**Quick Fix:**
1. Verify warehouse access: `USAGE` permission
2. Check database access: `SELECT` on `INFORMATION_SCHEMA`
3. Contact Snowflake admin for read permissions
4. **[Full Guide →](troubleshooting.md#permission-issues)**

---

### Tool Not Found
**Symptom:** Tool name not recognized by AI assistant

**Quick Fix:**
1. Check tool name spelling (case-sensitive)
2. Verify v1.10.0: Old tool names may not work
3. See [tool migration](#version-migration-guide)
4. **[Full Guide →](troubleshooting.md#tool-not-found)**

**[Complete Troubleshooting Guide →](troubleshooting.md)**

---

## Version Migration Guide

### Migrating from v1.9.0 → v1.10.0

#### Tool Renamed
```python
# OLD (v1.9.0)
discover_table_purpose(table_name="CUSTOMERS")

# NEW (v1.10.0)
profile_table(table_name="CUSTOMERS")
```

#### Simplified Parameters
```python
# OLD: depth parameter
discover_table_purpose(table_name="CUSTOMERS", depth="deep")

# NEW: Boolean flags
profile_table(
    table_name="CUSTOMERS",
    include_ai_analysis=True,
    include_relationships=True
)
```

#### Parameter Mapping
| v1.9.0 | v1.10.0 |
|--------|---------|
| `depth="quick"` | `include_ai_analysis=False, include_relationships=False` |
| `depth="standard"` | `include_ai_analysis=True, include_relationships=False` (default) |
| `depth="deep"` | `include_ai_analysis=True, include_relationships=True` |

**[Complete Migration Guide →](../CHANGELOG.md#unreleased---v1100)**

---

## Documentation Updates

This documentation was last updated for **v1.10.0** on **2025-10-06**.

### What's New in v1.10.0
- 🔄 Tool renamed: `discover_table_purpose` → `profile_table`
- ✨ Simplified parameters: Boolean flags instead of depth enum
- 🚀 Automatic caching with DDL-based invalidation
- 📉 40% reduction in MCP token usage
- 🔒 Enhanced security: Read-only by default, SQL injection protection
- ⏱️ Query timeout controls (default 120s, configurable)

**[Full Changelog →](../CHANGELOG.md)**

---

## Contributing to Documentation

Found an error? Have a suggestion?

1. **File an Issue:** [GitHub Issues](https://github.com/Evan-Kim2028/snowcli-tools/issues)
2. **Submit a PR:** Documentation is in `/docs` directory
3. **Ask Questions:** Use GitHub Discussions

---

## Documentation Structure

```
/docs
├── INDEX.md (you are here)
├── mcp_quick_start.md
├── getting-started.md
├── security.md
├── troubleshooting.md
├── workflows.md
├── architecture.md
├── features_overview.md
│
├── /api
│   ├── TOOLS_REFERENCE.md
│   ├── ERROR_CATALOG.md
│   └── /tools
│       ├── execute_query.md
│       ├── preview_table.md
│       ├── profile_table.md
│       ├── build_catalog.md
│       ├── get_catalog_summary.md
│       ├── query_lineage.md
│       ├── build_dependency_graph.md
│       ├── health_check.md
│       └── test_connection.md
│
├── /mcp
│   ├── mcp_architecture.md
│   ├── mcp_server_user_guide.md
│   └── mcp_server_technical_guide.md
│
├── /agentic_workflows
│   ├── README.md
│   └── prompt_engineering_guide.md
│
└── /advanced
    └── incremental_catalog_guide.md
```

---

## External Resources

### Official Links
- **GitHub Repository:** [Evan-Kim2028/snowcli-tools](https://github.com/Evan-Kim2028/snowcli-tools)
- **PyPI Package:** [snowcli-tools](https://pypi.org/project/snowcli-tools/)
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md)

### Community & Support
- **Issues:** Report bugs or request features
- **Discussions:** Ask questions, share workflows
- **Examples:** See `/examples` directory

### Related Projects
- **[Snowflake Labs MCP Server](https://github.com/Snowflake-Labs/mcp-servers)** - Official Snowflake MCP
- **[FastMCP](https://github.com/jlowin/fastmcp)** - MCP framework
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - MCP specification

---

## Quick Links by Task

| I Want To... | Documentation Link |
|-------------|--------------------|
| **Get started in 5 minutes** | [MCP Quick Start](mcp_quick_start.md) |
| **Understand all 9 tools** | [Tools Reference](api/TOOLS_REFERENCE.md) |
| **Profile unfamiliar tables** | [profile_table](api/tools/profile_table.md) |
| **Find PII in my database** | [PII Workflow](workflows.md#pii-detection) |
| **Trace data lineage** | [query_lineage](api/tools/query_lineage.md) |
| **Visualize architecture** | [build_dependency_graph](api/tools/build_dependency_graph.md) |
| **Troubleshoot connection issues** | [Troubleshooting](troubleshooting.md#connection-issues) |
| **Understand security features** | [Security Guide](security.md) |
| **Optimize performance** | [Incremental Catalog](incremental_catalog_guide.md) |
| **Configure advanced settings** | [MCP Advanced Config](mcp/mcp_server_user_guide.md) |

---

## Feedback

We'd love to hear from you! This documentation is continuously improved based on user feedback.

**Was this documentation helpful?**
- ✅ Yes: Star us on [GitHub](https://github.com/Evan-Kim2028/snowcli-tools)
- ❌ No: [Open an issue](https://github.com/Evan-Kim2028/snowcli-tools/issues) with suggestions

---

**Version:** 1.10.0
**Last Updated:** 2025-10-06
**Documentation Maintainer:** SnowCLI Tools Team

---

**Happy exploring your Snowflake data with AI assistance!** 🚀
