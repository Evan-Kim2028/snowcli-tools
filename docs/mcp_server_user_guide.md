# MCP Server User Guide

## Overview

The MCP (Model Context Protocol) server for snowcli-tools provides AI assistants like VS Code, Cursor, and Claude Code with direct access to your Snowflake data and metadata. This enables natural language interactions with your Snowflake database through AI assistants.

## Quick Start

### Prerequisites

1. **Configure Snowflake Connection**: Set up a Snowflake CLI connection profile
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
      "cwd": "/path/to/your/snowflake_connector_py"
    }
  }
}
```

### Claude Code Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcp": {
    "snowflake-cli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/your/snowflake_connector_py"
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

## Usage Examples

Once configured, AI assistants can help you:

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
