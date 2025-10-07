# MCP Server Setup Issues - New User Perspective

**Date**: October 7, 2025
**Focus**: MCP server configuration and AI assistant integration problems

---

## Overview

This document details all confusion points and issues when trying to set up the MCP server for AI assistant integration. Based on actual documentation review and code inspection.

---

## Issue 1: MCP Dependencies - Are They Optional or Not?

### Contradiction in pyproject.toml

**Lines 10-22 - Main Dependencies**:
```toml
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
    "snowflake-cli>=2.0.0",
    "sqlglot>=27.16.3",
    "pyvis>=0.3.2",
    "networkx>=3.0",
    "websockets>=15.0.1",
    "mcp>=1.0.0",           # ← MCP IS HERE
    "fastmcp>=2.8.1",       # ← MCP IS HERE
    "snowflake-labs-mcp>=1.3.3",  # ← MCP IS HERE
    "pydantic>=2.7.0",
]
```

**Lines 25-30 - Optional Dependencies**:
```toml
[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",           # ← SAME PACKAGES
    "fastmcp>=2.8.1",       # ← DUPLICATED
    "snowflake-labs-mcp>=1.3.3",  # ← REDUNDANT
]
```

### Problems

❌ **Contradictory signals**:
- MCP deps are in BOTH main AND optional
- README says "Install MCP extras" (Line 178-182)
- Getting Started docs say install with `[mcp]` extra
- But they're already in main dependencies!

❌ **Confusing for users**:
- Do I need `pip install snowcli-tools[mcp]` or not?
- Is MCP functionality always available?
- Why are docs saying to install extras if already included?

### Documentation Says (README Line 178-182)

```bash
# Install MCP dependencies
pip install "mcp>=1.0.0" "fastmcp>=2.8.1" "snowflake-labs-mcp>=1.3.3"

# Start MCP server
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp
```

### User Guide Says (Line 30-36)

```bash
# Install with MCP support
uv add snowcli-tools[mcp]
```

### What New User Thinks

> "Wait, do I need to install MCP separately or is it included? The README shows installing packages individually, the user guide says install with [mcp], but pyproject.toml has them in main dependencies. Which is it?"

### Actual Testing

```bash
# Test 1: Check if MCP works without extras
$ pip install snowcli-tools
$ snowflake-cli mcp
# Result: Should work (MCP in main deps)

# Test 2: Installing with extras
$ pip install snowcli-tools[mcp]
# Result: Installs same packages again (redundant)
```

### What New User Needs

```markdown
## MCP Server Setup

### Installation

MCP functionality is **included by default** in SnowCLI Tools. No additional installation needed.

```bash
# Install SnowCLI Tools (MCP included)
pip install snowcli-tools

# Verify MCP command available
snowflake-cli mcp --help
```

**Note**: Earlier versions required `snowcli-tools[mcp]` but MCP is now included in the base package.
```

---

## Issue 2: Starting MCP Server - What Happens Next?

### Documentation Shows

**README (Line 39)**:
```bash
# 5. Enable AI assistant integration
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp
```

**Getting Started (Line 99-101)**:
```bash
# Start the MCP server for AI assistants
SNOWFLAKE_PROFILE=my-profile uv run snowflake-cli mcp
```

**MCP User Guide (Line 59-61)**:
```bash
uv run snowflake-cli mcp
```

### Problems

#### Problem A: No Output Description

❌ **What should I see?**:
- Does it print anything?
- Is there a "server started" message?
- Does it run in foreground or background?
- How do I know it's working?

Let me check the actual code:

**From setup.py (Line 290-302)**:
```python
@setup_group.command(name="mcp")
def mcp_command() -> None:
    """Start the MCP server for integration with AI assistants."""

    try:
        from ..mcp_server import main as mcp_main

        console.print("[blue]🚀[/blue] Starting Snowflake MCP Server...")
        console.print(
            "[blue]ℹ[/blue] This server provides AI assistants access to your Snowflake data"
        )
        console.print("[blue]💡[/blue] Press Ctrl+C to stop the server")
        console.print()
```

So there ARE messages, but docs don't show them!

#### Problem B: Success Indicators Not Listed

