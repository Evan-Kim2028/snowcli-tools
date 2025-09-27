# MCP Server User Guide

## Overview

The MCP (Model Context Protocol) server for snowcli-tools provides AI assistants like VS Code, Cursor, and Claude Code with direct access to your Snowflake data and metadata. This enables natural language interactions with your Snowflake database through AI assistants.

## Quick Start

### Prerequisites

1. **Install with MCP Support**: The MCP server requires the optional `mcp` extra:
   ```bash
   # Install with MCP support
   uv add snowcli-tools[mcp]
   ```

   If you get an ImportError when running `snowflake-cli mcp`, install the extra as shown above.

2. **Configure Snowflake Connection**: Set up a Snowflake CLI connection profile
   ```bash
   uv run snow connection add \
     --connection-name my-profile \
     --account your-account \
     --user your-username \
     --private-key /path/to/your/rsa_key.p8 \
     --warehouse your-warehouse \
     --database your-database \
     --schema your-schema \
     --default
   ```

2. **Set Environment Variable** (optional):
   ```bash
   export SNOWFLAKE_PROFILE=my-profile
   ```

### Starting the MCP Server

#### Option 1: CLI Command (Recommended)
```bash
uv run snowflake-cli mcp
```

#### Option 2: Direct Python Example
```bash
uv run python examples/run_mcp_server.py
```

The server will display usage information and available tools. Press `Ctrl+C` to stop the server.

## Available Tools

The MCP server exposes the following tools to AI assistants:

### Core Data Tools
- **`execute_query`** - Execute SQL queries against Snowflake
  - Parameters: `query`, `warehouse`, `database`, `schema`, `role`
  - Returns: Query results as JSON

- **`preview_table`** - Preview table contents
  - Parameters: `table_name`, `limit`, `warehouse`, `database`, `schema`, `role`
  - Returns: Table preview data

### Catalog and Metadata Tools
- **`build_catalog`** - Generate comprehensive data catalogs
  - Parameters: `output_dir`, `database`, `account`, `format`, `include_ddl`
  - Returns: Catalog metadata summary

- **`get_catalog_summary`** - Retrieve existing catalog summaries
  - Parameters: `catalog_dir`
  - Returns: Catalog statistics and metadata

### Analysis Tools
- **`query_lineage`** - Analyze data lineage and dependencies
  - Parameters: `object_name`, `direction`, `depth`, `format`, `catalog_dir`, `cache_dir`
  - Returns: Lineage graph in text/JSON/HTML format

- **`build_dependency_graph`** - Create object dependency graphs
  - Parameters: `database`, `schema`, `account`, `format`
  - Returns: Dependency graph in JSON or DOT format

### Health Monitoring & Diagnostic Tools (v1.4.4+)
- **`health_check`** - Comprehensive server health status
  - Parameters: None
  - Returns: Detailed health status including profile, connection, and resource availability

- **`check_profile_config`** - Validate and diagnose profile configuration
  - Parameters: None
  - Returns: Profile validation status, available profiles, and configuration recommendations

- **`get_resource_status`** - Check MCP resource availability
  - Parameters: None
  - Returns: Status of all MCP resources and their dependencies

- **`check_resource_dependencies`** - Check specific resource dependencies
  - Parameters: `resource_name` (optional)
  - Returns: Dependency status and recommendations for specific resources

### Utility Tools
- **`test_connection`** - Test Snowflake connection
  - Parameters: None
  - Returns: Connection status

## Configuration

### VS Code / Cursor Configuration

Create or update your MCP configuration file (usually `~/.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowcli-tools/project",
      "env": {
        "SNOWFLAKE_PROFILE": "your-profile-name"
      }
    }
  }
}
```

For additional configuration examples, see `examples/mcp_config_example.json` and `examples/mcp_config_alternatives.json` in this repository.

### Claude Code Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowcli-tools/project",
      "env": {
        "SNOWFLAKE_PROFILE": "your-profile-name"
      }
    }
  }
}
```

### Environment Variables

The MCP server respects the following environment variables:

- `SNOWFLAKE_PROFILE` - Snowflake connection profile to use
- `SNOWFLAKE_WAREHOUSE` - Default warehouse
- `SNOWFLAKE_DATABASE` - Default database
- `SNOWFLAKE_SCHEMA` - Default schema
- `SNOWFLAKE_ROLE` - Default role

## Profile Configuration & Troubleshooting

### Profile Validation (v1.4.4+)

The MCP server now includes robust profile validation that catches configuration issues at startup:

#### ✅ What Works Now
- **Early validation**: Profile issues detected before server starts
- **Clear error messages**: No more confusing timeout errors
- **Actionable guidance**: Specific steps to fix configuration problems
- **Real-time diagnostics**: New MCP tools for ongoing health monitoring
- **MCP-compliant error responses**: Structured error format following JSON-RPC 2.0 standards

#### Common Error Scenarios

**Profile Not Found Error:**
```bash
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: evan-oauth, mystenlabs-keypair
To fix this issue:
1. Set SNOWFLAKE_PROFILE environment variable to one of the available profiles
2. Or pass --profile <profile_name> when starting the server
3. Or run 'snow connection add' to create a new profile
```

**No Profiles Configured:**
```bash
❌ Snowflake profile validation failed
Error: No Snowflake profiles found. Please run 'snow connection add' to create a profile.
Expected config file at: ~/Library/Application Support/snowflake/config.toml
```

### Profile Management

**Check your current configuration:**
```bash
# List all available profiles
snow connection list

