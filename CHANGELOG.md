# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.3] - 2025-09-26

### Added
- Session management helpers that snapshot and restore Snowflake context so MCP
  overrides stay scoped to a single tool call.
- `--enable-cli-bridge` flag to optionally expose the legacy `snow` CLI bridge
  tool; the FastMCP server defaults to the in-process connector tools.
- `local_sf_test/` smoke harness that fetches the latest rows from
  `object_parquet2` for visual verification.

### Changed
- MCP argument parsing now treats missing defaults as `None`, preventing
  help-string values from becoming accidental overrides.
- Snowcli MCP tools reuse the official `SnowflakeService` connection under a
  scoped lock rather than opening ad-hoc sessions.
- Documentation updated with the new flag, session model, and smoke-test
  instructions.

## [1.3.0] - 2024-09-24

### Added
- **MCP (Model Context Protocol) Server Support**: Complete integration with AI assistants
  - New `snowflake-cli mcp` command to run MCP server
  - 7 MCP tools: execute_query, preview_table, build_catalog, query_lineage, build_dependency_graph, test_connection, get_catalog_summary
  - Optional dependency installation via `pip install snowcli-tools[mcp]`
  - stdio transport with JSON-RPC 2.0 protocol
  - Compatible with VS Code, Cursor, Claude Code, and other MCP clients

- **Comprehensive MCP Documentation**
  - `/docs/mcp/` directory with technical and user guides
  - ASCII-based architecture diagrams for GitHub compatibility
  - Complete setup and integration instructions
  - Real-world DeFi sample dataset examples

- **Sample Data Infrastructure**
  - `/examples/sample_data/` with production DeFi pipeline DDL
  - `dex_trades_stable` table as primary example (224M+ records)
  - Automated setup script for sample dataset installation
  - Complete database structure for DEX trading analytics

- **Enhanced Lineage Analysis**
  - Improved partial object lookup for lineage queries
  - Better error handling for missing objects
  - HTML visualization support for lineage graphs
  - Support for task objects in lineage traversal

### Changed
- Updated all documentation to use real DeFi examples instead of generic placeholders
- Moved MCP configuration to examples folder as template
- Enhanced README with MCP installation and usage instructions
- Improved error messages and user feedback across MCP tools

### Fixed
- Large file handling in git repository (removed oversized lineage_graph.json)
- Pre-commit hook compliance (formatting, imports, trailing whitespace)
- Unused variable warnings in MCP server code

### Technical Details
- MCP server runs as async stdio server using `mcp.server.stdio`
- Integrates with existing SnowCLI and LineageQueryService infrastructure
- Supports all existing snowcli-tools functionality through MCP protocol
- Maintains backward compatibility with CLI usage

## [1.2.x] - Previous Versions
- Core lineage analysis and catalog building functionality
- Dependency graph generation
- Snowflake CLI integration
- Basic documentation and examples
