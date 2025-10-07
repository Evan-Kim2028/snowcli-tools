# File-by-File Documentation Issues

**Evaluation Date:** October 7, 2025
**Project:** SnowCLI Tools v1.9.0

---

## /Users/evandekim/Documents/snowcli_tools/README.md

### Version Inconsistencies
- **Line 7:** `## ✨ v1.7.0 New Features`
  - **Issue:** Should be v1.9.0 (per pyproject.toml)
  - **Fix:** Change to `## ✨ v1.9.0 Features`

- **Line 209:** `Version 1.5.0 | Built with ❤️`
  - **Issue:** Two versions behind current
  - **Fix:** Change to `Version 1.9.0 | Built with ❤️`

### Broken Links
- **Line 15:** `[📖 See Release Notes](./RELEASE_NOTES.md)`
  - **Issue:** File exists but only covers v1.7.0, outdated
  - **Fix:** Update RELEASE_NOTES.md or remove link

- **Line 164:** `**[MCP Integration](docs/mcp-integration.md)**`
  - **Issue:** File does not exist
  - **Fix:** Change to `docs/mcp/mcp_server_user_guide.md`

- **Line 164:** `**[API Reference](docs/api-reference.md)**`
  - **Issue:** File does not exist
  - **Fix:** Change to `docs/api/README.md`

- **Line 165:** `**[Configuration Guide](docs/configuration.md)**`
  - **Issue:** File does not exist (CRITICAL - referenced 4+ times)
  - **Fix:** Create docs/configuration.md

- **Line 167:** `**[Contributing](CONTRIBUTING.md)**`
  - **Issue:** File does not exist
  - **Fix:** Create CONTRIBUTING.md or remove link

- **Line 199:** `[GitHub Issues](link-to-issues)`
  - **Issue:** Placeholder link
  - **Fix:** Change to `https://github.com/Evan-Kim2028/snowcli-tools/issues`

- **Line 201:** `[Discord/Slack community link]`
  - **Issue:** Placeholder link
  - **Fix:** Add actual link or remove

### Content Issues
- **Lines 23-24:** Installation instruction
  ```bash
  pip install snowcli-tools
  ```
  - **Issue:** Conflicts with getting-started.md which says "when published"
  - **Fix:** Clarify if this is published or not

- **Line 32:** Verify command has no expected output
  ```bash
  snowflake-cli verify -p my-profile
  ```
  - **Fix:** Add expected output example

---

## /Users/evandekim/Documents/snowcli_tools/docs/getting-started.md

### Version Inconsistencies
- **Line 250:** `*Version 1.5.0 | Updated: 2025-09-28*`
  - **Issue:** Four versions behind
  - **Fix:** Change to `*Version 1.9.0 | Updated: 2025-10-07*`

### Missing Repository URL
- **Line 15:** `git clone <repository-url>`
  - **Issue:** Placeholder, users cannot clone
  - **Fix:** `git clone https://github.com/Evan-Kim2028/snowcli-tools`

### Broken Links
- **Line 238:** `[MCP Integration](./mcp-integration.md)`
  - **Issue:** File does not exist
  - **Fix:** Change to `[MCP Integration](mcp/mcp_server_user_guide.md)`

- **Line 239:** `[API Reference](./api-reference.md)`
  - **Issue:** File does not exist
  - **Fix:** Change to `[API Reference](api/README.md)`

- **Line 240:** `[Configuration](./configuration.md)`
  - **Issue:** File does not exist
  - **Fix:** Create configuration.md or remove link

### Content Issues
- **Lines 5-9:** Prerequisites inconsistent with README
  - **Issue:** Says "with uv package manager" (exclusive), README says "pip or uv"
  - **Fix:** Match README wording

- **Lines 21-22:** "Or install from PyPI (when published)"
  - **Issue:** Conflicts with README which implies it IS published
  - **Fix:** Remove "when published" or clarify status

- **Line 73:** Verify command missing expected output
  - **Issue:** Users don't know what success looks like
  - **Fix:** Add expected output example

- **Line 100:** MCP server start missing expected output
  - **Issue:** No success indicators
  - **Fix:** Add FastMCP banner example and health check output

- **Lines 33-42:** Key-pair authentication command
  - **Issue:** No explanation of how to generate the key
  - **Fix:** Add key generation steps before this command

---

## /Users/evandekim/Documents/snowcli_tools/docs/architecture.md

### Version Inconsistencies
- **Line 1:** `# SnowCLI Tools Architecture (v1.5.0)`
  - **Issue:** Four versions behind
  - **Fix:** Change to `(v1.9.0)`

