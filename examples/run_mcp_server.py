#!/usr/bin/env python3
"""Example: Start the MCP server for AI assistant integration.

This example demonstrates how to start the MCP (Model Context Protocol) server that
provides AI assistants with direct access to your Snowflake data and metadata.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that enables AI assistants to
securely interact with external data sources and tools. It provides a structured way
for AI models to:
- Execute queries and retrieve data
- Access metadata and documentation
- Perform analysis and transformations
- All through a secure, well-defined protocol

## Architecture Overview

    ┌─────────────────┐         ┌──────────────────┐
    │   AI Assistant  │ <-----> │   MCP Server     │
    │ (VS Code, etc.) │  stdio  │ (this program)   │
    └─────────────────┘         └──────────────────┘
                                        │
                                        ▼
                                ┌──────────────────┐
                                │  Snowflake CLI   │
                                │   Connection     │
                                └──────────────────┘
                                        │
                                        ▼
                                ┌──────────────────┐
                                │    Snowflake     │
                                │    Database      │
                                └──────────────────┘

## Installation

The MCP server is an OPTIONAL feature that requires additional dependencies:

    # Install with MCP support
    pip install snowcli-tools[mcp]

    # Or with uv
    uv add snowcli-tools[mcp]

Without the [mcp] extra, the core CLI tools work normally, but MCP server
functionality will not be available.

## Setup for Examples

Before using MCP with the examples, set up the sample dataset:

    # Set up the DeFi sample dataset
    uv run python examples/sample_data/setup_sample_data.py

    # Build a catalog for MCP to work with
    uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -o ./sample_data_catalog

## Usage

### Starting the Server

    # Option 1: Use the CLI command (recommended)
    uv run snowflake-cli mcp

    # Option 2: Run this example directly
    uv run python examples/run_mcp_server.py

### Available Tools

The MCP server exposes these tools to AI assistants:

1. **execute_query**: Execute SQL queries with full context control
   - Params: query, warehouse, database, schema, role
   - Returns: JSON query results

2. **preview_table**: Quick preview of table data
   - Params: table_name, limit (default 100)
   - Returns: Sample rows from the table

3. **build_catalog**: Generate comprehensive data catalogs
   - Params: output_dir, database, account scope, format, include_ddl
   - Returns: Catalog metadata and statistics

4. **query_lineage**: Analyze data lineage relationships
   - Params: object_name, direction (upstream/downstream/both), depth
   - Returns: Lineage graph showing dependencies

5. **build_dependency_graph**: Create object dependency visualizations
   - Params: database, schema, account scope, format (json/dot)
   - Returns: Dependency graph data

6. **test_connection**: Verify Snowflake connectivity
   - Params: None
   - Returns: Connection status

7. **get_catalog_summary**: Retrieve existing catalog statistics
   - Params: catalog_dir
   - Returns: Summary of cataloged objects

## Prerequisites

1. **Snowflake CLI Connection**: Configure a connection profile
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

2. **Environment Variable** (optional):
   ```bash
   export SNOWFLAKE_PROFILE=my-profile
   ```

## Integration Examples

### VS Code / Cursor
Add to your MCP configuration (~/.vscode/mcp.json):
```json
{
  "mcpServers": {
    "snowflake": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/path/to/snowcli-tools"
    }
  }
}
```

### Claude Code
Configure in Claude Code settings to enable natural language SQL queries.

## Sample Dataset Examples

Once configured, try these natural language queries with the sample DeFi dataset:

### Data Discovery
- "Show me the schema of the main DEX trades table"
- "What columns does DEX_TRADES_STABLE have?"
- "Describe the COIN_INFO dynamic table"
- "What are the different schemas in DEFI_SAMPLE_DB?"

### Lineage Analysis
- "What feeds into the BTC analytics table?"
- "Show me the lineage for FILTERED_DEX_TRADES_VIEW"
- "What tables depend on COIN_INFO?"
- "How does the DEX trades data flow through the pipeline?"

### Query Execution
- "Execute a query to show the top 10 trading protocols by volume"
- "Run a query to count total trades per protocol"
- "Preview the first 100 rows of DEX_TRADES_STABLE"
- "Show me sample data from the COIN_INFO table"

### Catalog Operations
- "Build a catalog for the DeFi sample database"
- "Generate a dependency graph for DEFI_SAMPLE_DB"
- "Create lineage analysis for the analytics layer"

## Technical Details

- **Protocol**: MCP over stdio (standard input/output)
- **Transport**: JSON-RPC 2.0 messages
- **Concurrency**: Async/await pattern for non-blocking operations
- **Error Handling**: Structured exceptions with detailed messages
- **Security**: Leverages Snowflake CLI's secure authentication

For more details, see:
- docs/mcp_server_user_guide.md - User documentation
- docs/mcp_server_technical_guide.md - Technical implementation details
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def print_usage_info():
    """Print information about how to use the MCP server."""
    print("🚀 Snowflake MCP Server Example")
    print("=" * 50)
    print()
    print("This example demonstrates the MCP (Model Context Protocol) server that")
    print("enables AI assistants to interact with the sample DeFi dataset.")
    print()
    print("What MCP Provides:")
    print("• Structured protocol for AI-to-database communication")
    print("• Secure access through existing Snowflake CLI authentication")
    print("• Tool-based interface for queries, analysis, and metadata")
    print()
    print("Available MCP Tools:")
    print("• execute_query      - Run SQL queries against Snowflake")
    print("• preview_table      - Preview table contents (default 100 rows)")
    print("• build_catalog      - Generate comprehensive data catalogs")
    print("• query_lineage      - Analyze upstream/downstream dependencies")
    print("• build_dependency_graph - Create object dependency graphs")
    print("• test_connection    - Verify Snowflake connectivity")
    print("• get_catalog_summary - Retrieve catalog statistics")
    print()
    print("Sample Dataset Objects:")
    print("• DEX_TRADES_STABLE - Main fact table (224M+ DEX trades)")
    print("• COIN_INFO - Dynamic table with cryptocurrency metadata")
    print("• FILTERED_DEX_TRADES_VIEW - Business logic for user-initiated trades")
    print("• BTC_DEX_TRADES_USD_DT - BTC-focused analytics with USD pricing")
    print()
    print("Integration Options:")
    print("1. VS Code/Cursor: Configure in MCP settings")
    print("2. Claude Code: Add to MCP configuration")
    print("3. Other MCP clients: Use stdio transport protocol")
    print()
    print("Setup First:")
    print("  uv run python examples/sample_data/setup_sample_data.py")
    print("  uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -o ./sample_data_catalog")
    print()
    print("Note: MCP server requires stdio interaction with AI assistants.")
    print("Press Ctrl+C to stop the server when running interactively.")
    print()


async def main():
    """Start the MCP server."""
    print_usage_info()

    print("⚠️  Note: This example shows usage information.")
    print("💡 To actually start the MCP server, use:")
    print("   uv run snowflake-cli mcp")
    print()
    print("The MCP server requires stdio interaction with AI assistants.")
    print("This example cannot run the server directly in a terminal.")
    print()
    print("For more information, see the MCP Server Integration section in README.md")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
