# MCP Quick Start Guide
## Get Started with SnowCLI Tools MCP Server in 5 Minutes

**Last Updated:** 2025-10-06
**Version:** 1.10.0
**Audience:** First-time users setting up MCP integration

---

## What is MCP?

**MCP (Model Context Protocol)** is a standard protocol that allows AI assistants (like Claude Code, Cursor, VS Code Copilot) to connect to external tools and data sources. Think of it as an API that AI assistants can use to interact with your Snowflake data warehouse.

### Why Use SnowCLI Tools MCP Server?

- **Safe by Default**: Read-only operations, blocks destructive SQL (DROP, DELETE, TRUNCATE)
- **AI-Powered Discovery**: Automatically understand table purposes, find PII, discover relationships
- **Fast Queries**: Execute SQL with automatic timeout protection
- **Built on Official Stack**: Extends Snowflake Labs official MCP server

---

## Prerequisites

Before you begin, you need:

1. **Python 3.12+** installed
2. **Snowflake account** with read access
3. **AI assistant** that supports MCP:
   - Claude Code (recommended)
   - Cursor
   - VS Code with MCP extension
4. **5 minutes** of setup time

---

## Step 1: Install SnowCLI Tools

Open your terminal and run:

```bash
# Using uv (recommended - fastest)
uv pip install snowcli-tools

# OR using pip
pip install snowcli-tools
```

**Verify installation:**
```bash
python -c "from snowcli_tools import __version__; print(__version__)"
# Should print: 1.10.0
```

---

## Step 2: Configure Snowflake Connection

You need a Snowflake profile for authentication. Choose one method:

### Option A: Using Snowflake CLI (Recommended)

```bash
# Install Snowflake CLI
pip install snowflake-cli

# Create a connection profile
snow connection add \
  --connection-name "my-profile" \
  --account "myorg-myaccount" \
  --user "your_username" \
  --authenticator externalbrowser \
  --database "ANALYTICS" \
  --schema "PUBLIC" \
  --warehouse "COMPUTE_WH"

# Test connection
snow connection test --connection "my-profile"
```

### Option B: Using Key-Pair Authentication (More Secure)

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -m PEM -f ~/.ssh/snowflake_key

# Add public key to Snowflake user
# (In Snowflake UI: User Settings → Public Keys)

# Create profile with key-pair auth
snow connection add \
  --connection-name "my-profile" \
  --account "myorg-myaccount" \
  --user "your_username" \
  --private-key-file "~/.ssh/snowflake_key" \
  --database "ANALYTICS" \
  --warehouse "COMPUTE_WH"
```

### Option C: Environment Variables

```bash
# Set in your shell profile (~/.bashrc or ~/.zshrc)
export SNOWFLAKE_ACCOUNT="myorg-myaccount"
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_DATABASE="ANALYTICS"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_PROFILE="my-profile"
```

---

## Step 3: Set Up MCP Configuration

MCP servers are configured via a `.mcp.json` file. You can set this up **globally** (for all projects) or **per-project**.

### Option A: Project-Scoped Setup (Recommended)

Create `.mcp.json` in your project root:

```bash
cd /path/to/your/project
touch .mcp.json
```

**Edit `.mcp.json`:**

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "python",
      "args": [
        "-m",
        "snowcli_tools.mcp_server"
      ],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**If using a virtual environment:**

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "/absolute/path/to/your/.venv/bin/python",
      "args": [
        "-m",
        "snowcli_tools.mcp_server"
      ],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

### Option B: Global Setup

Create `.mcp.json` in your home directory:

```bash
touch ~/.mcp.json
```

**Edit `~/.mcp.json`:**

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

---

## Step 4: Restart Your AI Assistant

**For Claude Code:**
1. Quit Claude Code completely (Cmd+Q on Mac, Alt+F4 on Windows)
2. Reopen Claude Code
3. You should see a prompt to approve the MCP server
4. Click "Approve" or "Always Allow"

**For Cursor:**
1. Restart Cursor
2. Open Settings → MCP Servers
3. Verify `snowcli-tools` appears in the list

**For VS Code:**
1. Reload window (Cmd+Shift+P → "Reload Window")
2. Check MCP status in status bar

---

## Step 5: Verify MCP Connection

### Test in AI Assistant

Ask your AI assistant:

```
Can you test the Snowflake connection?
```

The assistant should use the `test_connection` tool and report success.

### Manual Verification

```bash
# Test MCP server manually
python -m snowcli_tools.mcp_server --help

