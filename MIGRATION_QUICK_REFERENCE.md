# V2.0 Migration Quick Reference

**Last Updated**: 2025-10-07 | [Full Guide](BREAKING_CHANGES_V2.0.md)

## 30-Second Summary

```
snowcli-tools (CLI + MCP) → nanuk-mcp (MCP only)
Package renamed  ✓ CLI removed  ✓ MCP-first architecture
95% of users: 5-10 min migration
 5% of users: 1-2 hours migration
Timeline: Q2 2025 release → Dec 2025 EOL
```

---

## Migration by User Type

### MCP User? (95% of users)

**Time**: 5-10 minutes | **Impact**: LOW

```bash
# 1. Uninstall old
pip uninstall snowcli-tools

# 2. Install new
pip install nanuk-mcp

# 3. Update MCP config
# Change: "snowflake-tools" → "nanuk-mcp"
# Change: "python -m snowcli_tools.mcp_server" → "nanuk-mcp"

# 4. Restart MCP client
# Done!
```

**Automated**: `python migrate_mcp_config.py`

---

### CLI User? (5% of users)

**Time**: 1-2 hours | **Impact**: HIGH

**Choose One:**

**Option A: AI Assistant (RECOMMENDED)**
```
Old: snowflake-cli catalog --database MYDB
New: "Build a catalog for MYDB database" (tell Claude)
```

**Option B: MCP CLI**
```bash
Old: snowflake-cli catalog --database MYDB
New: mcp run nanuk-mcp build_catalog database=MYDB
```

**Option C: Python API**
```python
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.context import create_service_context

context = create_service_context()
service = CatalogService(context=context)
result = await service.build_catalog(database="MYDB")
```

---

### CI/CD User? (15% of users)

**Time**: 2-4 hours | **Impact**: MODERATE

**Bash Script Migration:**
```bash
# OLD v1.x
snowflake-cli catalog --database ANALYTICS_DB
snowflake-cli depgraph --database ANALYTICS_DB

# NEW v2.0 - Convert to Python
python scripts/migrate_bash_script.py pipeline.sh
# Generates: pipeline_v2.py
```

**Or Stay on v1.x until Dec 2025**

---

### Library User? (10% of users)

**Time**: 15-30 minutes | **Impact**: MODERATE

```python
# Find & Replace in your codebase:
from snowcli_tools → from nanuk_mcp

# Automated:
python migrate_imports.py /path/to/your/project
```

**No API changes** - only import paths!

---

## Command Cheat Sheet

| v1.x CLI | v2.0 MCP Tool |
|----------|---------------|
| `catalog --database DB` | `build_catalog(database="DB")` |
| `lineage TABLE` | `query_lineage(object_name="TABLE")` |
| `depgraph --database DB` | `build_dependency_graph(database="DB")` |
| `query "SELECT ..."` | `execute_query(statement="SELECT ...")` |
| `preview TABLE` | `preview_table(table_name="TABLE")` |
| `verify` | `test_connection()` |

