# SnowCLI Tools

> **Powerful Snowflake operations with AI assistant integration**

Transform your Snowflake data operations with automated cataloging, advanced lineage analysis, SQL safety validation, and seamless AI assistant connectivity through MCP (Model Context Protocol).

## ✨ v1.10.0 New Features - Discovery Assistant

- 🔍 **AI-Powered Table Discovery:** Automatically profile and document tables using Cortex Complete
- 📊 **Three Depth Modes:** quick (stats only), standard (+ AI analysis), deep (+ relationships)
- 🤖 **Smart Analysis:** 75%+ accuracy on table purpose, 95%+ PII detection
- 🔗 **Relationship Discovery:** Multi-strategy FK detection with confidence scoring
- 📝 **Rich Documentation:** Markdown data dictionaries with Mermaid ER diagrams
- ⚡ **Fast:** <5s for 1M row tables, batch discovery support
- 💰 **Cost Transparent:** Estimates shown for each discovery operation

```bash
# Discover and document a table with AI analysis
snowflake-cli discover CUSTOMERS --depth standard

# Batch discovery with relationship mapping
snowflake-cli discover CUSTOMERS,ORDERS,PRODUCTS --depth deep
```

## ✨ v1.7.0 New Features

- 🛡️ **SQL Safety:** Blocks destructive operations (DELETE, DROP, TRUNCATE) with safe alternatives
- 🧠 **Intelligent Errors:** Compact mode (default) saves 70% tokens; verbose mode for debugging
- ⏱️ **Agent-Controlled Timeouts:** Configure query timeouts per-request (1-3600s)
- ✅ **MCP Protocol Compliant:** Standard exception-based error handling
- 🚀 **Zero Vendoring:** Imports from upstream, stays in sync

[📖 See Release Notes](./RELEASE_NOTES.md) for details.