# Expected output:
# MCP Server for SnowCLI Tools
# Available tools: execute_query, preview_table, profile_table, ...
```

---

## Quick Usage Examples

Once set up, try these in your AI assistant:

### Example 1: Test Connection
```
Test my Snowflake connection
```

### Example 2: List Tables
```
Show me all tables in my database
```

### Example 3: Preview Table
```
Show me the first 10 rows of CUSTOMERS table
```

### Example 4: Profile a Table
```
Profile the CUSTOMERS table - what's its purpose and what columns does it have?
```

### Example 5: Find PII
```
Which tables in my database contain PII?
```

### Example 6: Run Safe Query
```
Calculate total sales by month from ORDERS table
```

---

## Troubleshooting

### Issue: MCP Server Not Showing Up

**Symptoms:** AI assistant doesn't recognize Snowflake commands

**Solutions:**
1. Verify `.mcp.json` exists in correct location
2. Check JSON syntax: `cat .mcp.json | python -m json.tool`
3. Restart AI assistant completely (quit and reopen)
4. Check Python path: `which python` matches path in `.mcp.json`

### Issue: Snowflake Connection Failed

**Symptoms:** "Profile not found" or "Connection timeout"

**Solutions:**
1. Verify profile exists: `snow connection list`
2. Test connection: `snow connection test --connection "my-profile"`
3. Check environment variable: `echo $SNOWFLAKE_PROFILE`
4. Ensure credentials are correct

### Issue: Permission Denied

**Symptoms:** "Access denied" or "Insufficient privileges"

**Solutions:**
1. Verify Snowflake user has `USAGE` on warehouse, database, schema
2. Verify user has `SELECT` on `INFORMATION_SCHEMA` tables
3. Ask Snowflake admin to grant read permissions

### Issue: Python Module Not Found

**Symptoms:** "ModuleNotFoundError: No module named 'snowcli_tools'"

**Solutions:**
1. Install package: `pip install snowcli-tools`
2. Use absolute Python path in `.mcp.json`
3. Check virtual environment is activated

---

## Configuration Options

### Advanced MCP Server Configuration

**With Service Config File:**

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "python",
      "args": [
        "-m",
        "snowcli_tools.mcp_server",
        "--service-config-file",
        "/path/to/mcp_service_config.json"
      ],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**`mcp_service_config.json` (optional):**

```json
{
  "snowflake": {
    "account": "",
    "user": "",
    "database": "",
    "schema": "",
    "warehouse": "",
    "role": ""
  }
}
```

**Note:** Leave values empty to use profile defaults.

### Environment Variables

You can override profile settings with environment variables:

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_DATABASE": "ANALYTICS",
        "SNOWFLAKE_SCHEMA": "PUBLIC",
        "SNOWFLAKE_ROLE": "ANALYST"
      }
    }
  }
}
```

---

## Available MCP Tools

Once configured, your AI assistant can use these tools:

### Core Query Tools
- **`execute_query`** - Run safe SQL queries (read-only by default)
- **`preview_table`** - Quick table inspection (max 1000 rows)

### Discovery & Documentation
- **`profile_table`** - AI-powered table understanding (schema, stats, PII detection)
- **`build_catalog`** - Extract complete database metadata
- **`get_catalog_summary`** - Get catalog statistics

### Lineage & Dependencies
- **`query_lineage`** - Trace data flows (upstream/downstream)
- **`build_dependency_graph`** - Map object relationships

### Health & Diagnostics
- **`health_check`** - Validate system health
- **`test_connection`** - Quick connection test

---

## Security Features

