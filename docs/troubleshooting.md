# Troubleshooting Guide
**Version:** 1.10.0
**Last Updated:** 2025-10-06

---

## Quick Diagnostic Steps

Before diving into specific issues:

1. **Test Connection:** `snow connection test --connection "my-profile"`
2. **Check Profile:** `snow connection list`
3. **Verify Version:** `python -c "from snowcli_tools import __version__; print(__version__)"`
4. **Check MCP Config:** `cat .mcp.json | python -m json.tool`

---

## Common Issues

### 1. MCP Server Not Showing Up

**Symptoms:**
- AI assistant doesn't recognize Snowflake commands
- No MCP tools available
- Server not listed in MCP settings

**Diagnostic:**
```bash
# Check if config exists
ls -la .mcp.json

# Validate JSON syntax
cat .mcp.json | python -m json.tool

# Check Python path
which python
```

**Solutions:**

**A. Fix JSON Configuration**
```bash
# Common issue: Invalid JSON
cat .mcp.json
# Look for: missing commas, trailing commas, unquoted strings

# Fix example:
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {"SNOWFLAKE_PROFILE": "my-profile"}  # ← Remove trailing comma
    }
  }
}
```

**B. Use Absolute Python Path**
```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "/absolute/path/to/python",  // Use full path
      "args": ["-m", "snowcli_tools.mcp_server"]
    }
  }
}
```

**C. Restart AI Assistant**
- **Claude Code:** Quit (Cmd+Q) and reopen
- **Cursor:** Restart application
- **VS Code:** Reload window (Cmd+Shift+P → "Reload Window")

---

### 2. Connection Issues

**Symptoms:**
- "Profile not found"
- "Connection timeout"
- "Authentication failed"

**Diagnostic:**
```bash
# List available profiles
snow connection list

# Test specific profile
snow connection test --connection "my-profile"

# Check environment variable
echo $SNOWFLAKE_PROFILE
```

**Solutions:**

**A. Profile Not Found**
```bash
# Error: Profile 'default' not found
# Available profiles: evan-oauth, prod-keypair

# Solution: Set correct profile
export SNOWFLAKE_PROFILE=evan-oauth

# Or update .mcp.json
"env": {
  "SNOWFLAKE_PROFILE": "evan-oauth"
}
```

**B. Create Missing Profile**
```bash
# Interactive setup
snow connection add

# Or non-interactive
snow connection add \
  --connection-name "my-profile" \
  --account "myorg-myaccount" \
  --user "analyst" \
  --authenticator externalbrowser \
  --database "ANALYTICS" \
  --warehouse "COMPUTE_WH"
```

**C. Connection Timeout**
```bash
# Test Snowflake connectivity
snow sql -q "SELECT CURRENT_VERSION()" --connection my-profile

# If timeout:
# 1. Check network connectivity
# 2. Verify account name (should be: org-account)
# 3. Try different warehouse
# 4. Check Snowflake status: status.snowflake.com
```

---

### 3. Permission Issues

**Symptoms:**
- "Access denied"
- "Insufficient privileges"
- "Object does not exist or not authorized"

**Diagnostic:**
```sql
-- Check current role and permissions
SHOW GRANTS TO ROLE analyst_role;

-- Check warehouse access
SHOW WAREHOUSES;

-- Check database access
SHOW DATABASES;
```

**Required Permissions:**
```sql
-- Minimum for read-only operations
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE analyst_role;
GRANT USAGE ON DATABASE ANALYTICS TO ROLE analyst_role;
GRANT USAGE ON SCHEMA ANALYTICS.PUBLIC TO ROLE analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA INFORMATION_SCHEMA TO ROLE analyst_role;
```

**Solutions:**

**A. Request Permissions from Admin**
```
Email template:

Subject: Snowflake Read Permissions Request

Hi [Admin],

I need read-only access to use SnowCLI Tools (AI assistant for Snowflake).

Required permissions:
- USAGE on warehouse: COMPUTE_WH
- USAGE on database: ANALYTICS
- USAGE on schema: ANALYTICS.PUBLIC
- SELECT on INFORMATION_SCHEMA tables

Use case: AI-assisted data exploration (read-only)

Thanks!
```

