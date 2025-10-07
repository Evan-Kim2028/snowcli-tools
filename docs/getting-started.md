# Getting Started with Nanuk MCP

> **Quick Start**: Set up your Snowflake profile → Install Nanuk MCP → Start using with your AI assistant

## Prerequisites

**Required**:
1. **Python 3.12+** with `uv` or pip package manager
   - Check: `python --version`
   - Install: https://www.python.org/downloads/

2. **Snowflake CLI** (Official package - for profile management)
   - Install: `pip install snowflake-cli-labs`
   - Check: `snow --version`
   - Docs: https://docs.snowflake.com/en/developer-guide/snowflake-cli/
   - Purpose: Manages Snowflake authentication profiles only

3. **Snowflake account** with appropriate permissions
   - Need: USAGE on warehouse/database/schema
   - Need: SELECT on INFORMATION_SCHEMA
   - Contact your Snowflake admin if unsure

4. **AI Assistant** that supports MCP (e.g., Claude Code, Cline, etc.)

## Step 1: Install Nanuk MCP

### Installation Methods

**Option 1: PyPI Installation (Recommended for most users)**
```bash
pip install nanuk-mcp
```

**Option 2: Development Installation (For contributors)**
```bash
# Clone and install the project
git clone https://github.com/Evan-Kim2028/nanuk-mcp
cd nanuk-mcp

# Install with uv (recommended)
uv sync
```

## Step 2: Set Up Your Snowflake Profile

**Critical**: Nanuk MCP uses Snowflake CLI profiles for authentication.

### Create a Snowflake Profile

```bash
# Create a new profile (interactive)
snow connection add

# Example with key-pair authentication
snow connection add \
  --connection-name my-profile \
  --account mycompany-prod.us-east-1 \
  --user alex.chen \
  --warehouse COMPUTE_WH \
  --database MY_DB \
  --schema PUBLIC \
  --private-key-file ~/.snowflake/key.pem
```

### Verify Your Profile

```bash
# List all profiles
snow connection list

# Test your connection
snow sql -q "SELECT CURRENT_VERSION()" --connection my-profile
```

## Step 3: Configure MCP Server

Add nanuk-mcp to your AI assistant's MCP configuration.

### Claude Code Configuration

Edit your Claude Code MCP settings (`~/.config/claude-code/mcp.json`):

```json
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/nanuk-mcp",
        "run",
        "nanuk-mcp"
      ],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**For PyPI installation**, use:
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

### Other MCP Clients

For other MCP-compatible clients, use similar configuration pointing to:
- **Command**: `nanuk-mcp` (PyPI) or `uv run nanuk-mcp` (dev)
- **Environment**: Set `SNOWFLAKE_PROFILE` to your profile name

## Step 4: Start Using MCP Tools

Once configured, interact with Nanuk MCP through your AI assistant:

### Example Prompts

```
"Test my Snowflake connection"
→ Uses: test_connection tool

"Build a catalog for MY_DATABASE"
→ Uses: build_catalog tool

"Show me lineage for USERS table"
→ Uses: query_lineage tool

"Execute this query: SELECT * FROM CUSTOMERS LIMIT 10"
→ Uses: execute_query tool

"Build a dependency graph for MY_DATABASE"
→ Uses: build_dependency_graph tool
```

## Available MCP Tools

| Tool Name | Description | Key Parameters |
|-----------|-------------|----------------|
| `test_connection` | Test Snowflake connection | profile (optional) |
| `build_catalog` | Build database catalog | database, output_dir |
| `query_lineage` | Analyze table lineage | object_name, direction, depth |
| `build_dependency_graph` | Generate dependency graph | database, format |
| `execute_query` | Execute SQL query | statement, output_format |
| `preview_table` | Preview table data | table_name, limit |
| `health_check` | Check MCP server health | - |
| `get_catalog_summary` | Get catalog statistics | catalog_dir |

## Advanced Configuration

### Environment Variables

```bash
# Set default Snowflake profile
export SNOWFLAKE_PROFILE=my-profile

# Set default catalog directory
export SNOWCLI_CATALOG_DIR=./my_catalog

# Set default lineage directory
export SNOWCLI_LINEAGE_DIR=./my_lineage
```

### Multiple Profiles

Switch between environments by changing the `SNOWFLAKE_PROFILE`:

```json
{
  "mcpServers": {
    "nanuk-dev": {
      "command": "nanuk-mcp",
      "env": {"SNOWFLAKE_PROFILE": "dev"}
    },
    "nanuk-prod": {
      "command": "nanuk-mcp",
      "env": {"SNOWFLAKE_PROFILE": "prod"}
    }
  }
}
```

## Troubleshooting

### MCP Server Won't Start

**Issue**: MCP server fails to start
**Solution**:
1. Verify Snowflake profile: `snow connection list`
2. Test connection: `snow sql -q "SELECT 1" --connection my-profile`
3. Check MCP configuration in your AI assistant settings
4. Review logs in your AI assistant

### Authentication Errors

**Issue**: "Authentication failed"
**Solution**:
1. Verify profile credentials are correct
2. Check private key file permissions (should be 600)
3. Ensure profile name matches `SNOWFLAKE_PROFILE` env var

### Tool Not Found

**Issue**: AI assistant can't find MCP tools
**Solution**:
1. Restart your AI assistant
2. Verify MCP server is configured correctly
3. Check command path in MCP configuration

## Next Steps

- 📖 [MCP Tools Reference](mcp/tools-reference.md) - Detailed tool documentation
- 🔧 [Configuration Guide](configuration.md) - Advanced settings
- 🐛 [Troubleshooting Guide](troubleshooting.md) - Common issues
- 📊 [Usage Examples](examples/) - Real-world examples

## Migrating from CLI?

If you were using the old CLI interface from snowcli-tools, see the [Migration Guide](migration-guide.md) for step-by-step instructions.

---

*Questions? Check our [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)*
