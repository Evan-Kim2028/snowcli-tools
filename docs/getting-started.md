# Getting Started with SnowCLI Tools

> **Quick Start**: Set up your Snowflake profile → Install SnowCLI Tools → Start using powerful data operations and MCP integration

## Prerequisites

- **Python 3.12+** with `uv` package manager
- **Snowflake account** with appropriate permissions
- **Private key file** (for key-pair authentication) or other auth method

## Step 1: Install SnowCLI Tools

```bash
# Clone and install the project
git clone <repository-url>
cd snowcli-tools

# Install with uv (recommended)
uv sync

# Or install from PyPI (when published)
pip install snowcli-tools
```

## Step 2: Set Up Your Snowflake Profile

**This is the most critical step** - SnowCLI Tools requires a properly configured Snowflake CLI profile for authentication and connection management.

### Option A: Key-Pair Authentication (Recommended)

```bash
# Create a new profile with private key authentication
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --private-key-file "/path/to/your/private_key.p8" \
  --database "YOUR_DATABASE" \
  --schema "YOUR_SCHEMA" \
  --warehouse "YOUR_WAREHOUSE" \
  --role "YOUR_ROLE"
```

### Option B: Other Authentication Methods

```bash
# Browser-based OAuth
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --authenticator "externalbrowser" \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE"

# Username/password (not recommended for production)
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --password \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE"
```

### Verify Your Profile

```bash
# List all configured profiles
uv run snow connection list

# Test your profile works
uv run snowflake-cli -p my-profile verify
```

**Expected output**: ✅ "Verified Snow CLI and profile 'my-profile'"

## Step 3: Basic Usage

### CLI Operations

```bash
# Execute SQL queries
uv run snowflake-cli -p my-profile query "SELECT CURRENT_VERSION()"

# Build data catalog
uv run snowflake-cli -p my-profile catalog

# Generate dependency graphs
uv run snowflake-cli -p my-profile depgraph

# Analyze lineage
uv run snowflake-cli -p my-profile lineage MY_TABLE
```

### MCP Server (AI Assistant Integration)

```bash
# Start the MCP server for AI assistants
SNOWFLAKE_PROFILE=my-profile uv run snowflake-cli mcp
```

**Success indicators**:
- ✅ FastMCP 2.0 banner appears
- ✅ Profile validation succeeds
- ✅ Health checks pass
- ✅ Server shows "running" status

## Step 4: Configuration (Optional)

### Environment Variables

```bash
# Set default profile
export SNOWFLAKE_PROFILE=my-profile

# Set default paths
export SNOWCLI_CATALOG_DIR=./my_catalog
export SNOWCLI_LINEAGE_DIR=./my_lineage
```

### Configuration File

```yaml
# ~/.snowcli-tools/config.yml
snowflake:
  profile: "my-profile"

catalog:
  output_dir: "./data_catalogue"

lineage:
  cache_dir: "./lineage_cache"
  max_depth: 3
```

## Common Workflows

### 1. Data Discovery Workflow

```bash
# 1. Build comprehensive catalog
uv run snowflake-cli -p my-profile catalog

# 2. Explore dependencies
uv run snowflake-cli -p my-profile depgraph --format dot

# 3. Analyze specific table lineage
uv run snowflake-cli -p my-profile lineage MY_IMPORTANT_TABLE --depth 2
```

### 2. AI Assistant Integration Workflow

```bash
# 1. Start MCP server
SNOWFLAKE_PROFILE=my-profile uv run snowflake-cli mcp &

# 2. Configure your AI assistant (VS Code, Claude Code, etc.) to connect
# 3. Use AI assistant to query data, analyze schemas, generate insights
```

### 3. Development Workflow

```bash
# 1. Set up profile for development environment
uv run snow connection add --connection-name "dev-profile" ...

# 2. Run operations with explicit profile
uv run snowflake-cli -p dev-profile query "..."

# 3. Switch between environments easily
SNOWFLAKE_PROFILE=prod-profile uv run snowflake-cli mcp
```

## Architecture Overview

SnowCLI Tools uses a **layered architecture**:

```
┌─────────────────────────────────────┐
│        Your Applications            │
├─────────────────────────────────────┤
│     SnowCLI Tools MCP Server        │  ← AI Assistant Interface
│  (Catalog, Lineage, Dependencies)   │
├─────────────────────────────────────┤
│      Snowflake Labs MCP             │  ← Authentication & Core Tools
│   (Auth, Connection, Security)      │
├─────────────────────────────────────┤
│       Snowflake CLI                 │  ← Profile Management
├─────────────────────────────────────┤
│         Snowflake                   │  ← Your Data Warehouse
└─────────────────────────────────────┘
```

**Key Benefits**:
- **Secure**: Leverages Snowflake's official authentication
- **Powerful**: Combines official tools with advanced analytics
- **Integrated**: Single MCP endpoint for AI assistants
- **Flexible**: Support for multiple profiles and environments

## Troubleshooting

### Profile Issues

```bash
# Check if profile exists
uv run snow connection list

# Test Snow CLI directly
uv run snow sql -q "SELECT 1" --connection my-profile

# Recreate profile if needed
uv run snow connection delete --connection-name my-profile
uv run snow connection add --connection-name my-profile ...
```

### Permission Issues

Common permissions needed:
- `USAGE` on warehouse, database, schema
- `SELECT` on `INFORMATION_SCHEMA` tables
- `SHOW` privileges for object discovery
- Role with appropriate access to your data

### MCP Server Issues

```bash
# Check for missing dependencies
uv add "mcp>=1.0.0" "fastmcp>=2.8.1" "snowflake-labs-mcp>=1.3.3"

# Test with debug output
SNOWFLAKE_PROFILE=my-profile uv run snowflake-cli mcp --log-level DEBUG
```

## Next Steps

- **Read the [Architecture Guide](./architecture.md)** to understand the service layer design
- **Explore [MCP Integration](./mcp-integration.md)** for AI assistant setup
- **Check [API Reference](./api-reference.md)** for programmatic usage
- **Review [Configuration](./configuration.md)** for advanced settings

## Support

- **Documentation**: Check `/docs` folder for detailed guides
- **Issues**: Report problems via GitHub issues
- **Examples**: See `/examples` directory for common use cases

---

*Version 1.5.0 | Updated: 2025-09-28*