# Check MCP server profile status
snowflake-cli mcp --help  # Shows current profile in use

# Validate specific profile
snow connection test --connection-name my-profile
```

**Create a new profile:**
```bash
# Interactive setup
snow connection add

# Non-interactive setup
snow connection add \
  --connection-name my-new-profile \
  --account your-account \
  --user your-username \
  --authenticator SNOWFLAKE_JWT \
  --private-key /path/to/rsa_key.p8 \
  --warehouse your-warehouse \
  --database your-database \
  --schema your-schema \
  --default
```

**Set environment profile:**
```bash
# Temporary (current session)
export SNOWFLAKE_PROFILE=my-profile

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export SNOWFLAKE_PROFILE=my-profile' >> ~/.bashrc
```

### Troubleshooting Connection Issues

**Server won't start:**
1. Check available profiles: `snow connection list`
2. Verify profile exists: `snow connection test --connection-name <profile>`
3. Set correct profile: `export SNOWFLAKE_PROFILE=<existing-profile>`

**Connection timeouts:**
1. Test profile directly: `snow connection test --connection-name <profile>`
2. Check network connectivity
3. Verify credentials haven't expired

**Permission errors:**
1. Verify role has necessary permissions
2. Check warehouse/database/schema access
3. Test with different role if available

### Health Monitoring & Diagnostics (v1.4.4+)

The enhanced MCP server provides comprehensive health monitoring through new diagnostic tools:

#### Real-Time Health Checks

**Check overall server health:**
```
AI: "Check the health of the MCP server"
```

Response includes:
- Profile validation status
- Connection health
- Resource availability
- Component-specific diagnostics

**Profile configuration diagnostics:**
```
AI: "Check my Snowflake profile configuration"
```

Response includes:
- Current profile status
- Available profiles list
- Configuration recommendations
- Troubleshooting guidance

**Resource dependency checking:**
```
AI: "Check if all MCP resources are available"
AI: "Check the dependencies for the catalog resource"
```

#### Health Check Response Format

```json
{
  "status": "healthy",
  "timestamp": 1673524800.0,
  "server_uptime": 3600.5,
  "components": {
    "profile": {
      "status": "healthy",
      "profile_name": "dev",
      "is_valid": true,
      "available_profiles": ["dev", "prod"],
      "last_validated": 1673524500.0
    },
    "connection": {
      "status": "healthy",
      "last_tested": 1673524700.0
    },
    "resources": {
      "status": "healthy",
      "available": {
        "catalog": true,
        "lineage": true,
        "cortex_search": true
      },
      "dependencies_met": true
    }
  }
}
```

## Usage Examples

Once configured, AI assistants can help you:

### Health Monitoring & Diagnostics
- "Check the MCP server health status"
- "Validate my Snowflake profile configuration"
- "Are all MCP resources available?"
- "Diagnose any connection issues"
- "What profiles are available on this system?"

### Data Exploration
- "Show me the schema of the CUSTOMERS table"
- "Preview the first 100 rows from the SALES table"
- "What are the most recent transactions?"

### Catalog Management
- "Build a catalog of all tables in the SALES database"
- "Generate a dependency graph for my data warehouse"
- "Show me what objects depend on the USER_ACTIVITY view"

### Lineage Analysis
- "What's the lineage for the USER_ACTIVITY view?"
- "Show me what depends on the CUSTOMER_DIMENSION table"
- "Trace the data flow from raw tables to final reports"

### Query Execution
- "Execute this SQL query and show me the results"
- "Run a count of records in the ORDERS table"
- "Show me the average order value by customer segment"

## Troubleshooting

### Connection Issues
1. Verify your Snowflake CLI connection works:
   ```bash
   uv run snowflake-cli test
   ```

2. Check that your profile is configured correctly:
   ```bash
   uv run snow connection list
   ```

3. Ensure required environment variables are set or use CLI flags

### MCP Client Issues
1. **VS Code/Cursor**: Restart the editor after configuration changes
2. **Claude Code**: Reload your MCP settings
3. **Permission Errors**: Ensure the MCP server has access to your Snowflake credentials

### Performance Issues
- Use specific database/schema parameters to limit scan scope
- Set appropriate concurrency limits for large catalogs
- Use incremental catalog builds when possible

### Common Error Messages
- `"Object not found in lineage graph"` - Run `build_catalog` first
- `"Connection failed"` - Check your Snowflake CLI configuration
- `"Permission denied"` - Ensure your role has necessary privileges

## Security Considerations

- The MCP server uses the same authentication as your Snowflake CLI
- No credentials are stored in the MCP server configuration
- All database access is controlled by your Snowflake role permissions
- The server only exposes tools you've explicitly configured

## Support

For issues with the MCP server:
1. Check the troubleshooting section above
2. Verify your Snowflake CLI connection works independently
3. Review the MCP client logs for detailed error messages
4. Check that you're using compatible versions of all components

The MCP server is designed to be a thin wrapper around your existing snowcli-tools functionality, so most issues can be diagnosed by testing the underlying CLI commands first.
