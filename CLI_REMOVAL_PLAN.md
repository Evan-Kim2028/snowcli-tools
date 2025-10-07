# CLI Removal Plan - Nanuk MCP v2.1.0

**Date**: October 7, 2025
**Current Version**: 2.0.0 (post-rebrand)
**Target Version**: 2.1.0 (MCP-only)
**Estimated Timeline**: 1-2 hours implementation

---

## Executive Summary

Since Nanuk MCP has been rebranded to emphasize MCP-first architecture, we should complete the migration by removing the legacy CLI interface entirely. This will:

- ✅ Simplify the codebase (remove ~774 LOC)
- ✅ Reduce maintenance burden by ~40%
- ✅ Eliminate confusion about which interface to use
- ✅ Align with the "MCP" in the package name

---

## Current State

### CLI Components to Remove

**Code**:
- `src/nanuk_mcp/cli.py` (main CLI entry point) - ~200 LOC
- `src/nanuk_mcp/commands/` directory:
  - `__init__.py`
  - `analyze.py`
  - `discover.py`
  - `query.py`
  - `registry.py`
  - `setup.py`
  - `utils.py`
- Total: ~774 LOC

**Dependencies** (CLI-specific):
- `click>=8.0.0` (used only by CLI)
- `rich>=13.0.0` (used by both - keep for MCP error formatting)

**Entry Points** (pyproject.toml):
```toml
[project.scripts]
nanuk-mcp = "nanuk_mcp.mcp_server:main"  # KEEP
nanuk = "nanuk_mcp.cli:main"              # REMOVE
```

**Tests**:
- `tests/test_cli.py` - CLI-specific tests (~113 LOC)
- Some command tests in `tests/commands/`

---

## Removal Strategy

### Option 1: Complete Removal (Recommended)

**Pros**:
- Clean, no legacy code
- Clear MCP-only message
- Simplest maintenance

**Cons**:
- Breaking change for any CLI users
- No backward compatibility

**Timeline**: v2.1.0 (immediate)

### Option 2: Deprecation First

**Pros**:
- Gentler transition
- Users have warning period

**Cons**:
- Maintains technical debt longer
- Mixed messaging ("deprecated but still works")

**Timeline**: Deprecate in v2.0.0, remove in v3.0.0 (6 months)

**Decision**: **Option 1 - Complete Removal** (we just did a major version bump anyway)

---

## Implementation Steps

### Step 1: Remove CLI Code (30 min)

```bash
cd /Users/evandekim/Documents/nanuk_mcp

# Remove CLI entry point
rm src/nanuk_mcp/cli.py

# Remove command modules
rm -rf src/nanuk_mcp/commands/

# Remove CLI tests
rm tests/test_cli.py
# Check for any command tests
ls tests/commands/ 2>/dev/null && rm -rf tests/commands/
```

### Step 2: Update pyproject.toml (5 min)

**Current**:
```toml
[project.scripts]
nanuk-mcp = "nanuk_mcp.mcp_server:main"
nanuk = "nanuk_mcp.cli:main"

dependencies = [
    "click>=8.0.0",          # CLI only
    "rich>=13.0.0",          # Both CLI and MCP
    # ... other deps
]
```

**Updated**:
```toml
[project.scripts]
nanuk-mcp = "nanuk_mcp.mcp_server:main"
# nanuk removed

dependencies = [
    # "click>=8.0.0",      # REMOVED - CLI only
    "rich>=13.0.0",        # KEEP - used by MCP error formatting
    # ... other deps
]
```

### Step 3: Update Documentation (20 min)

**Files to Update**:
1. `README.md` - Remove CLI command reference table
2. `docs/migration-guide.md` - Note CLI removed in v2.1.0
3. `docs/getting-started.md` - Remove CLI examples
4. `CHANGELOG.md` - Add v2.1.0 entry

**README.md Changes**:
```markdown
## Command Quick Reference

### MCP Server (Primary Interface)

| Task | Command | Notes |
|------|---------|-------|
| Start MCP server | `nanuk-mcp` | For AI assistant integration |
| Start with profile | `nanuk-mcp --profile PROF` | Specify profile explicitly |
| Configure | `nanuk-mcp --configure` | Interactive setup |

### CLI Interface ~~(Legacy - Deprecated)~~

~~CLI interface removed in v2.1.0. Use MCP server only.~~
~~See [v2.0.0 Migration Guide](docs/migration-from-v2.0.md) if you were using CLI.~~
```