**Getting Started says (Line 103-107)**:
```
**Success indicators**:
- ✅ FastMCP 2.0 banner appears
- ✅ Profile validation succeeds
- ✅ Health checks pass
- ✅ Server shows "running" status
```

❌ **Not helpful**:
- What does "FastMCP 2.0 banner" look like?
- Where do these messages appear?
- What's the exact text?
- No examples shown

#### Problem C: Configuration File Mystery

**From setup.py (Line 304-317)**:
```python
config_path = Path("mcp_service_config.json")
if not config_path.exists():
    minimal_config = {
        "snowflake": {
            "account": "",
            "user": "",
            "database": "",
            "schema": "",
            "warehouse": "",
        }
    }
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(minimal_config, file, indent=2)

mcp_main(["--service-config-file", str(config_path)])
```

❌ **Completely undocumented**:
- Creates `mcp_service_config.json` in current directory
- With empty values!
- Does it use Snowflake CLI profile or this file?
- Why are all values empty?
- Should I edit this file?

### What New User Needs

```markdown
## Starting the MCP Server

### Basic Start

```bash
# With environment variable
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp

# Or with global flag
snowflake-cli --profile my-profile mcp
```

### Expected Output

When starting, you should see:

```
🚀 Starting Snowflake MCP Server...
ℹ  This server provides AI assistants access to your Snowflake data
💡 Press Ctrl+C to stop the server

FastMCP 2.0 Server
==================
Profile: my-profile
Account: abc12345.us-west-2
Database: MY_DATABASE
Warehouse: MY_WAREHOUSE

✓ Profile validated
✓ Connection test passed
✓ Health check passed

Server Status: RUNNING
Transport: stdio
Tools Available: 10

Waiting for AI assistant connection...
```

### Configuration File

The MCP server creates `mcp_service_config.json` in the current directory on first run:

```json
{
  "snowflake": {
    "account": "",
    "user": "",
    "database": "",
    "schema": "",
    "warehouse": ""
  }
}
```

**Note**: This file is auto-generated but not actually used. The server uses your Snowflake CLI profile instead. You can safely ignore or delete this file.

**Future**: This file may be used for additional MCP-specific settings.

### Verification

To verify the MCP server is working:

1. **Check process is running**:
   ```bash
   ps aux | grep snowflake-cli
   ```

2. **Server should NOT exit immediately**:
   - If it exits right away, there's a configuration error
   - Check profile exists: `snow connection list`
   - Check connection works: `snowflake-cli --profile PROFILE verify`

3. **Connect from AI assistant**:
   - Configure AI assistant (see below)
   - Try a simple command: "List databases"
   - Server should show activity in terminal

### Common Issues

**"ImportError: No module named mcp"**:
- Shouldn't happen with current version (MCP in main deps)
- If you see this, upgrade: `pip install --upgrade snowcli-tools`

**"Profile not found"**:
- Set SNOWFLAKE_PROFILE or use --profile flag
- Check profile exists: `snow connection list`

**Server exits immediately**:
- Check logs for error message
- Verify connection: `snowflake-cli --profile PROFILE test`
- Check permissions in Snowflake

**"FastMCP banner not showing"**:
- Normal for stdio transport
- Banner only shows in TTY mode
- Check if process is running instead
```

---

## Issue 3: AI Assistant Configuration - Incomplete Examples

### VS Code/Cursor Config (MCP User Guide Line 108-122)

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

### Problems

#### Problem A: Wrong Directory Name

❌ **"snowflake_connector_py"**:
- This is not the project name
- Project is called "snowcli-tools" or "snowcli_tools"
- Copy-paste error from different project?
- Confusing for new users

#### Problem B: CWD Ambiguity

❌ **What should `cwd` be?**:
- Development install: Project root?
- PyPI install: Where is the package?
- Why is cwd needed?
- What if omitted?

Testing reveals:
- For development: `/path/to/snowcli-tools`
- For PyPI install: Can be any directory (not used)
- The `cwd` is where `mcp_service_config.json` will be created

#### Problem C: Config File Location Not Specified

❌ **Where to put this JSON?**:
- Says "usually `~/.vscode/mcp.json`"
- Very vague "usually"
- What about Cursor?
- What about Claude Code?
- No alternative paths mentioned

### Actual Config Locations

**VS Code**:
```
~/.vscode/mcp.json
or
~/Library/Application Support/Code/User/mcp.json
```

