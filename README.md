# Nanuk MCP - Snowflake MCP Server

> 🐻‍❄️ **AI-first Snowflake operations via Model Context Protocol**

Nanuk (Inuit for "polar bear") enhances the official [Snowflake Labs MCP](https://github.com/Snowflake-Labs/mcp) with more features for agentic native workflows.

## ✨ Features

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

## Installation

### For End Users (Recommended)

**Install from PyPI for stable releases**:
```bash
uv pip install nanuk-mcp
```

## ⚡ Quickstart

```bash
# 1. Install (1 minute)
uv pip install nanuk-mcp snowflake-cli-labs

# 2. Create Snowflake profile (2 minutes)
snow connection add \
  --connection-name "quickstart" \
  --account "<your-account>.<region>" \
  --user "<your-username>" \
  --password \
  --warehouse "<your-warehouse>"
# Enter password when prompted

# 3. Configure your MCP client (1 minute)
# Add to your MCP client config (e.g., Claude Code, Continue, Zed):
{
  "mcpServers": {
    "snowflake": {
      "command": "nanuk-mcp",
      "args": ["--profile", "quickstart"]
    }
  }
}

# 4. Test it! (1 minute)
# In your AI assistant, ask:
# "Show me my Snowflake databases"
```

**Success!** 🎉 Your AI can now query Snowflake.

**New to Snowflake?** See [Parameter Guide](docs/getting-started.md#snowflake-parameters) for help finding your account identifier and understanding which parameters are required.

---

## Complete Setup Guide key-pair authentication

For production with key-pair authentication:

```bash
# 1. Set up your Snowflake profile
snow connection add --connection-name "my-profile" \
  --account "your-account.region" --user "your-username" \
  --private-key-file "/path/to/key.p8" --database "DB" --warehouse "WH"

# 2. Start MCP server
SNOWFLAKE_PROFILE=my-profile nanuk-mcp

# Expected output:
# ✓ MCP server started successfully
# ✓ Listening on stdio for MCP requests
```

See [Getting Started Guide](docs/getting-started.md) for detailed setup instructions.

### MCP Server (MCP-Only Interface)

| Task | Command | Notes |
|------|---------|-------|
| Start MCP server | `nanuk-mcp` | For AI assistant integration |
| Start with profile | `nanuk-mcp --profile PROF` | Specify profile explicitly |
| Configure | `nanuk-mcp --configure` | Interactive setup |

> 🐻‍❄️ **MCP-Only Architecture**
> Nanuk is MCP-only. All functionality is available through MCP tools.

**Profile Selection Options**:
- **Command flag**: `nanuk-mcp --profile PROFILE_NAME` (explicit)
- **Environment variable**: `export SNOWFLAKE_PROFILE=PROFILE_NAME` (session)
- **Default profile**: Set with `snow connection set-default PROFILE_NAME` (implicit)


## Available MCP Tools

### Nanuk MCP Tools
- `execute_query` - Execute SQL queries with safety checks
- `preview_table` - Preview table contents
- `build_catalog` - Build metadata catalog
- `get_catalog_summary` - Get catalog overview
- `query_lineage` - Query data lineage
- `build_dependency_graph` - Build dependency graph
- `test_connection` - Test Snowflake connection
- `health_check` - Get system health status

### Upstream Snowflake Labs MCP Tools
Nanuk MCP also provides access to all tools from the [official Snowflake Labs MCP](https://github.com/Snowflake-Labs/mcp), including Cortex AI and object management tools.

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
