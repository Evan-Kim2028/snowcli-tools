# SNOWCLI-TOOLS

An enhanced Snowflake CLI toolkit with AI-powered MCP server integration. Transform your Snowflake data operations with automated cataloging, advanced lineage analysis, and seamless AI assistant connectivity.

[![PyPI version](https://badge.fury.io/py/snowcli-tools.svg)](https://pypi.org/project/snowcli-tools/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## 🚀 Key Features

### 📊 **Data Intelligence**
- **Automated Data Catalog**: Comprehensive metadata extraction from your Snowflake environment
- **Advanced Lineage Analysis**: Column-level lineage, cross-database tracking, and impact analysis
- **Dependency Mapping**: Visual object relationships and circular dependency detection
- **External Source Integration**: S3/Azure/GCS mapping and tracking

### 🤖 **AI Assistant Integration (MCP Server)**
- **Claude Code/VS Code/Cursor**: Direct AI assistant access to your Snowflake data
- **Natural Language Queries**: "Show me the schema of CUSTOMERS table" → Instant results
- **Real-time Health Monitoring**: Proactive diagnostics and configuration validation
- **Enhanced Profile Validation**: Clear error messages instead of confusing timeouts

### ⚡ **Performance & Reliability**
- **Parallel Query Execution**: Concurrent operations for faster bulk workloads
- **Circuit Breaker Pattern**: Fault-tolerant operations with intelligent failure handling
- **Modern Python Architecture**: 3.12+ features with performance optimization

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistants                          │
│          (Claude Code, VS Code, Cursor)                    │
├─────────────────────────────────────────────────────────────┤
│                   MCP Protocol Layer                       │
│    ┌─────────────────┐  ┌──────────────────┐              │
│    │  Health         │  │  Diagnostic      │              │
│    │  Monitoring     │  │  Tools           │              │
│    └─────────────────┘  └──────────────────┘              │
├─────────────────────────────────────────────────────────────┤
│              SNOWCLI-TOOLS Core Engine                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │  Data Catalog   │  │  Lineage         │  │  Parallel │ │
│  │  Builder        │  │  Analyzer        │  │  Executor │ │
│  └─────────────────┘  └──────────────────┘  └───────────┘ │
├─────────────────────────────────────────────────────────────┤
│                Snowflake CLI Integration                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │  Profile        │  │  Authentication  │  │  Session  │ │
│  │  Management     │  │  & Security      │  │  Handling │ │
│  └─────────────────┘  └──────────────────┘  └───────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Snowflake Data Cloud                   │
└─────────────────────────────────────────────────────────────┘
```

## 🏃‍♂️ Quick Start

### Installation
```bash
# Core CLI tools
pip install snowcli-tools

# With AI assistant integration
pip install "snowcli-tools[mcp]"
```

### Setup Snowflake Profile
```bash
# Create a connection profile (one-time setup)
snow connection add \
  --connection-name my-profile \
  --account YOUR_ACCOUNT \
  --user YOUR_USER \
  --authenticator SNOWFLAKE_JWT \
  --private-key /path/to/key.p8 \
  --warehouse YOUR_WAREHOUSE \
  --default
```

### Basic Operations
```bash
# Test connection
snowflake-cli query "SELECT CURRENT_VERSION()"

# Build data catalog
snowflake-cli catalog --database ANALYTICS --output ./catalog

# Generate dependency graph
snowflake-cli depgraph --database ANALYTICS --format dot

# Analyze lineage
snowflake-cli lineage ANALYTICS.CUSTOMERS --direction both --depth 3
```

### AI Assistant Integration
```bash
# Start MCP server for AI assistants
snowflake-cli mcp

# Add to your AI assistant's MCP configuration:
{
  "mcpServers": {
    "snowflake": {
      "command": "snowflake-cli",
      "args": ["mcp"],
      "env": {"SNOWFLAKE_PROFILE": "my-profile"}
    }
  }
}
```

## 🎯 Enhanced Profile Validation (v1.4.5+)

### Before vs After
**Before:** `❌ Connection timeout after 300 seconds`

**After:**
```bash
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: dev-profile, prod-profile
To fix this issue:
1. Set SNOWFLAKE_PROFILE environment variable
2. Or pass --profile <profile_name>
3. Or run 'snow connection add' to create a new profile
```

### New MCP Diagnostic Tools
- **`health_check`** - Comprehensive server health status
- **`check_profile_config`** - Profile validation and recommendations
- **`get_resource_status`** - Resource availability monitoring
- **`check_resource_dependencies`** - Dependency validation

## 🛠️ Core CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `query` | Execute SQL queries | `snowflake-cli query "SELECT * FROM CUSTOMERS LIMIT 10"` |
| `catalog` | Build metadata catalog | `snowflake-cli catalog --database SALES --include-ddl` |
| `lineage` | Analyze data lineage | `snowflake-cli lineage SALES.ORDERS --direction upstream` |
| `depgraph` | Generate dependency graph | `snowflake-cli depgraph --account --format json` |
| `mcp` | Start MCP server | `snowflake-cli mcp --transport stdio` |

## 🔧 Advanced Features

### Column-Level Lineage
Track data transformations at granular column level with confidence scoring:
```bash
snowflake-cli lineage ANALYTICS.USER_METRICS --column-level --format html
```

### Cross-Database Analysis
Unified lineage across multiple databases:
```bash
snowflake-cli catalog --account-scope
snowflake-cli lineage --cross-database SALES.ORDERS
```

### Impact Analysis
Understand change impact before implementation:
```bash
snowflake-cli lineage CORE.DIM_CUSTOMER --impact-analysis --depth 5
```

### External Source Mapping
Track S3/Azure/GCS dependencies:
```bash
snowflake-cli catalog --include-external-sources
```

## 📚 Documentation

- **[Profile Troubleshooting Guide](docs/profile_troubleshooting_guide.md)** - Comprehensive troubleshooting
- **[Profile Validation Quick-Start](docs/profile_validation_quickstart.md)** - Step-by-step setup
- **[MCP Diagnostic Tools Reference](docs/mcp_diagnostic_tools.md)** - Health monitoring API
- **[MCP Server User Guide](docs/mcp_server_user_guide.md)** - AI assistant integration
- **[Features Overview](docs/features_overview.md)** - Complete feature documentation

## 🏗️ Development

### Local Development
```bash
git clone https://github.com/Evan-Kim2028/snowcli-tools.git
cd snowcli-tools
uv sync
uv add snowflake-cli
```

### Testing
```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/snowcli_tools

# Lint and format
uv run ruff check
uv run ruff format
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **PyPI**: https://pypi.org/project/snowcli-tools/
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Evan-Kim2028/snowcli-tools/issues)
- **Snowflake CLI**: https://docs.snowflake.com/en/user-guide/snowcli

---

⭐ **Star this repo** if you find it useful! Questions? Check our [documentation](docs/) or [open an issue](https://github.com/Evan-Kim2028/snowcli-tools/issues).