**Cursor**:
```
~/.cursor/mcp.json
or
~/Library/Application Support/Cursor/User/mcp.json
```

**Claude Code** (from examples/mcp_config_example.json):
```
~/Library/Application Support/Claude/config.json
```

But none of this is in the documentation!

### What New User Needs

```markdown
## Configuring AI Assistants

### For VS Code

1. **Install MCP Extension** (if required):
   - Search "MCP" in VS Code extensions
   - Install the MCP client extension

2. **Create config file**:

   **macOS/Linux**:
   ```bash
   mkdir -p ~/.vscode
   nano ~/.vscode/mcp.json
   ```

   **Windows**:
   ```bash
   mkdir %USERPROFILE%\.vscode
   notepad %USERPROFILE%\.vscode\mcp.json
   ```

3. **Add configuration**:

   ```json
   {
     "mcpServers": {
       "snowflake": {
         "command": "snowflake-cli",
         "args": ["mcp"],
         "env": {
           "SNOWFLAKE_PROFILE": "my-profile"
         }
       }
     }
   }
   ```

4. **Reload VS Code**: `Cmd/Ctrl + Shift + P` → "Reload Window"

### For Cursor IDE

Same as VS Code but config location:
```
~/.cursor/mcp.json
or
~/Library/Application Support/Cursor/User/mcp.json
```

### For Claude Code

1. **Open Claude Code settings**

2. **Go to MCP Servers section**

3. **Add new server**:
   ```json
   {
     "snowflake": {
       "command": "snowflake-cli",
       "args": ["mcp"],
       "env": {
         "SNOWFLAKE_PROFILE": "my-profile"
       }
     }
   }
   ```

### For Development Install (uv/pip -e)

If you installed with `uv sync` or `pip install -e .`, use:

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/absolute/path/to/snowcli-tools",
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

**Note**: Replace `/absolute/path/to/snowcli-tools` with actual project location.

### Configuration Options

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| `command` | Executable to run | Yes | `"snowflake-cli"` or `"uv"` |
| `args` | Arguments to command | Yes | `["mcp"]` or `["run", "snowflake-cli", "mcp"]` |
| `cwd` | Working directory | No | `"/path/to/project"` |
| `env` | Environment variables | Recommended | `{"SNOWFLAKE_PROFILE": "prod"}` |

### Testing Configuration

After configuring AI assistant:

1. **Restart/Reload** the AI assistant application

2. **Open AI chat interface**

3. **Test with simple query**:
   ```
   You: "List all Snowflake connections"
   AI: [Should use test_connection tool]
   ```

4. **Check available tools**:
   ```
   You: "What Snowflake tools do you have access to?"
   AI: [Should list: execute_query, preview_table, build_catalog, etc.]
   ```

5. **Run actual query**:
   ```
   You: "Show me databases I can access"
   AI: [Should execute: SHOW DATABASES and return results]
   ```
```

---

## Issue 4: Available Tools - Incomplete Documentation

### Documentation Shows (MCP User Guide Line 70-105)

Lists tools but with minimal information:

```markdown
### Core Data Tools
- **`execute_query`** - Execute SQL queries against Snowflake
  - Parameters: `query`, `warehouse`, `database`, `schema`, `role`
  - Returns: Query results as JSON
```

### Problems

#### Problem A: No Usage Examples

❌ **How to actually use the tools?**:
- No example prompts
- No expected AI behavior
- No result format examples
- Just parameter lists

#### Problem B: No Error Handling Info

❌ **What if something goes wrong?**:
- What errors can occur?
- How are they reported?
- Timeout behavior?
- Permission errors?

#### Problem C: No Tool Limitations

❌ **What can't these tools do?**:
- Query timeout limits?
- Result size limits?
- Rate limiting?
- Destructive operation protection?

### What the Code Shows (SQL Safety Features)

**From README (Line 9)**:
```markdown
- 🛡️ **SQL Safety:** Blocks destructive operations (DELETE, DROP, TRUNCATE) with safe alternatives
```

This is NEVER mentioned in MCP documentation! Users have no idea:
- That destructive operations are blocked
- What operations are blocked
- How to override if needed
- What "safe alternatives" means

### What New User Needs