[![PyPI version](https://badge.fury.io/py/snowcli-tools.svg)](https://pypi.org/project/snowcli-tools/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Quick Start

```bash
# 1. Install SnowCLI Tools
pip install snowcli-tools

# 2. Set up your Snowflake profile
snow connection add --connection-name "my-profile" \
  --account "your-account.region" --user "your-username" \
  --private-key-file "/path/to/key.p8" --database "DB" --warehouse "WH"

# 3. Verify connection
snowflake-cli verify -p my-profile

# 4. Start exploring your data
snowflake-cli catalog -p my-profile
snowflake-cli lineage MY_TABLE -p my-profile

# 5. Enable AI assistant integration
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp
```

## Core Features

### 📊 **Data Discovery & Analysis**
- **Automated Catalog**: Complete metadata extraction from databases, schemas, tables
- **Advanced Lineage**: Column-level lineage tracking with impact analysis
- **Dependency Mapping**: Visual object relationships and circular dependency detection
- **External Integration**: S3/Azure/GCS source mapping

### 🤖 **AI Assistant Integration**
- **MCP Server**: Direct integration with Claude Code, VS Code, Cursor
- **Natural Language**: "Show me schema of CUSTOMERS" → instant results
- **Health Monitoring**: Real-time diagnostics and validation
- **Enhanced Profiles**: Clear error messages instead of timeouts

### ⚡ **Enterprise Ready**
- **Layered Security**: Built on Snowflake's official authentication
- **High Performance**: Parallel operations and connection pooling
- **Fault Tolerance**: Circuit breaker patterns for reliability
- **Modern Architecture**: Python 3.12+ with async support

## Architecture

SnowCLI Tools uses a **layered architecture** that combines official Snowflake tools with enhanced analytics:

```
┌─────────────────────────────────────┐
│     AI Assistants & Applications    │  ← Your workflows
├─────────────────────────────────────┤
│      SnowCLI Tools MCP Server       │  ← Enhanced analytics
│   (Catalog, Lineage, Dependencies)  │
├─────────────────────────────────────┤
│       Snowflake Labs MCP            │  ← Official foundation
│    (Auth, Connection, Security)     │
├─────────────────────────────────────┤
│        Snowflake Platform           │  ← Your data warehouse
└─────────────────────────────────────┘
```

**Key Benefits:**
- **🔐 Secure**: Leverages Snowflake's official authentication
- **🚀 Powerful**: Combines official tools with advanced analytics
- **🔗 Integrated**: Single MCP endpoint for AI assistants
- **📈 Scalable**: Service layer architecture for extensibility

## Common Use Cases

### Data Discovery Workflow
```bash
# Build comprehensive catalog
snowflake-cli catalog -p prod

# Map dependencies
snowflake-cli depgraph -p prod --format dot

# Analyze critical table lineage
snowflake-cli lineage CUSTOMER_ORDERS -p prod --depth 3
```

### AI Assistant Integration
```bash
# Start MCP server for AI assistants
SNOWFLAKE_PROFILE=prod snowflake-cli mcp

# Now use Claude Code, VS Code, or Cursor to:
# - "What tables depend on CUSTOMERS?"
# - "Show me the schema for ORDERS table"
# - "Generate a data quality report"
```

### Multi-Environment Development
```bash
# Switch between environments easily
snowflake-cli query "SELECT COUNT(*) FROM users" -p dev
snowflake-cli query "SELECT COUNT(*) FROM users" -p staging
snowflake-cli query "SELECT COUNT(*) FROM users" -p prod
```

## Getting Started

### Prerequisites
- **Python 3.12+** with pip or uv
- **Snowflake account** with appropriate permissions
- **Snowflake CLI** installed (`pip install snowflake-cli`)

### Installation Options

**Option 1: PyPI (Recommended)**
```bash
pip install snowcli-tools
```

**Option 2: Development Install**
```bash
git clone <repository-url>
cd snowcli-tools
uv sync  # or pip install -e .
```

### Profile Setup
```bash
# Key-pair authentication (recommended)
snow connection add --connection-name "my-profile" \
  --account "your-account.region" \
  --user "username" \
  --private-key-file "/path/to/key.p8" \
  --database "DATABASE" \
  --warehouse "WAREHOUSE"

# OAuth authentication
snow connection add --connection-name "my-profile" \
  --account "your-account.region" \
  --user "username" \
  --authenticator "externalbrowser"

# Verify setup
snowflake-cli verify -p my-profile
```

## Documentation

- **[Getting Started Guide](docs/getting-started.md)** - Complete setup and usage guide
- **[Architecture Overview](docs/architecture.md)** - Technical architecture and design patterns
- **[MCP Integration](docs/mcp-integration.md)** - AI assistant setup and configuration
- **[API Reference](docs/api-reference.md)** - Complete command and API documentation
- **[Configuration Guide](docs/configuration.md)** - Advanced configuration options
- **[Contributing](CONTRIBUTING.md)** - Development and contribution guidelines

## Requirements

- **Python**: 3.12 or higher
- **Snowflake CLI**: Latest version recommended
- **Dependencies**: Automatically installed with package
- **Permissions**: `USAGE` on warehouse/database/schema, `SELECT` on `INFORMATION_SCHEMA`

## MCP Integration

For AI assistant integration, install MCP extras:

```bash
# Install MCP dependencies
pip install "mcp>=1.0.0" "fastmcp>=2.8.1" "snowflake-labs-mcp>=1.3.3"

# Start MCP server
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp

# Configure your AI assistant to connect via MCP
```

**Supported AI Assistants:**
- Claude Code
- VS Code with MCP extensions
- Cursor IDE
- Any MCP-compatible client

## Support

- **Documentation**: Comprehensive guides in `/docs`
- **Issues**: Report bugs via [GitHub Issues](link-to-issues)
- **Examples**: Sample workflows in `/examples`
- **Community**: [Discord/Slack community link]

## License

[License Type] - see [LICENSE](LICENSE) file for details.

---

**Version 1.5.0** | Built with ❤️ for the Snowflake community