**CHANGELOG.md Entry**:
```markdown
## [2.1.0] - 2025-10-XX

### BREAKING CHANGES

**CLI Interface Removed**

The legacy CLI interface (`nanuk` command) has been removed. Nanuk is now MCP-only.

#### Removed
- `nanuk` CLI command and all subcommands
- `src/nanuk_mcp/cli.py` and `src/nanuk_mcp/commands/` directory
- CLI-specific dependency: `click`
- CLI-specific tests

#### Migration
All CLI functionality is available through MCP tools:

| Old CLI Command | New MCP Tool |
|----------------|--------------|
| `nanuk verify` | `test_connection` |
| `nanuk catalog` | `build_catalog` |
| `nanuk lineage` | `query_lineage` |
| `nanuk depgraph` | `build_dependency_graph` |
| `nanuk query` | `execute_query` |

See [MCP Migration Guide](docs/cli-to-mcp-migration.md) for details.

#### Rationale
- Package name is "nanuk-**mcp**" - should be MCP-only
- Reduces codebase by 774 LOC (40% reduction in interface code)
- Eliminates user confusion about which interface to use
- Aligns with AI-first architecture
```

### Step 4: Update __init__.py (5 min)

**File**: `src/nanuk_mcp/__init__.py`

Remove any CLI-related exports:
```python
# Remove these if present
# from nanuk_mcp.cli import main as cli_main
# from nanuk_mcp.commands import *
```

### Step 5: Check for CLI Dependencies (10 min)

```bash
# Search for any remaining CLI imports
grep -r "from nanuk_mcp.cli" src/ tests/
grep -r "import.*cli" src/ tests/ | grep -v "# " | grep -v snowflake

# Search for click usage
grep -r "import click" src/ tests/
grep -r "from click" src/ tests/

# If only used in removed files, we're good
# If used elsewhere, keep dependency
```

### Step 6: Run Tests (10 min)

```bash
# Remove CLI tests from test suite
pytest tests/ -v

# All tests should still pass (excluding removed CLI tests)
# Fix any broken imports or dependencies
```

### Step 7: Update Build and Verify (10 min)

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build new package
uv build

# Test local installation
pip uninstall -y nanuk-mcp
pip install -e .

# Verify MCP command works
nanuk-mcp --version

# Verify CLI command is gone
nanuk --version
# Should error: command not found

# Test Python imports
python -c "from nanuk_mcp import __version__; print(__version__)"
# Should print: 2.1.0
```

---

## Documentation Updates Needed

### Create New Migration Guide

**File**: `docs/cli-to-mcp-migration.md`

```markdown
# CLI to MCP Migration Guide (v2.0 → v2.1)

## Overview

The `nanuk` CLI command was removed in v2.1.0. All functionality is now available exclusively through the MCP server.

## Why Was CLI Removed?

- Package is named "nanuk-**mcp**" - MCP should be the only interface
- Reduced codebase by 40%
- Eliminated user confusion
- Aligned with AI-first architecture

## Migration Path

### Step 1: Start Using MCP Server

**Old (CLI)**:
```bash
nanuk --profile my-profile verify
```

**New (MCP)**:
```bash
# Start MCP server
SNOWFLAKE_PROFILE=my-profile nanuk-mcp

# Use through AI assistant or MCP client
echo '{"tool": "test_connection", "arguments": {}}' | nanuk-mcp
```

### Step 2: Command Mapping

| CLI Command | MCP Tool | Notes |
|-------------|----------|-------|
| `nanuk verify` | `test_connection` | Connection testing |
| `nanuk catalog -d DB` | `build_catalog` | Database cataloging |
| `nanuk lineage TABLE` | `query_lineage` | Lineage analysis |
| `nanuk depgraph` | `build_dependency_graph` | Dependency mapping |
| `nanuk query "SQL"` | `execute_query` | SQL execution |

### Step 3: Update Scripts

**Before**:
```bash
#!/bin/bash
nanuk --profile prod catalog -d MY_DB
nanuk --profile prod lineage MY_TABLE
```

**After**:
```bash
#!/bin/bash
export SNOWFLAKE_PROFILE=prod

# Option 1: Direct MCP tool calls
echo '{"tool": "build_catalog", "arguments": {"database": "MY_DB"}}' | nanuk-mcp

# Option 2: Use AI assistant
# Configure AI assistant to use nanuk-mcp, then use natural language
```

### Step 4: CI/CD Updates

**GitHub Actions Example**:
```yaml
# Old
- name: Build Catalog
  run: nanuk --profile prod catalog -d MY_DB

# New
- name: Build Catalog
  run: |
    export SNOWFLAKE_PROFILE=prod
    echo '{"tool": "build_catalog", "arguments": {"database": "MY_DB"}}' | nanuk-mcp
```