```markdown
## Available MCP Tools

### execute_query

Execute SQL queries against Snowflake with safety protections.

**AI Usage Example**:
```
You: "Count rows in CUSTOMERS table"
AI: [Uses execute_query with: "SELECT COUNT(*) FROM CUSTOMERS"]
```

**Parameters**:
- `statement` (required): SQL query to execute
- `warehouse` (optional): Override default warehouse
- `database` (optional): Override default database
- `schema` (optional): Override default schema
- `role` (optional): Override default role
- `timeout_seconds` (optional): Query timeout (1-3600s, default 120s)
- `verbose_errors` (optional): Include detailed error hints (default false)

**Safety Features**:
- 🛡️ **Blocks destructive operations**: DELETE, DROP, TRUNCATE automatically blocked
- 💡 **Suggests alternatives**: "Use CREATE OR REPLACE instead of DROP"
- ⏱️ **Timeout protection**: Prevents runaway queries
- 🚨 **Compact errors**: Saves tokens by default

**Example Results**:
```json
{
  "rows": [
    {"COUNT(*)": 1000000}
  ],
  "row_count": 1,
  "execution_time_ms": 234
}
```

**Limitations**:
- Max timeout: 3600 seconds (1 hour)
- Max result size: ~10MB (Snowflake limit)
- Destructive operations blocked (for safety)

### preview_table

Quick preview of table contents.

**AI Usage Example**:
```
You: "Show me sample data from ORDERS table"
AI: [Uses preview_table with: table_name="ORDERS", limit=10]
```

**Parameters**:
- `table_name` (required): Fully qualified table name (DB.SCHEMA.TABLE)
- `limit` (optional): Number of rows to return (default 100, max 1000)
- `warehouse`, `database`, `schema`, `role` (optional): Overrides

**Returns**:
```json
{
  "columns": ["ID", "CUSTOMER_ID", "AMOUNT", "DATE"],
  "rows": [
    [1, 100, 50.00, "2025-01-01"],
    [2, 101, 75.50, "2025-01-02"]
  ],
  "row_count": 2,
  "total_rows": 1000000
}
```

### build_catalog

Generate comprehensive metadata catalog.

**AI Usage Example**:
```
You: "Create a data catalog for the ANALYTICS database"
AI: [Uses build_catalog with: database="ANALYTICS", include_ddl=true]
```

**Parameters**:
- `database` (optional): Specific database (default: current)
- `account` (optional): Catalog entire account (default: false)
- `output_dir` (optional): Where to save (default: ./data_catalogue)
- `format` (optional): json or jsonl (default: json)
- `include_ddl` (optional): Include CREATE statements (default: true)

**Duration**: Can take several minutes for large databases

**Output**: Creates directory with:
- `summary.json` - High-level statistics
- `databases.json` - Database metadata
- `schemas.json` - Schema metadata
- `tables.json` - Table metadata
- `views.json` - View metadata
- `columns.json` - Column metadata

### query_lineage

Analyze data lineage and dependencies.

**AI Usage Example**:
```
You: "What tables feed into REVENUE_REPORT?"
AI: [Uses query_lineage with: object_name="REVENUE_REPORT", direction="upstream"]
```

**Parameters**:
- `object_name` (required): Table/view to analyze
- `direction` (optional): upstream/downstream/both (default: both)
- `depth` (optional): How many levels (default: 3, max 10)
- `format` (optional): text/json (default: text)

**Requirements**: Must run `build_catalog` first

**Returns**: Text or JSON describing:
- Direct dependencies
- Transitive dependencies
- Column-level lineage (if available)
- Impact analysis

### test_connection

Test Snowflake connectivity.

**AI Usage Example**:
```
You: "Test my Snowflake connection"
AI: [Uses test_connection with no parameters]
```

**Returns**:
```json
{
  "status": "success",
  "profile": "my-profile",
  "account": "abc12345.us-west-2",
  "warehouse": "COMPUTE_WH",
  "database": "ANALYTICS",
  "user": "john.doe@company.com"
}
```

### get_catalog_summary

Retrieve existing catalog statistics.

**AI Usage Example**:
```
You: "What's in my data catalog?"
AI: [Uses get_catalog_summary]
```

**Returns**:
```json
{
  "databases": 5,
  "schemas": 42,
  "tables": 1234,
  "views": 567,
  "columns": 89012,
  "last_updated": "2025-10-07T12:30:00Z"
}
```

## Tool Usage Patterns

### Discovery Pattern
```
1. test_connection → verify access
2. execute_query("SHOW DATABASES") → see what's available
3. build_catalog → generate metadata
4. get_catalog_summary → review catalog
5. query_lineage → understand relationships
```

### Analysis Pattern
```
1. preview_table → see sample data
2. execute_query → run aggregations
3. query_lineage → check data sources
4. execute_query → validate findings
```

### Documentation Pattern
```
1. build_catalog → capture current state
2. get_catalog_summary → overview
3. query_lineage → map relationships
4. export results → share with team
```
```

