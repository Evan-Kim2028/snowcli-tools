# CLI to MCP Migration Guide

## Overview

The `nanuk` CLI command was removed in v2.0.0. All functionality is now available exclusively through the MCP server.

## Why Was CLI Removed?

- Package is named "nanuk-**mcp**" - MCP should be the only interface
- Reduced codebase by 40% (774 LOC removed)
- Eliminated user confusion about which interface to use
- Aligned with AI-first architecture

## Migration Path

### Command Mapping

All CLI functionality is available through MCP tools:

| Old CLI Command | New MCP Tool | Notes |
|-----------------|--------------|-------|
| `nanuk verify` | `test_connection` | Connection testing |
| `nanuk catalog -d DB` | `build_catalog` | Database cataloging |
| `nanuk lineage TABLE` | `query_lineage` | Lineage analysis |
| `nanuk depgraph` | `build_dependency_graph` | Dependency mapping |
| `nanuk query "SQL"` | `execute_query` | SQL execution |
| `nanuk profile TABLE` | `profile_table` | Table profiling |

### Using MCP Tools

**Option 1: Through AI Assistant (Recommended)**

Configure Claude Code or another MCP-compatible AI assistant:

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

Then use natural language:
- "Build a catalog for MY_DATABASE"
- "Show me lineage for ANALYTICS.CUSTOMERS"
- "Profile the table RAW.ORDERS"

**Option 2: Direct MCP Tool Calls**

For scripting or automation:

```bash
# Start MCP server
SNOWFLAKE_PROFILE=my-profile nanuk-mcp

# Use through MCP client or AI assistant
```

### Example Migrations

**Before (CLI)**:
```bash
#!/bin/bash
nanuk --profile prod catalog -d ANALYTICS_DB
nanuk --profile prod lineage ANALYTICS.CUSTOMERS
nanuk --profile prod query "SELECT COUNT(*) FROM users"
```

**After (MCP)**:
```bash
#!/bin/bash
export SNOWFLAKE_PROFILE=prod

# Configure AI assistant to use nanuk-mcp, then:
# - "Build catalog for ANALYTICS_DB"
# - "Show lineage for ANALYTICS.CUSTOMERS"
# - "Execute: SELECT COUNT(*) FROM users"
```

### CI/CD Updates

**GitHub Actions Example**:

**Before**:
```yaml
- name: Build Catalog
  run: nanuk --profile prod catalog -d MY_DB
```

**After**:
```yaml
- name: Build Catalog
  run: |
    export SNOWFLAKE_PROFILE=prod
    # Use MCP-compatible automation or AI assistant
```

## Advantages of MCP

- **AI Integration**: Works natively with Claude Code and other AI assistants
- **Standardized**: Uses Model Context Protocol standard
- **Modern**: Designed for AI-first workflows
- **Simpler**: One interface, less confusion
- **More Powerful**: AI can chain operations intelligently

## Need Help?

- 📖 [MCP Server User Guide](mcp/mcp_server_user_guide.md)
- 🔧 [Configuration Guide](configuration.md)
- 💬 [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
