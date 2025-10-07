# Nanuk MCP - Snowflake MCP Server

> 🐻‍❄️ **AI-first Snowflake operations via Model Context Protocol**

Nanuk (Inuit for "polar bear") brings powerful Snowflake data operations to your AI assistants through the Model Context Protocol (MCP).

## ✨ v2.0.0 Features

- 🛡️ **SQL Safety:** Blocks destructive operations (DELETE, DROP, TRUNCATE) with safe alternatives
- 🧠 **Intelligent Errors:** Compact mode (default) saves 70% tokens; verbose mode for debugging
- ⏱️ **Agent-Controlled Timeouts:** Configure query timeouts per-request (1-3600s)
- ✅ **MCP Protocol Compliant:** Standard exception-based error handling
- 🚀 **Zero Vendoring:** Imports from upstream, stays in sync

[📖 See Release Notes](./RELEASE_NOTES.md) for details.

[![PyPI version](https://badge.fury.io/py/nanuk-mcp.svg)](https://pypi.org/project/nanuk-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🔄 Migrating from snowcli-tools?

This package was formerly known as `snowcli-tools`. See the [Migration Guide](docs/migration-from-snowcli-tools.md) for step-by-step instructions.

**Quick migration:**
```bash
pip uninstall snowcli-tools
pip install nanuk-mcp
# Update imports: from snowcli_tools → from nanuk_mcp
```

---

## Installation

### For End Users (Recommended)

**Install from PyPI for stable releases**:
```bash
pip install nanuk-mcp
```

**When to use**: Production use, stable releases, most users

### For Developers

**Install from source for latest features**:
```bash
git clone https://github.com/Evan-Kim2028/nanuk-mcp.git
cd nanuk-mcp
uv sync
```

**When to use**: Testing new features, contributing, custom modifications

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete development setup.

## Quick Start

```bash
# 1. Set up your Snowflake profile
snow connection add --connection-name "my-profile" \
  --account "your-account.region" --user "your-username" \
  --private-key-file "/path/to/key.p8" --database "DB" --warehouse "WH"

# 2. Start MCP server for AI assistant integration
SNOWFLAKE_PROFILE=my-profile nanuk-mcp

# Expected output:
# ✓ MCP server started successfully
# ✓ Listening on stdio for MCP requests
```

## What is Nanuk?

Nanuk is a Model Context Protocol (MCP) server that provides AI assistants with powerful Snowflake operations:

- 🔍 **Query execution and data exploration**
- 📊 **Table profiling and statistics**
- 🔗 **Data lineage tracking**
- 📚 **Catalog building and metadata**
- ⚡ **Performance optimized for AI workflows**

## Core Features

### 📊 **Data Discovery & Analysis**
- **Automated Catalog**: Complete metadata extraction from databases, schemas, tables
- **Advanced Lineage**: Column-level lineage tracking with impact analysis
- **Dependency Mapping**: Visual object relationships and circular dependency detection
- **Table Profiling**: Statistical analysis and data quality insights

### 🔍 **Query Operations**
- **SQL Execution**: Run queries directly from AI assistants
- **Safety Validation**: Blocks destructive operations by default
- **Timeout Control**: Agent-controlled query timeouts (1-3600s)
- **Result Formatting**: Optimized output for AI consumption

### 🤖 **AI Assistant Integration**
- **MCP Protocol**: Standard Model Context Protocol support
- **Claude Code**: Native integration with Claude Code
- **Error Handling**: Compact (70% token savings) or verbose modes
- **Async Operations**: Non-blocking query execution

### 🛡️ **Safety & Reliability**
- **Destructive Operation Protection**: Prevents accidental data deletion
- **Circuit Breaker**: Automatic failover for resilience
- **Connection Pooling**: Efficient resource management
- **Error Recovery**: Graceful error handling with suggestions

## Command Quick Reference

### MCP Server (MCP-Only Interface)

| Task | Command | Notes |
|------|---------|-------|
| Start MCP server | `nanuk-mcp` | For AI assistant integration |
| Start with profile | `nanuk-mcp --profile PROF` | Specify profile explicitly |
| Configure | `nanuk-mcp --configure` | Interactive setup |

> 🐻‍❄️ **MCP-Only Architecture**
> Nanuk is MCP-only. All functionality is available through MCP tools.
> CLI interface was removed in v2.0.0. See [CLI Migration Guide](docs/cli-to-mcp-migration.md) if upgrading.

**Profile Selection Options**:
- **Command flag**: `nanuk-mcp --profile PROFILE_NAME` (explicit)
- **Environment variable**: `export SNOWFLAKE_PROFILE=PROFILE_NAME` (session)
- **Default profile**: Set with `snow connection set-default PROFILE_NAME` (implicit)

## MCP Integration

### Claude Code Integration

Add to your Claude Code configuration (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nanuk": {
      "command": "nanuk-mcp",
      "args": ["--profile", "my-profile"]
    }
  }
}
```

### Available MCP Tools

- `execute_query` - Execute SQL queries
- `preview_table` - Preview table contents
- `profile_table` - Get table statistics
- `build_catalog` - Build metadata catalog
- `get_catalog_summary` - Get catalog overview
- `query_lineage` - Query data lineage
- `build_dependency_graph` - Build dependency graph
- `test_connection` - Test Snowflake connection
- `health_check` - Get system health status

See [MCP Documentation](docs/mcp/mcp_server_user_guide.md) for details.

## Python API

```python
from nanuk_mcp import QueryService, CatalogService