- **Line 304:** `*Architecture Version: 1.5.0 | Last Updated: 2025-09-28*`
  - **Issue:** Outdated version
  - **Fix:** Change to `1.9.0 | Last Updated: 2025-10-07`

### Content Quality
- **Overall:** Excellent documentation, just needs version updates
- **Recommendation:** Use this as a template for other docs

---

## /Users/evandekim/Documents/snowcli_tools/docs/api/README.md

### Version Inconsistencies
- **Line 162:** `**Version:** v1.8.0`
  - **Issue:** One version behind
  - **Fix:** Change to `v1.9.0`

### Broken Links
- **Line 32:** References `check_profile_config` tool
  - **Issue:** Tool was removed in v1.9.0 migration
  - **Fix:** Remove reference

### Missing Tool Documentation
- **Documented:** execute_query, preview_table, build_catalog, test_connection, health_check
- **Missing:**
  - query_lineage (referenced but no doc)
  - build_dependency_graph (referenced but no doc)
  - get_catalog_summary (referenced but no doc)
  - profile_table (if it exists)

---

## /Users/evandekim/Documents/snowcli_tools/docs/api/tools/execute_query.md

### Broken Links
- **Line 134:** `[check_profile_config](check_profile_config.md)`
  - **Issue:** Tool removed in v1.9.0, file doesn't exist
  - **Fix:** Remove this link

- **Line 138:** `[SQL Permissions Configuration](../configuration.md#sql-permissions)`
  - **Issue:** configuration.md doesn't exist
  - **Fix:** Create configuration.md first

- **Line 139:** `[Error Catalog](../errors.md)`
  - **Issue:** errors.md doesn't exist
  - **Fix:** Create errors.md or remove link

### Content Quality
- **Overall:** Good documentation with clear examples
- **Recommendation:** Use as template for missing tool docs

---

## /Users/evandekim/Documents/snowcli_tools/docs/mcp/mcp_server_user_guide.md

### Content Quality
- **Overall:** EXCELLENT documentation
- **Strengths:**
  - Clear structure (What → Quick Start → Tools → Config → Examples)
  - Real conversation examples (Lines 154-185)
  - Comprehensive use cases (Lines 189-218)
  - Good troubleshooting section
- **Recommendation:** This should be the template for ALL documentation

