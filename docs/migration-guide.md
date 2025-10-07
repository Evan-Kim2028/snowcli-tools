# Migration Guide: CLI to MCP

This guide helps you migrate from the deprecated CLI interface to the modern MCP (Model Context Protocol) interface.

## Why Migrate?

### Benefits of MCP
- **AI-First Design**: Built for AI assistant integration
- **Modern Protocol**: Industry standard for tool integration
- **Better Error Handling**: Structured error responses
- **Future-Proof**: Aligns with emerging AI tool standards
- **Reduced Maintenance**: Single interface to maintain

### CLI Deprecation Timeline
- **v1.9.0**: Deprecation warnings added
- **v1.10.0**: CLI moved to legacy package
- **v2.0.0**: CLI removed from default installation (Q2 2026)
- **v3.0.0**: CLI completely removed (Q4 2026)

## Migration Checklist

- [ ] Review current CLI usage
- [ ] Install MCP dependencies (included by default)
- [ ] Configure MCP server
- [ ] Test MCP tools
- [ ] Update scripts/automation
- [ ] Remove CLI from workflow

## Command Mapping

| CLI Command | MCP Equivalent | Notes |
|-------------|----------------|-------|
| `nanuk verify` | `test_connection` tool | Connection testing |
| `nanuk catalog -d DB` | `build_catalog` tool | Database cataloging |
| `nanuk lineage TABLE` | `query_lineage` tool | Lineage analysis |
| `nanuk depgraph -d DB` | `build_dependency_graph` tool | Dependency mapping |
| `nanuk query "SQL"` | `execute_query` tool | SQL execution |
| `nanuk-mcp` | MCP server startup | Server management |

## Migration Examples

### Before (CLI)
```bash
# Test connection
nanuk --profile prod verify

# Build catalog
nanuk --profile prod catalog -d MY_DATABASE -o ./output

# Query lineage
nanuk --profile prod lineage MY_TABLE

# Execute query
nanuk --profile prod query "SELECT * FROM users LIMIT 10"
```

### After (MCP)
```json
{
  "tool": "test_connection",
  "arguments": {
    "profile": "prod"
  }
}

{
  "tool": "build_catalog",
  "arguments": {
    "database": "MY_DATABASE",
    "output_dir": "./output"
  }
}

{
  "tool": "query_lineage",
  "arguments": {
    "object_name": "MY_TABLE"
  }
}

{
  "tool": "execute_query",
  "arguments": {
    "statement": "SELECT * FROM users LIMIT 10"
  }
}
```

## MCP Server Setup

### 1. Start MCP Server
```bash
# Set profile environment variable
export SNOWFLAKE_PROFILE=my-profile

# Start MCP server
nanuk-mcp
```

### 2. Configure AI Assistant
Add to your AI assistant configuration:

```json
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "nanuk",
      "args": ["mcp"],
      "env": {
        "SNOWFLAKE_PROFILE": "my-profile"
      }
    }
  }
}
```

### 3. Test MCP Integration
```bash
# Test connection via MCP
echo '{"tool": "test_connection", "arguments": {}}' | nanuk-mcp

# Expected: JSON response with connection status
```

## Automation Migration

### Scripts Using CLI
**Before**:
```bash
#!/bin/bash
# Old script using CLI
nanuk --profile prod catalog -d MY_DB
nanuk --profile prod lineage MY_TABLE
```

**After**:
```bash
#!/bin/bash
# New script using MCP
export SNOWFLAKE_PROFILE=prod

# Start MCP server in background
nanuk-mcp &
MCP_PID=$!

# Send MCP requests
echo '{"tool": "build_catalog", "arguments": {"database": "MY_DB"}}' | nc localhost 8080
echo '{"tool": "query_lineage", "arguments": {"object_name": "MY_TABLE"}}' | nc localhost 8080

# Cleanup
kill $MCP_PID
```

### CI/CD Pipeline Updates
**Before**:
```yaml
# GitHub Actions using CLI
- name: Build Catalog
  run: nanuk --profile prod catalog -d MY_DB
```

**After**:
```yaml
# GitHub Actions using MCP
- name: Build Catalog
  run: |
    export SNOWFLAKE_PROFILE=prod
    echo '{"tool": "build_catalog", "arguments": {"database": "MY_DB"}}' | nanuk-mcp
```

## Troubleshooting

### Common Migration Issues

#### MCP Server Won't Start
**Error**: `MCP server failed to start`
**Solution**:
- Check profile configuration: `snow connection list`
- Verify environment variables: `echo $SNOWFLAKE_PROFILE`
- Test basic connection: `nanuk --profile my-profile verify`

#### Tool Not Found
**Error**: `Tool 'execute_query' not found`
**Solution**:
- Ensure MCP server is running
- Check tool name spelling
- Verify MCP protocol version

#### Authentication Issues
**Error**: `Authentication failed`
**Solution**:
- Use same profile as CLI
- Check key permissions
- Verify Snowflake credentials

### Getting Help

- 📖 [MCP Integration Guide](mcp-integration.md) - Complete MCP setup
- 🔧 [Configuration Guide](configuration.md) - Advanced settings
- 🐛 [Error Catalog](api/errors.md) - Common issues and solutions
- 💬 [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions) - Community help

## Legacy CLI Support

### If You Still Need CLI
```bash
# Install legacy CLI package (when available)
pip install "nanuk-mcp[legacy-cli]==1.9.x"
```

### Legacy CLI Limitations
- Security fixes only
- No new features
- Limited support
- Will be removed in v3.0.0

## Success Metrics

After migration, you should have:
- ✅ MCP server running successfully
- ✅ All CLI functionality available via MCP
- ✅ AI assistant integration working
- ✅ Automation scripts updated
- ✅ No CLI dependencies in new code

## Next Steps

1. **Complete Migration**: Follow this guide step by step
2. **Test Thoroughly**: Verify all functionality works via MCP
3. **Update Documentation**: Update internal docs to reference MCP
4. **Train Team**: Share MCP knowledge with your team
5. **Monitor**: Watch for new MCP features and improvements

---

*Need help with migration? Check the [Error Catalog](api/errors.md) or [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions).*
