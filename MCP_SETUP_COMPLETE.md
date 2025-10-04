# MCP Server Setup Complete ✅

**Date**: January 4, 2025  
**Status**: Ready for testing with droid

---

## Setup Summary

### ✅ Step 1: Snowflake Profile Configuration

**Found existing profiles**:
- `mystenlabs-keypair` (default) - RSA key authentication
  - Account: `HKB47976.us-west-2`
  - User: `evan.kim@mystenlabs.com`
  - Database: `PIPELINE_V2_GROOT_DB`
  - Schema: `PIPELINE_V2_GROOT_SCHEMA`
  - Warehouse: `PRESET_WH`
  - Role: `SECURITYADMIN`
  - Auth: `SNOWFLAKE_JWT`
  - Private Key: `<configured>`

- `evan-oauth` - OAuth browser authentication
  - Same account and database settings
  - Auth: `externalbrowser`

**Selected profile**: `mystenlabs-keypair` (default profile with keypair authentication)

### ✅ Step 2: MCP Server Configuration

**Updated**: `~/.factory/mcp.json`

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "cwd": "/Users/evandekim/Documents/snowcli_tools",
      "env": {
        "SNOWFLAKE_PROFILE": "mystenlabs-keypair"
      }
    }
  }
}
```

This configuration:
- Uses `uv` to run the MCP server
- Sets working directory to the project root
- Uses the `mystenlabs-keypair` profile for Snowflake authentication
- Server name: `snowcli-tools`

### ✅ Step 3: Verification Tests

**Test script**: `test_mcp_server_startup.py`

**Results**: All 3/3 tests passed ✅

1. **Profile exists**: ✅
   - `mystenlabs-keypair` profile found and configured
   
2. **SQL validation**: ✅
   - SELECT queries allowed (bug fix working)
   - Lowercase statement types working correctly
   
3. **MCP imports**: ✅
   - `ExecuteQueryTool` imports successfully
   - `HealthCheckTool` imports successfully
   - All MCP server components available

---

## Available MCP Tools

Once Factory restarts and loads the MCP server, you'll have access to:

### Query Tools
- **`execute_query`**: Execute SQL queries with validation
  ```python
  mcp__snowcli_tools__execute_query(statement="SELECT 1")
  ```

### Catalog Tools
- **`build_catalog`**: Build comprehensive data catalog
- **`get_catalog_summary`**: Get catalog summary
- **`preview_table`**: Preview table contents

### Lineage Tools
- **`query_lineage`**: Query object lineage
- **`build_dependency_graph`**: Build dependency graph

### Health & Diagnostics
- **`health_check`**: Get comprehensive health status
- **`test_connection`**: Validate Snowflake connectivity
- **`check_profile_config`**: Check profile configuration
- **`get_resource_status`**: Get resource availability status
- **`check_resource_dependencies`**: Check resource dependencies

---

## Testing with Droid

### Test Droid Created

**Location**: `~/.factory/droids/snowcli_tools_test_droid.md`

This specialized droid can test:
- SQL validation (SELECT, DELETE, DROP)
- MCP tool execution
- Profile configuration
- Error handling

### Example Test Queries

```python
# Test 1: Basic SELECT (should work)
execute_query(statement="SELECT 1")

# Test 2: Current timestamp
execute_query(statement="SELECT CURRENT_TIMESTAMP()")

# Test 3: INFORMATION_SCHEMA query
execute_query(statement="""
    SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'PIPELINE_V2_GROOT_SCHEMA'
    LIMIT 10
""")

# Test 4: Blocked operation (should show alternatives)
execute_query(statement="DELETE FROM test_table")
```

---

## Next Steps

### To Start Using the MCP Server

1. **Restart Factory** (if not already done)
   - The MCP server will auto-start when Factory loads
   - It will connect using the `mystenlabs-keypair` profile

2. **Test basic query** in any chat:
   ```python
   mcp__snowcli_tools__execute_query(statement="SELECT 1")
   ```

3. **Run the test droid**:
   - Start a new task with the droid
   - Ask it to test the MCP server
   - It will run through validation tests

### Expected Behavior

**SELECT queries** (after bug fix):
```
✅ Success - Returns results
```

**Blocked operations** (DELETE, DROP, TRUNCATE):
```
❌ ValueError with safe alternatives:
  Safe alternatives:
    soft_delete: UPDATE table SET deleted_at = CURRENT_TIMESTAMP()...
    create_view: CREATE VIEW active_table AS SELECT * FROM...
```

---

## Troubleshooting

### If MCP server doesn't start

1. Check MCP server logs:
   ```bash
   cd /Users/evandekim/Documents/snowcli_tools
   SNOWFLAKE_PROFILE=mystenlabs-keypair uv run snowflake-cli mcp
   ```

2. Verify profile:
   ```bash
   .venv/bin/snow connection list
   ```

3. Test manually:
   ```bash
   .venv/bin/python test_mcp_server_startup.py
   ```

### If queries fail

1. **Profile validation error**: Check that RSA key file exists and is configured correctly

2. **Permission error**: Verify SECURITYADMIN role has access

3. **Connection timeout**: Check network/VPN connection to Snowflake

---

## Files Created/Modified

### Modified
- `~/.factory/mcp.json` - Added snowcli-tools MCP server configuration

### Created
- `~/.factory/droids/snowcli_tools_test_droid.md` - Test droid for MCP
- `test_mcp_server_startup.py` - Startup verification tests
- `MCP_SETUP_COMPLETE.md` - This file

### Previously Fixed (Committed)
- `src/snowcli_tools/config.py` - Lowercase statement types
- `src/snowcli_tools/sql_validation.py` - Capitalized display names
- `test_sql_validation_fix.py` - SQL validation tests
- `SQL_VALIDATION_FIX_SUMMARY.md` - Bug fix documentation

---

## Configuration Summary

```
MCP Server: snowcli-tools
Profile: mystenlabs-keypair
Database: PIPELINE_V2_GROOT_DB
Schema: PIPELINE_V2_GROOT_SCHEMA
Warehouse: PRESET_WH
Role: SECURITYADMIN
Auth: RSA Key Pair

Status: ✅ Ready for testing
```

---

**Ready to test!** The MCP server is fully configured and verified. Just restart Factory and start querying Snowflake! 🚀