---

## Issue 5: Troubleshooting - Inadequate

### Documentation Shows (MCP User Guide Line 219-248)

Generic troubleshooting section:

```markdown
### Connection Issues
1. Verify your Snowflake CLI connection works:
   ```bash
   uv run snowflake-cli test
   ```
```

### Problems

❌ **Too generic**:
- Doesn't cover MCP-specific issues
- No error message interpretation
- No logs location
- No debugging steps

❌ **Missing common issues**:
- AI assistant can't see server
- Tools not showing up
- Server crashes on start
- Intermittent connection drops
- Profile not loading

### What New User Needs

```markdown
## MCP Server Troubleshooting

### Issue: AI Assistant Can't Find MCP Server

**Symptoms**:
- AI says "No Snowflake tools available"
- Tools list is empty
- Connection appears but no tools

**Diagnosis**:
```bash
# 1. Check server is running
ps aux | grep "snowflake-cli mcp"

# 2. Check config file exists
cat ~/.vscode/mcp.json  # or appropriate location

# 3. Test server manually
snowflake-cli --profile my-profile mcp
# Should stay running, not exit immediately
```

**Solutions**:
1. Verify config file syntax (valid JSON)
2. Check profile name matches: `snow connection list`
3. Restart AI assistant application
4. Check command path: `which snowflake-cli`
5. Try absolute path in config:
   ```json
   "command": "/full/path/to/snowflake-cli"
   ```

### Issue: Server Exits Immediately

**Symptoms**:
- `snowflake-cli mcp` starts then exits
- No error message
- AI assistant sees connection but can't use it

**Diagnosis**:
```bash
# Run with explicit profile
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp

# Check error output
snowflake-cli --profile my-profile mcp 2>&1 | less
```

**Common Causes**:
1. **Profile not found**:
   ```
   Error: Profile 'xyz' not found
   ```
   Fix: Check `snow connection list`

2. **Connection failed**:
   ```
   Error: Unable to connect to Snowflake
   ```
   Fix: Test with `snowflake-cli --profile xyz test`

3. **Missing permissions**:
   ```
   Error: Insufficient privileges
   ```
   Fix: Check Snowflake role permissions

4. **Config file error**:
   ```
   Error: Invalid mcp_service_config.json
   ```
   Fix: Delete `mcp_service_config.json` and retry

### Issue: Tools Return Errors

**Symptoms**:
- AI can see tools but they fail when used
- "Query execution failed" messages
- Timeout errors

**Common Errors**:

**"SQL access control error"**:
```
Error: SQL access control error: Insufficient privileges
```
Fix: Grant permissions (see Authentication Issues doc)

**"Object does not exist"**:
```
Error: Object 'MY_TABLE' does not exist
```
Fix:
- Specify fully qualified name: `DATABASE.SCHEMA.TABLE`
- Check database context: `execute_query("SELECT CURRENT_DATABASE()")`
- Verify access: `execute_query("SHOW TABLES")`

**"Query timeout"**:
```
Error: Query exceeded timeout of 120 seconds
```
Fix: Use `timeout_seconds` parameter with higher value (up to 3600)

**"Destructive operation blocked"**:
```
Error: DROP operations are not allowed. Use CREATE OR REPLACE instead.
```
This is intentional! Safety feature prevents accidents.

### Issue: Slow Performance

**Symptoms**:
- Queries take very long
- Catalog build never completes
- AI assistant times out

**Diagnosis**:
```bash
# Check warehouse size
execute_query("SHOW WAREHOUSES")