**B. Switch to Role with Permissions**
```bash
# List available roles
snow sql -q "SHOW ROLES" --connection my-profile

# Use different role
snow connection add \
  --connection-name "my-profile-analyst" \
  --role "analyst_role" \
  ...
```

---

### 4. Tool Not Found

**Symptoms:**
- "Unknown tool: discover_table_purpose"
- "Tool 'xyz' not available"

**Diagnostic:**
```bash
# Check version
python -c "from snowcli_tools import __version__; print(__version__)"

# List available tools (in AI assistant)
"What MCP tools are available?"
```

**Solutions:**

**A. Tool Renamed in v1.10.0**
```python
# OLD (v1.9.0 and earlier)
discover_table_purpose(table_name="CUSTOMERS")

# NEW (v1.10.0+)
profile_table(table_name="CUSTOMERS")
```

**B. Update Package**
```bash
# Update to latest version
pip install --upgrade snowcli-tools

# Verify version
python -c "from snowcli_tools import __version__; print(__version__)"
# Should be: 1.10.0
```

---

### 5. Query Timeout

**Symptoms:**
- "Query timeout after 120s"
- Long-running queries fail

**Diagnostic:**
```python
# Test with small query
execute_query("SELECT 1")

# Test with known slow query
execute_query("SELECT COUNT(*) FROM large_table")
```

**Solutions:**

**A. Increase Timeout**
```python
# Default timeout: 120s
execute_query(
    statement="SELECT ... FROM large_table",
    timeout_seconds=600  # 10 minutes
)
```

**B. Optimize Query**
```sql
-- Add WHERE clause
SELECT * FROM orders WHERE date >= '2025-01-01'

-- Add LIMIT for testing
SELECT * FROM customers LIMIT 1000

-- Use aggregations instead of full scan
SELECT COUNT(*), AVG(amount) FROM orders
```

**C. Scale Warehouse**
```python
# Use larger warehouse
execute_query(
    statement="SELECT ...",
    warehouse="LARGE_WH",
    timeout_seconds=300
)
```

---

### 6. Module Not Found

**Symptoms:**
- "ModuleNotFoundError: No module named 'snowcli_tools'"
- "ImportError: cannot import name 'FastMCP'"

**Diagnostic:**
```bash
# Check if installed
pip list | grep snowcli-tools

# Check Python environment
which python
python --version
```

**Solutions:**

**A. Install Package**
```bash
# Install with uv (recommended)
uv pip install snowcli-tools

# Or with pip
pip install snowcli-tools

# Verify installation
python -c "import snowcli_tools; print('OK')"
```

**B. Virtual Environment Issues**
```bash
# Check if venv is activated
which python
# Should show: /path/to/.venv/bin/python

# Activate venv
source .venv/bin/activate  # Unix/Mac
.venv\Scripts\activate     # Windows

# Install in venv
pip install snowcli-tools
```

**C. Update .mcp.json with venv Path**
```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "snowcli_tools.mcp_server"]
    }
  }
}
```

---

### 7. Cache Issues

**Symptoms:**
- Stale results from `profile_table`
- Outdated catalog summaries
- Changes not reflected

**Diagnostic:**
```bash
# Check cache directories
ls -la ./lineage/
ls -la ./data_catalogue/

# Check cache age
stat ./data_catalogue/_catalog_metadata.json
```

**Solutions:**

**A. Force Refresh profile_table**
```python
profile_table(
    table_name="CUSTOMERS",
    force_refresh=True  # Bypass cache
)
```

**B. Rebuild Catalog**
```python
# Full rebuild
build_catalog(database="ANALYTICS")
```

**C. Clear Cache Manually**
```bash
# Remove lineage cache
rm -rf ./lineage/

# Remove catalog
rm -rf ./data_catalogue/

# Rebuild
build_catalog(database="ANALYTICS")
```

---

### 8. Large Table Issues

**Symptoms:**
- `profile_table` timing out on wide tables (>100 columns)
- `build_catalog` taking too long

**Diagnostic:**
```sql
-- Check table column count
SELECT COUNT(*)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'WIDE_TABLE';
```

**Solutions:**

**A. Increase Timeout for Wide Tables**
```python
profile_table(
    table_name="WIDE_TABLE",  # 200 columns
    timeout_seconds=180,       # 3 minutes
    include_ai_analysis=False  # Faster
)
```

