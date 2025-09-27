# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.4] - 2025-09-27

### Added
- **🎯 Enhanced Profile Validation System**: Revolutionary improvement to user experience
  - Startup profile validation that catches configuration issues immediately
  - Clear, actionable error messages instead of confusing timeout errors
  - Modern Python 3.12+ implementation with performance caching
  - Structured error responses following MCP JSON-RPC 2.0 standards
- **🏥 Comprehensive Health Monitoring**: New diagnostic tools for MCP server
  - `health_check`: Real-time server health status with component details
  - `check_profile_config`: Profile validation and configuration recommendations
  - `get_resource_status`: Resource availability and dependency checking
  - `check_resource_dependencies`: Specific resource dependency validation
- **🔧 Advanced Error Handling Infrastructure**:
  - Circuit breaker pattern for fault-tolerant Snowflake operations
  - Comprehensive error categorization (Connection, Permission, Timeout, Configuration)
  - `ProfileConfigurationError` with rich context and available profiles
  - MCP-compliant error codes (-32001 to -32005) with structured data
- **📚 Comprehensive Documentation Suite**:
  - Profile Troubleshooting Guide with before/after comparisons
  - Profile Validation Quick-Start Guide with step-by-step setup
  - MCP Diagnostic Tools Reference with API documentation
  - Enhanced user guides with v1.4.4+ features and examples
- **🔬 Extensive Testing Infrastructure**:
  - Robust service layer with health monitoring and safe execution patterns
  - Enhanced MCP server configuration examples with multiple setup options
  - Extensive test coverage for new reliability infrastructure (~80 new tests)

### Changed
- **🚀 User Experience Transformation**:
  - Profile validation errors now provide immediate, clear feedback
  - MCP server startup includes proactive profile validation
  - Error messages include specific available profiles and next steps
  - Documentation updated with practical troubleshooting examples
- **⚡ Performance Optimizations**:
  - Profile validation caching with `@functools.lru_cache`
  - mtime-based configuration file caching for efficiency
  - Modern Python 3.12+ patterns (match statements, union types)
- **📖 Documentation Enhancements**:
  - Updated README.md with comprehensive profile management section
  - Enhanced MCP server user guide with health monitoring capabilities
  - Features overview updated with v1.4.4+ improvements
  - Added cross-references between related documentation

### Fixed
- **🐛 Critical UX Issues**:
  - Eliminated misleading timeout errors for profile configuration problems
  - Fixed silent fallback to non-existent "default" profile
  - Resolved late error detection that confused users
  - Improved error messaging accessibility and clarity
- **🔧 Technical Improvements**:
  - Type annotation errors in circuit breaker and error handling modules
  - Code formatting consistency across all Python files
  - MCP configuration format and environment variable documentation
  - Import optimization and unused code removal

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