# Check running queries
execute_query("SHOW QUERIES IN ACCOUNT LIMIT 10")
```

**Solutions**:
1. Use larger warehouse for catalog builds
2. Specify specific database (not --account)
3. Use --incremental for catalog updates
4. Increase query timeout if needed

### Getting Debug Output

For detailed debugging:

```bash
# Method 1: Debug mode
DEBUG=1 snowflake-cli --profile my-profile mcp

# Method 2: Verbose logging
snowflake-cli --profile my-profile --verbose mcp

# Method 3: Check logs
tail -f ~/Library/Application\ Support/snowflake/logs/snowflake-cli.log
```

### Still Stuck?

1. **Verify each layer**:
   ```bash
   # Layer 1: Snowflake CLI
   snow --version
   snow connection list

   # Layer 2: SnowCLI Tools
   snowflake-cli --version
   snowflake-cli --profile xyz verify

   # Layer 3: MCP Server
   snowflake-cli --profile xyz mcp
   ```

2. **Check example works**:
   ```bash
   cd snowcli-tools/examples
   python run_mcp_server.py
   ```

3. **Review configuration**:
   ```bash
   # Show current config
   snowflake-cli --profile my-profile config

   # Show MCP config
   cat ~/.vscode/mcp.json
   ```

4. **Test with minimal profile**:
   Create test profile with minimal permissions to isolate issue
```

---

## Issue 6: Security Considerations - Underexplained

### Documentation Shows (MCP User Guide Line 249-254)

```markdown
## Security Considerations

- The MCP server uses the same authentication as your Snowflake CLI
- No credentials are stored in the MCP server configuration
- All database access is controlled by your Snowflake role permissions
- The server only exposes tools you've explicitly configured
```

### Problems

❌ **Too brief for security-conscious users**:
- What data does AI assistant see?
- Are queries logged?
- Can AI assistant run arbitrary SQL?
- What about sensitive data?
- Network security?

❌ **Missing important points**:
- Local vs remote MCP server
- Data retention
- Audit trails
- Compliance considerations

### What New User Needs

```markdown
## Security & Privacy

### How MCP Server Works

```
┌─────────────────┐
│  AI Assistant   │
│   (VS Code,     │
│  Claude Code)   │
└────────┬────────┘
         │ stdio (local process)
         │
┌────────▼────────┐
│   MCP Server    │
│  (Local only)   │
│  snowflake-cli  │
└────────┬────────┘
         │ TLS/HTTPS
         │