[Complete mapping →](BREAKING_CHANGES_V2.0.md#complete-cli--mcp-command-mapping)

---

## Timeline

| Date | What Happens |
|------|--------------|
| **Q2 2025** | v2.0.0 releases; v1.x enters maintenance |
| **Dec 31, 2025** | v1.x end of life |
| **Q1 2026** | v1.x removed from PyPI |

**You have 18 months** to migrate from v1.x

---

## Installation Changes

```bash
# OLD
pip install snowcli-tools

# NEW
pip install nanuk-mcp
```

---

## MCP Configuration Changes

### OLD (v1.x)
```json
{
  "mcpServers": {
    "snowflake-tools": {
      "command": "python",
      "args": ["-m", "snowcli_tools.mcp_server"],
      "env": {"SNOWFLAKE_PROFILE": "my-profile"}
    }
  }
}
```

### NEW (v2.0)
```json
{
  "mcpServers": {
    "nanuk-mcp": {
      "command": "nanuk-mcp",
      "env": {"SNOWFLAKE_PROFILE": "my-profile"}
    }
  }
}
```

**Config file location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

---

## Import Changes (Library Users)

```python
# OLD
from snowcli_tools.catalog import CatalogService
from snowcli_tools.lineage import LineageQueryService
from snowcli_tools.mcp_server import main

# NEW
from nanuk_mcp.catalog import CatalogService
from nanuk_mcp.lineage import LineageQueryService
from nanuk_mcp.mcp_server import main
```

**Everything else is identical!**

---

## Migration Tools

### 1. MCP Config Updater
```bash
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_mcp_config.py
python migrate_mcp_config.py
```

### 2. Import Path Migrator
```bash
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_imports.py
python migrate_imports.py /path/to/project
```

### 3. CLI Command Translator
```bash
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/translate_cli_to_mcp.py
python translate_cli_to_mcp.py
```

### 4. Bash Script Migrator
```bash
curl -O https://raw.githubusercontent.com/Evan-Kim2028/nanuk-mcp/main/scripts/migrate_bash_script.py
python migrate_bash_script.py pipeline.sh
```

---

## Top 5 FAQs

### 1. Why rename?
"nanuk-mcp" clearly identifies purpose (MCP server for Snowflake). "snowcli-tools" implied CLI-first, which is now inaccurate.

### 2. Why remove CLI?
95% of usage is MCP. Maintaining two interfaces doubles work. AI-first is the future.

### 3. Will v1.x work?
Yes, until Dec 31, 2025. Security patches only, no new features.

### 4. Are there API breaking changes?
NO! Only package name and import paths change. All APIs identical.

### 5. What if I can't migrate by Dec 2025?
- Option 1: Migrate MCP users now (easy), tackle automation later
- Option 2: Fork v1.x (not recommended - maintenance burden)
- Option 3: Contact for enterprise support agreement

---

## Get Help

- 📖 [Full Migration Guide](BREAKING_CHANGES_V2.0.md) - Complete documentation
- 🤖 [Migration Scripts](https://github.com/Evan-Kim2028/nanuk-mcp/tree/main/scripts) - Automated tools
- 💬 [Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions) - Ask questions
- 🐛 [Issues](https://github.com/Evan-Kim2028/nanuk-mcp/issues) - Report problems
- 📧 [Email](mailto:ekcopersonal@gmail.com) - Direct support

---

## Pre-Flight Checklist

**Before Migration:**
- [ ] Identify your user type (MCP/CLI/CI-CD/Library)
- [ ] Read appropriate migration section
- [ ] Download migration tools
- [ ] Backup existing configuration
- [ ] Test in development environment

**During Migration:**
- [ ] Uninstall snowcli-tools
- [ ] Install nanuk-mcp
- [ ] Update configurations/imports
- [ ] Run migration tools
- [ ] Test functionality

**After Migration:**
- [ ] Verify all features work
- [ ] Update documentation/runbooks
- [ ] Remove v1.x dependencies
- [ ] Monitor for issues
- [ ] Celebrate! 🎉

---

## Common Errors & Fixes

### Error: "Command 'nanuk-mcp' not found"
```bash
# Fix: Reinstall package
pip install --force-reinstall nanuk-mcp
```

### Error: "No module named 'nanuk_mcp'"
```bash
# Fix: Check Python environment
which python
pip show nanuk-mcp
```

### Error: MCP server won't start
```bash
# Fix: Verify Snowflake profile
snow connection list
export SNOWFLAKE_PROFILE=my-profile
```

### Error: "ModuleNotFoundError: No module named 'snowcli_tools'"
```python
# Fix: Update imports
# from snowcli_tools → from nanuk_mcp
python migrate_imports.py .
```

---

## One-Liner Migrations

### MCP User (Most Common)
```bash
pip uninstall snowcli-tools && pip install nanuk-mcp && python migrate_mcp_config.py
```

### Library User
```bash
pip uninstall snowcli-tools && pip install nanuk-mcp && python migrate_imports.py .
```

### Check Current Version
```python
import nanuk_mcp
print(nanuk_mcp.__version__)  # Should show 2.0.0
```

---

**Need More Details?** Read the [Complete Migration Guide](BREAKING_CHANGES_V2.0.md)