# Execute query
query_service = QueryService(profile="my-profile")
result = query_service.execute("SELECT * FROM users LIMIT 10")

# Build catalog
catalog_service = CatalogService(profile="my-profile")
catalog = catalog_service.build_catalog(database="MY_DB")
```

## Documentation

- [Getting Started Guide](docs/getting-started.md)
- [MCP Server User Guide](docs/mcp/mcp_server_user_guide.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api/README.md)
- [Migration from snowcli-tools](docs/migration-from-snowcli-tools.md)
- [Contributing Guide](CONTRIBUTING.md)

## Examples

### Query Execution via MCP

```python
# AI assistant sends query via MCP
{
  "tool": "execute_query",
  "arguments": {
    "statement": "SELECT COUNT(*) FROM users WHERE created_at > CURRENT_DATE - 30",
    "timeout_seconds": 60
  }
}
```

### Table Profiling

```python
# Get table statistics
{
  "tool": "profile_table",
  "arguments": {
    "table_name": "MY_DATABASE.MY_SCHEMA.USERS"
  }
}
```

### Data Lineage

```python
# Query lineage for impact analysis
{
  "tool": "query_lineage",
  "arguments": {
    "object_name": "MY_TABLE",
    "direction": "both",
    "depth": 3
  }
}
```

## Why "Nanuk"?

- 🐻‍❄️ **Nanuk** (polar bear in Inuit) connects to Snowflake's arctic theme
- 🎯 **MCP-first**: Name reflects our focus on Model Context Protocol
- ✨ **Unique & memorable**: Stands out in the MCP ecosystem
- 🚀 **Future-proof**: Positions as the premier Snowflake MCP provider

## Troubleshooting

### Common Issues

**Issue**: "No module named 'nanuk_mcp'"
**Solution**: Ensure you've installed the package: `pip install nanuk-mcp`

**Issue**: "Command 'nanuk-mcp' not found"
**Solution**: Reinstall package or check PATH: `pip install --force-reinstall nanuk-mcp`

**Issue**: MCP server won't start
**Solution**: Check Snowflake profile is configured: `nanuk --profile PROF verify`

See [Troubleshooting Guide](docs/troubleshooting.md) for more solutions.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/Evan-Kim2028/nanuk-mcp.git
cd nanuk-mcp

# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Run linting
ruff check .
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 🐛 **Bug reports**: [Open an issue](https://github.com/Evan-Kim2028/nanuk-mcp/issues)
- 💬 **Questions**: [Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
- 📧 **Email**: ekcopersonal@gmail.com

## Acknowledgments

Built with:
- [Snowflake Connector for Python](https://github.com/snowflakedb/snowflake-connector-python)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [FastMCP](https://github.com/jlowin/fastmcp)

---

**🐻‍❄️ Nanuk MCP - Bringing Snowflake to your AI assistants**
