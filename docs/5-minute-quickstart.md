# 5-Minute Quickstart

Get SnowCLI Tools running in under 5 minutes! This tutorial assumes you have a Snowflake account and basic command-line experience.

## Prerequisites Check (30 seconds)

```bash
# Check Python version (need 3.12+)
python --version

# Check if Snowflake CLI is installed
snow --version

# If not installed, install it:
pip install nanuk
```

## Step 1: Install SnowCLI Tools (1 minute)

```bash
# Install from PyPI
pip install nanuk-mcp

# Verify installation
nanuk --version
# Expected: 1.9.0
```

## Step 2: Configure Your Profile (1 minute)

```bash
# Create a profile (replace with your details)
snow connection add \
  --connection-name "quickstart" \
  --account "your-org-your-account.region" \
  --user "your-username" \
  --authenticator "externalbrowser" \
  --database "SNOWFLAKE" \
  --warehouse "COMPUTE_WH"

# Expected: Profile created successfully
```

## Step 3: Test Your Connection (30 seconds)

```bash
# Verify everything works
nanuk --profile quickstart verify

# Expected output:
# ✓ Verified Snow CLI and profile 'quickstart'.
# ✓ Connection successful
```

## Step 4: Run Your First Query (30 seconds)

```bash
# Execute a simple query
nanuk --profile quickstart query "SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_WAREHOUSE()"

# Expected: Query results in table format
```

## Step 5: Explore Your Data (1.5 minutes)

```bash
# Build a catalog of your database
nanuk --profile quickstart catalog -d SNOWFLAKE

# Expected: Progress bar, then summary statistics

# Query lineage for a table (if you have one)
nanuk --profile quickstart lineage INFORMATION_SCHEMA.TABLES

# Expected: Lineage information
```

## What's Next?

### For Data Analysis
- Explore the [Getting Started Guide](getting-started.md) for detailed setup
- Learn about [authentication methods](getting-started.md#step-2-set-up-your-snowflake-profile)
- Check out [advanced features](features_overview.md)

### For AI Assistant Integration
- Set up [MCP integration](mcp-integration.md) for Claude Code
- Configure your AI assistant to use SnowCLI Tools
- Explore [MCP tools](api/README.md#tools) available

### For Automation
- Learn about [automation patterns](guides/automation.md)
- Set up [CI/CD integration](guides/automation.md#cicd-integration)
- Create [scheduled jobs](guides/automation.md#scheduled-jobs)

## Troubleshooting

### Common Issues

**"Profile not found"**:
- Check profile name: `snow connection list`
- Create profile: `snow connection add`

**"Connection failed"**:
- Verify account format: `org-account.region`
- Check user permissions
- Try browser authentication: `--authenticator externalbrowser`

**"Permission denied"**:
- Ensure USAGE on warehouse
- Check database access
- Contact Snowflake admin

### Getting Help

- 📖 [Getting Started Guide](getting-started.md) - Detailed setup
- 🔧 [Configuration Guide](configuration.md) - Advanced settings
- 🐛 [Error Catalog](api/errors.md) - Common issues and solutions
- 💬 [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions) - Community help

## Success!

You've successfully:
- ✅ Installed SnowCLI Tools
- ✅ Configured Snowflake connection
- ✅ Executed your first query
- ✅ Built a data catalog
- ✅ Analyzed data lineage

**Time taken**: ~5 minutes

**Next steps**: Explore the full documentation to unlock advanced features like MCP integration, automation, and advanced lineage analysis.

---

*Need help? Check the [Error Catalog](api/errors.md) or [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions).*