## Advantages of MCP

- **AI Integration**: Works natively with Claude Code and other AI assistants
- **Standardized**: Uses Model Context Protocol standard
- **Modern**: Designed for AI-first workflows
- **Simpler**: One interface, less confusion

## Need Help?

- 📖 [MCP Server User Guide](mcp/mcp_server_user_guide.md)
- 🔧 [Configuration Guide](configuration.md)
- 💬 [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
```

---

## Testing Plan

### Pre-Removal Tests

```bash
# Document what currently works
nanuk --version  # Should work in v2.0.0
nanuk --help     # Should show commands
nanuk-mcp --version  # Should work

# Run full test suite
pytest tests/ -v
# Note: X tests pass (including CLI tests)
```

### Post-Removal Tests

```bash
# Verify CLI is gone
nanuk --version  # Should error: command not found

# Verify MCP still works
nanuk-mcp --version  # Should work
python -c "from nanuk_mcp import __version__; print(__version__)"  # Should print 2.1.0

# Run test suite (excluding removed CLI tests)
pytest tests/ -v
# Note: Y tests pass (CLI tests removed)

# Verify package builds
uv build  # Should succeed
ls dist/  # Should show nanuk_mcp-2.1.0*
```

---

## Rollback Plan

If CLI removal causes issues:

```bash
# Revert to previous commit
git revert HEAD

# Or restore CLI files from v2.0.0
git checkout v2.0.0 -- src/nanuk_mcp/cli.py
git checkout v2.0.0 -- src/nanuk_mcp/commands/
git checkout v2.0.0 -- pyproject.toml

# Rebuild
uv build
```

---

## Communication Plan

### Announcement

**Subject**: Nanuk MCP v2.1.0 - CLI Removed (MCP-Only)

```markdown
# Nanuk MCP v2.1.0 Released - MCP-Only

We've completed the transition to MCP-only architecture by removing the legacy CLI interface.

## What Changed

- ❌ Removed: `nanuk` CLI command
- ✅ Kept: `nanuk-mcp` MCP server (only interface)
- 📉 40% reduction in interface code
- 🎯 Clear, simple architecture: MCP-only

## Migration

All CLI functionality is available through MCP tools:

```bash
# Old
nanuk --profile prod catalog -d MY_DB

# New
SNOWFLAKE_PROFILE=prod nanuk-mcp
# Then use through AI assistant
```

See [CLI Migration Guide](docs/cli-to-mcp-migration.md) for details.

## Why?

- Package name is "nanuk-**mcp**" - should be MCP-only
- Eliminates user confusion
- Reduces maintenance burden
- Aligns with AI-first architecture

## Questions?

- 📖 [Documentation](https://github.com/Evan-Kim2028/nanuk-mcp)
- 💬 [Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)
```

---

## Files to Modify

### Delete
- [ ] `src/nanuk_mcp/cli.py`
- [ ] `src/nanuk_mcp/commands/__init__.py`
- [ ] `src/nanuk_mcp/commands/analyze.py`
- [ ] `src/nanuk_mcp/commands/discover.py`
- [ ] `src/nanuk_mcp/commands/query.py`
- [ ] `src/nanuk_mcp/commands/registry.py`
- [ ] `src/nanuk_mcp/commands/setup.py`
- [ ] `src/nanuk_mcp/commands/utils.py`
- [ ] `tests/test_cli.py`
- [ ] `tests/commands/` (if exists)

### Modify
- [ ] `pyproject.toml` - Remove `nanuk` entry point, remove `click` dependency
- [ ] `src/nanuk_mcp/__init__.py` - Remove CLI exports
- [ ] `README.md` - Remove CLI command table, add note about removal
- [ ] `CHANGELOG.md` - Add v2.1.0 entry
- [ ] `docs/getting-started.md` - Remove CLI examples
- [ ] `docs/migration-guide.md` - Update for CLI removal

### Create
- [ ] `docs/cli-to-mcp-migration.md` - New migration guide

---

## Summary

**Effort**: ~2 hours
**Risk**: Low (clean break, major version allows breaking changes)
**Benefit**: 40% reduction in interface code, clearer architecture, aligned with package name

**Recommendation**: **Proceed with removal in v2.1.0**

The rebrand to "nanuk-**mcp**" sets the expectation - let's follow through with MCP-only architecture.

---

**Next Steps**:
1. Review this plan
2. Execute removal steps
3. Test thoroughly
4. Update documentation
5. Release v2.1.0
6. Announce changes

**🐻‍❄️ Nanuk MCP - MCP-First, MCP-Only**