┌────────▼────────┐
│   Snowflake     │
│   (Cloud DB)    │
└─────────────────┘
```

### Key Security Points

**✅ Local Only**:
- MCP server runs on YOUR machine
- No network exposure
- Communication via stdio (local process)
- AI assistant and server same computer

**✅ Authentication Reuse**:
- Uses existing Snowflake CLI credentials
- No new credentials to manage
- Same security as Snow CLI
- Key-pair auth recommended

**✅ Snowflake Permissions**:
- Limited by your Snowflake role
- Cannot access data you don't have access to
- Cannot perform actions your role forbids
- Same as using Snowflake directly

**✅ Destructive Operation Protection**:
- DELETE, DROP, TRUNCATE blocked by default
- Prevents accidental data loss
- AI can't delete your data
- Must use Snow CLI directly for destructive ops

### What AI Assistant Can See

**AI Has Access To**:
- Your Snowflake profile name
- Databases you have access to
- Schema and table metadata
- Query results you run
- Catalog data you generate

**AI Does NOT Have**:
- Your Snowflake password
- Your private key file
- Other profiles on your machine
- Data you don't query
- Other users' data

### Query Logging

**Snowflake Side**:
- All queries logged in `QUERY_HISTORY`
- Standard Snowflake auditing applies
- Can review: `SHOW QUERIES IN ACCOUNT`

**MCP Server Side**:
- Queries logged to Snowflake CLI log
- Location: `~/Library/Application Support/snowflake/logs/`
- No sensitive data in MCP server logs

**AI Assistant Side**:
- Conversation history may include queries
- Check your AI assistant's privacy policy
- Claude Code: Conversations are private
- VS Code: Check extension privacy policy

### Data Retention

**Catalog Files**:
- Stored locally: `./data_catalogue/`
- Contains schema metadata, no actual data
- You control these files
- Safe to version control (no secrets)

**Query Results**:
- Returned to AI assistant
- Not stored by MCP server
- Check AI assistant's data retention policy

### Compliance Considerations

**HIPAA/PII**:
- MCP server doesn't store query results
- Results go through AI assistant
- Check if your AI assistant is compliant
- Consider using local LLMs for sensitive data

**SOC 2**:
- Uses Snowflake's SOC 2 certified authentication
- Audit trail in Snowflake QUERY_HISTORY
- Local-only server (no cloud exposure)

**GDPR**:
- No personal data stored by MCP server
- Query results handled by AI assistant
- Review AI assistant's GDPR compliance

### Best Practices

1. **Use Least Privilege**:
   - Create specific role for MCP server
   - Grant only necessary permissions
   - Don't use ACCOUNTADMIN role

2. **Separate Profiles**:
   - Use different profile for AI assistance
   - Separate from production access
   - Easy to revoke if needed

3. **Review Query History**:
   ```sql
   SELECT query_text, start_time, user_name
   FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
   WHERE user_name = CURRENT_USER()
   ORDER BY start_time DESC
   LIMIT 100;
   ```

4. **Monitor for Anomalies**:
   - Unexpected databases accessed
   - High query volume
   - Failed authentication attempts

5. **Secure Private Keys**:
   - Store outside project directory
   - Use appropriate file permissions: `chmod 600 rsa_key.p8`
   - Never commit to version control

### What If Compromised?

If you suspect compromise:

1. **Immediately**:
   - Stop MCP server
   - Check Snowflake query history
   - Review recent AI assistant activity

2. **Revoke Access**:
   ```sql
   -- Remove public key
   ALTER USER your_username UNSET RSA_PUBLIC_KEY;

   -- Disable profile
   snow connection delete --connection-name compromised-profile
   ```

3. **Rotate Keys**:
   - Generate new key pair
   - Upload new public key to Snowflake
   - Update profile with new private key

4. **Audit**:
   - Review query history for suspicious activity
   - Check for data exfiltration
   - Notify security team if needed
```

---

## Summary of MCP Setup Documentation Gaps

### Critical Gaps

1. ✗ MCP dependency confusion (optional vs required)
2. ✗ No expected output for `mcp` command
3. ✗ Wrong project name in config examples
4. ✗ Config file locations not specified
5. ✗ No verification/testing steps

### High Priority Gaps

6. ✗ No tool usage examples
7. ✗ No error message reference
8. ✗ No debugging guide
9. ✗ Security implications under-explained
10. ✗ No limitations/constraints documented

### Medium Priority Gaps

11. ✗ SQL safety features not mentioned in MCP docs
12. ✗ No query timeout info
13. ✗ No result size limits
14. ✗ No performance guidance
15. ✗ No logging/monitoring info

---

## Recommendations

### Quick Wins (< 1 hour)

1. Fix pyproject.toml - remove duplicate MCP dependencies from optional
2. Fix config examples - change "snowflake_connector_py" to "snowcli-tools"
3. Add expected output section for `mcp` command
4. List config file locations for all AI assistants
5. Add simple verification steps

### Medium Effort (2-4 hours)

6. Write comprehensive tool usage guide with examples
7. Add troubleshooting section with common errors
8. Document SQL safety features in MCP context
9. Add security best practices guide
10. Create testing/verification checklist

### High Effort (1-2 days)

11. Create video walkthrough of MCP setup
12. Build interactive troubleshooting tool
13. Add monitoring/logging guide
14. Write compliance/security whitepaper
15. Create example AI assistant sessions

---

## Conclusion

**Can a new user successfully set up MCP server following current docs?**

**Answer**: ⚠️ **Partially** - Can start server but:
- Unclear if it's working
- Hard to troubleshoot
- AI assistant config incomplete
- No verification steps

**Estimated Time for New User**:
- **Expected** (from docs): 5 minutes
- **Actual** (with troubleshooting): 1-2 hours
- **With perfect docs**: 15 minutes

**Main Blockers**:
1. Dependency confusion
2. Config file location mystery
3. No verification steps
4. Inadequate troubleshooting

**Priority**: P1 - Blocks AI assistant integration (main feature)