SnowCLI Tools MCP Server is **read-only by default**:

✅ **Allowed Operations:**
- `SELECT` queries
- `SHOW` commands
- `DESCRIBE` commands
- Metadata queries

❌ **Blocked Operations:**
- `DROP` (tables, databases, etc.)
- `DELETE` (removing data)
- `TRUNCATE` (clearing tables)
- `ALTER` (schema changes)
- `CREATE` (new objects)

**Override for Advanced Users:**

If you need write operations, use `execute_query_unsafe` (not exposed to AI by default).

---

## Next Steps

### Learn More
- **[MCP Tools Reference](./mcp_tools_reference.md)** - Complete tool documentation
- **[Security Guide](./security.md)** - Understanding safety features
- **[Advanced Configuration](./mcp_advanced_config.md)** - Custom setups

### Common Workflows
- **[Database Discovery](./workflows/database_discovery.md)** - Explore unknown databases
- **[PII Detection](./workflows/pii_detection.md)** - Find sensitive data
- **[Impact Analysis](./workflows/impact_analysis.md)** - Understand dependencies

### Get Help
- **GitHub Issues:** [Report bugs or request features](https://github.com/Evan-Kim2028/snowcli-tools/issues)
- **Documentation:** Browse `/docs` folder for detailed guides

---

## Summary Checklist

- [ ] Python 3.12+ installed
- [ ] `snowcli-tools` package installed
- [ ] Snowflake profile configured and tested
- [ ] `.mcp.json` created (project or global)
- [ ] AI assistant restarted
- [ ] MCP server approved in AI assistant
- [ ] Connection tested successfully
- [ ] Ready to query Snowflake!

**Time to Complete:** ~5 minutes
**Difficulty:** Beginner-friendly

---

## Example Session

Here's what a typical session looks like:

```
User: "Test my Snowflake connection"
AI: I'll test the connection for you.
[Uses: test_connection()]
AI: ✅ Connected to Snowflake successfully!
    Profile: my-profile
    Account: myorg-myaccount
    Database: ANALYTICS
    Warehouse: COMPUTE_WH

User: "What tables are in my database?"
AI: I'll query the available tables.
[Uses: execute_query("SHOW TABLES")]
AI: Found 15 tables in ANALYTICS.PUBLIC:
    - CUSTOMERS (last modified: 2025-10-01)
    - ORDERS (last modified: 2025-10-06)
    - PRODUCTS (last modified: 2025-09-15)
    ...

User: "What's in the CUSTOMERS table?"
AI: I'll preview the table structure and sample data.
[Uses: preview_table("CUSTOMERS", limit=10)]
AI: CUSTOMERS table has 5 columns:
    - customer_id (NUMBER) - Primary key
    - email (VARCHAR) - Contains PII
    - name (VARCHAR) - Contains PII
    - created_at (TIMESTAMP)
    - status (VARCHAR)

    Sample rows: [shows 10 rows]

User: "Profile this table and find all PII"
AI: I'll run a comprehensive analysis.
[Uses: profile_table("CUSTOMERS", include_ai_analysis=True)]
AI: 📊 CUSTOMERS Table Analysis:

    Business Purpose: Customer master data with contact information

    PII Detected:
    - email (CONFIRMED - email addresses)
    - name (LIKELY - personal names)
    - phone (CONFIRMED - phone numbers)

    Statistics:
    - Total rows: 125,430
    - Null rate: email (0.2%), name (0.0%), phone (15.3%)
    - Unique values: email (125,180), name (98,234)

    Recommendations:
    - Consider masking email/phone for non-production environments
    - Implement column-level security for PII access
```

---

**Congratulations!** You're now ready to use SnowCLI Tools MCP Server with your AI assistant.

**Next:** Explore [MCP Tools Reference](./mcp_tools_reference.md) to learn about all available tools and their parameters.

---

**Questions?** Check the [Troubleshooting Guide](./troubleshooting.md) or open a [GitHub Issue](https://github.com/Evan-Kim2028/snowcli-tools/issues).