### No Major Issues
- Version not mentioned (neutral - doesn't create conflict)
- All links appear to work
- Comprehensive and clear

---

## /Users/evandekim/Documents/snowcli_tools/docs/profile_validation_quickstart.md

### Version Inconsistencies
- **Line 4:** References v1.4.4+ in overview
  - **Issue:** Outdated version reference
  - **Fix:** Update to v1.9.0+

- **Line 22:** "Should show v1.4.4 or higher"
  - **Fix:** Change to "Should show v1.9.0 or higher"

### Content Quality
- **Overall:** Excellent troubleshooting guide
- **Strengths:**
  - Clear error-to-solution mapping
  - Interactive demos
  - Security best practices
- **Minor:** Update version references

---

## /Users/evandekim/Documents/snowcli_tools/RELEASE_NOTES.md

### Version Coverage
- **Current:** Only covers v1.7.0
- **Issue:** Missing v1.8.0, v1.9.0 release notes
- **Fix:** Add release notes for v1.8.0 and v1.9.0

### Broken References
- **Line 332:** `**Branch:** v1.7.0-upgrade`
  - **Issue:** Current branch is v1.10.0_discovery_assistant
  - **Fix:** Update branch reference or clarify this is archived

---

## /Users/evandekim/Documents/snowcli_tools/docs/v1.9.0_migration.md

### Content Quality
- **Overall:** Good migration guide
- **Covers:** Changes from v1.8.0 → v1.9.0
- **Useful for:** Understanding what features were removed

### No Major Issues
- Appropriate version references for migration guide
- Clear breaking changes listed
- Good examples

---

## Files That Should Exist But Don't

### CRITICAL (Referenced 4+ times)
1. **docs/configuration.md**
   - Referenced in: README.md, getting-started.md, execute_query.md
   - Priority: CRITICAL
   - Estimated effort: 2 hours to create

### HIGH (Referenced 2-3 times)
2. **docs/mcp-integration.md**
   - Referenced in: README.md, getting-started.md
   - Priority: HIGH
   - Solution: Redirect to docs/mcp/mcp_server_user_guide.md

3. **docs/api-reference.md**
   - Referenced in: README.md, getting-started.md
   - Priority: HIGH
   - Solution: Redirect to docs/api/README.md

### MEDIUM (Referenced 1 time)
4. **CONTRIBUTING.md**
   - Referenced in: README.md
   - Priority: MEDIUM
   - Estimated effort: 1 hour to create

5. **docs/api/errors.md**
   - Referenced in: execute_query.md
   - Priority: MEDIUM
   - Estimated effort: 1 hour to create

6. **docs/api/tools/check_profile_config.md**
   - Referenced in: execute_query.md
   - Priority: LOW (should remove reference, tool was removed)

---

## Duplicate Files to Remove

### Duplicates Found
1. **docs/mcp_server_user_guide.md**
   - **Duplicate of:** docs/mcp/mcp_server_user_guide.md
   - **Action:** Keep docs/mcp/ version, remove top-level version

2. **docs/mcp_server_technical_guide.md**
   - **Duplicate of:** docs/mcp/mcp_server_technical_guide.md
   - **Action:** Keep docs/mcp/ version, remove top-level version

### Verification Needed
- Check if files are identical or have diverged
- If diverged, merge changes before removing duplicates

---

## Files That Need CLI Documentation

### Currently CLI Documentation Scattered Across:
- README.md (examples only)
- getting-started.md (examples only)
- No comprehensive CLI reference exists

### Recommended New File
**docs/cli-reference.md**
- Complete command reference
- All options with defaults
- Practical examples for each command
- Error messages and solutions
- Piping and scripting examples

**Estimated effort:** 3 hours

---

## Summary Statistics

### Version References Audit
| File | Correct Version | Incorrect References | Status |
|------|----------------|---------------------|--------|
| pyproject.toml | v1.9.0 | 0 | ✅ Correct |
| README.md | v1.9.0 | 2 (v1.7.0, v1.5.0) | ❌ Fix |
| getting-started.md | v1.9.0 | 1 (v1.5.0) | ❌ Fix |
| architecture.md | v1.9.0 | 2 (v1.5.0) | ❌ Fix |
| api/README.md | v1.9.0 | 1 (v1.8.0) | ❌ Fix |
| profile_validation_quickstart.md | v1.9.0 | 2 (v1.4.4) | ❌ Fix |
| RELEASE_NOTES.md | Multiple | N/A (covers v1.7.0) | ⚠️ Update |

### Link Health Audit
| File | Total Links | Working | Broken | Status |
|------|-------------|---------|--------|--------|
| README.md | 8 | 3 | 5 | ❌ Critical |
| getting-started.md | 6 | 2 | 4 | ❌ Critical |
| execute_query.md | 5 | 2 | 3 | ❌ High |
| architecture.md | 0 | 0 | 0 | ✅ Good |
| api/README.md | 3 | 2 | 1 | ⚠️ Medium |

### File Status Summary
- **✅ Excellent:** 2 files (mcp_server_user_guide.md, architecture.md)
- **⚠️ Good but needs updates:** 3 files (api/README.md, v1.9.0_migration.md, profile_validation_quickstart.md)
- **❌ Critical issues:** 3 files (README.md, getting-started.md, execute_query.md)
- **Missing:** 6 critical files (configuration.md, etc.)
- **Duplicates:** 2 files to remove

---

## Quick Fix Commands

### Version Updates (30 minutes)
```bash
cd /Users/evandekim/Documents/snowcli_tools

# README.md
sed -i '' 's/v1\.7\.0 New Features/v1.9.0 Features/g' README.md
sed -i '' 's/Version 1\.5\.0/Version 1.9.0/g' README.md

# getting-started.md
sed -i '' 's/Version 1\.5\.0/Version 1.9.0/g' docs/getting-started.md
sed -i '' 's/2025-09-28/2025-10-07/g' docs/getting-started.md

# architecture.md
sed -i '' 's/(v1\.5\.0)/(v1.9.0)/g' docs/architecture.md
sed -i '' 's/Architecture Version: 1\.5\.0/Architecture Version: 1.9.0/g' docs/architecture.md
sed -i '' 's/2025-09-28/2025-10-07/g' docs/architecture.md

# api/README.md
sed -i '' 's/v1\.8\.0/v1.9.0/g' docs/api/README.md
```

### Create Missing Redirects (5 minutes)
```bash
# Create redirect files
echo "# MCP Integration\n\nSee [MCP Server User Guide](mcp/mcp_server_user_guide.md)" > docs/mcp-integration.md
echo "# API Reference\n\nSee [API Documentation](api/README.md)" > docs/api-reference.md
```

---

**Generated:** October 7, 2025
**Purpose:** Quick reference for documentation fixes
**Use:** Check off issues as they're resolved