**B. Profile Without AI for Speed**
```python
# Fast SQL profiling only
profile_table(
    table_name="LARGE_TABLE",
    include_ai_analysis=False,      # Skip AI (saves ~15s)
    include_relationships=False     # Skip relationships (saves ~10s)
)
# Completes in ~5s
```

**C. Batch with Reduced Features**
```python
# Profile multiple tables quickly
profile_table(
    table_name=["TABLE1", "TABLE2", "TABLE3"],
    include_ai_analysis=False  # Fast batch mode
)
```

---

## Advanced Troubleshooting

### Enable Debug Logging

```bash
# Set debug environment variables
export SNOWCLI_TOOLS_DEBUG=1
export MCP_DEBUG=1

# Run MCP server
SNOWFLAKE_PROFILE=my-profile python -m snowcli_tools.mcp_server

# Check logs
# (Output to stdout/stderr)
```

### Check Snowflake Query History

```sql
-- View recent queries
SELECT
  query_text,
  start_time,
  end_time,
  execution_status,
  error_message
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE USER_NAME = CURRENT_USER()
ORDER BY start_time DESC
LIMIT 50;
```

### Test MCP Server Manually

```bash
# Run server in terminal
SNOWFLAKE_PROFILE=my-profile python -m snowcli_tools.mcp_server

# Expected output:
# FastMCP 2.0 server starting...
# Profile validation: ✓
# Available tools: 9
# Server running (press Ctrl+C to stop)
```

---

## Error Code Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `-32001` | Connection Error | Check network, profile, credentials |
| `-32002` | Permission Error | Request necessary Snowflake permissions |
| `-32003` | Timeout Error | Increase timeout or optimize query |
| `-32004` | Profile Validation Error | Set valid SNOWFLAKE_PROFILE |
| `-32005` | Configuration Error | Check .mcp.json syntax and paths |

---

## Getting Help

### Before Asking for Help

Collect this information:

1. **Version:** `python -c "from snowcli_tools import __version__; print(__version__)"`
2. **Error Message:** Full error text
3. **Configuration:** `.mcp.json` (redact credentials)
4. **Logs:** Debug logs if available
5. **Snowflake Version:** `SELECT CURRENT_VERSION()`

### Where to Get Help

1. **Documentation:**
   - [INDEX](INDEX.md) - All documentation
   - [MCP Quick Start](mcp_quick_start.md) - Setup guide
   - [Security Guide](security.md) - Permission issues

2. **GitHub:**
   - [Issues](https://github.com/Evan-Kim2028/snowcli-tools/issues) - Report bugs
   - [Discussions](https://github.com/Evan-Kim2028/snowcli-tools/discussions) - Ask questions

3. **Community:**
   - Check existing issues first
   - Provide complete information
   - Include error messages

---

## Checklist for Common Problems

### MCP Server Issues
- [ ] `.mcp.json` exists and is valid JSON
- [ ] Python path is absolute, not relative
- [ ] AI assistant restarted after config changes
- [ ] Package installed: `pip list | grep snowcli-tools`

### Connection Issues
- [ ] Profile exists: `snow connection list`
- [ ] Profile works: `snow connection test --connection "my-profile"`
- [ ] Environment variable set: `echo $SNOWFLAKE_PROFILE`
- [ ] Network connectivity: ping snowflake account

### Permission Issues
- [ ] Role has USAGE on warehouse
- [ ] Role has USAGE on database/schema
- [ ] Role has SELECT on INFORMATION_SCHEMA
- [ ] Verified with: `SHOW GRANTS TO ROLE your_role;`

### Performance Issues
- [ ] Query has WHERE clause (not full table scan)
- [ ] Timeout increased for large tables
- [ ] Using appropriate warehouse size
- [ ] Cache cleared if results seem stale

---

## See Also

- **[MCP Quick Start](mcp_quick_start.md)** - Setup guide
- **[Security Guide](security.md)** - Permission requirements
- **[Tools Reference](api/TOOLS_REFERENCE.md)** - Tool documentation
- **[Workflows Guide](workflows.md)** - Common patterns

---

**Last Updated:** 2025-10-06
**Version:** 1.10.0
**Need Help?** [Open a GitHub Issue](https://github.com/Evan-Kim2028/snowcli-tools/issues)
