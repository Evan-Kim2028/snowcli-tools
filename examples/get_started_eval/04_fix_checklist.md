# Documentation Fix Checklist

**Project:** SnowCLI Tools
**Date Created:** October 7, 2025
**Estimated Total Time:** 20 hours (spread over 3-4 weeks)

---

## Priority 1: Critical Blockers (Est. 6 hours)

### Version Consistency (Est. 30 minutes)
- [ ] Update README.md line 7: Change "v1.7.0" to "v1.9.0"
- [ ] Update README.md line 209: Change "Version 1.5.0" to "Version 1.9.0"
- [ ] Update getting-started.md line 250: Change "1.5.0" to "1.9.0"
- [ ] Update architecture.md line 1: Change "v1.5.0" to "v1.9.0"
- [ ] Update architecture.md line 304: Change "1.5.0" to "1.9.0"
- [ ] Review api/README.md: Update version references as needed
- [ ] Add note about v1.10.0 branch if needed in README

### Missing Core Documentation (Est. 4 hours)

#### Create docs/configuration.md
- [ ] Copy structure from mcp_server_user_guide.md (it's good)
- [ ] Add sections:
  - Configuration file location (`~/.snowcli-tools/config.yml`)
  - Environment variables (SNOWFLAKE_PROFILE, etc.)
  - SQL permissions configuration
  - Timeout settings
  - Catalog/lineage directory settings
- [ ] Include complete example config.yml
- [ ] Add troubleshooting section

#### Create or Redirect docs/mcp-integration.md
- [ ] Option A: Redirect to docs/mcp/mcp_server_user_guide.md
- [ ] Option B: Create new file that links to both user guide and technical guide
- [ ] Recommendation: Create small file with:
  ```markdown
  # MCP Integration Guide

  For comprehensive MCP integration documentation, see:
  - [MCP Server User Guide](mcp/mcp_server_user_guide.md) - Setup and usage
  - [MCP Server Technical Guide](mcp/mcp_server_technical_guide.md) - Architecture details
  - [MCP Architecture](mcp/mcp_architecture.md) - Design patterns
  ```

#### Create or Redirect docs/api-reference.md
- [ ] Redirect to docs/api/README.md with note:
  ```markdown
  # API Reference

  See [API Documentation](api/README.md) for complete API reference.
  ```

### Fix Broken Links (Est. 1 hour)
- [ ] README.md line 164: Update MCP Integration link to `mcp/mcp_server_user_guide.md`
- [ ] README.md line 164: Update API Reference link to `api/README.md`
- [ ] README.md line 199: Add actual GitHub Issues URL
- [ ] getting-started.md line 238: Update MCP Integration link
- [ ] getting-started.md line 239: Update API Reference link
- [ ] getting-started.md line 240: Update Configuration link
- [ ] execute_query.md line 134: Remove check_profile_config link (tool removed)
- [ ] execute_query.md line 138: Update configuration.md link

### Repository URL Fix (Est. 5 minutes)
- [ ] getting-started.md line 15: Replace `<repository-url>` with `https://github.com/Evan-Kim2028/snowcli-tools`

### Remove Duplicates (Est. 30 minutes)
- [ ] Decide: Keep docs/mcp/*.md or docs/*mcp*.md?
- [ ] Recommendation: Keep docs/mcp/ directory structure
- [ ] Remove docs/mcp_server_user_guide.md (duplicate of docs/mcp/mcp_server_user_guide.md)
- [ ] Remove docs/mcp_server_technical_guide.md (duplicate)
- [ ] Add redirects if needed

---

## Priority 2: Getting Started Improvements (Est. 6 hours)

### Clarify Installation (Est. 2 hours)

#### Update README.md Quick Start
- [ ] Add decision section before installation:
  ```markdown
  ## Installation

  Choose your installation method:

  ### For Users (Recommended)
  Install from PyPI for stable releases:
  ```bash
  pip install snowcli-tools
  ```

  ### For Developers
  Install from source for latest features:
  ```bash
  git clone https://github.com/Evan-Kim2028/snowcli-tools
  cd snowcli-tools
  uv sync
  ```
  ```

#### Update getting-started.md
- [ ] Remove "when published" language if package IS published
- [ ] Add clear sections: "User Installation" vs "Developer Installation"
- [ ] Explain when to use `uv run` prefix vs direct commands
- [ ] Add decision tree or table

### Add Success Indicators (Est. 2 hours)
- [ ] README.md line 32: Add expected output for verify command
- [ ] getting-started.md line 73: Add expected output for verify
- [ ] getting-started.md line 100: Add expected output for MCP server start
- [ ] Add "What Success Looks Like" callout boxes throughout

### Create Authentication Guide (Est. 2 hours)

#### Create docs/getting-started/authentication.md
- [ ] Section 1: Authentication Methods Overview
- [ ] Section 2: Key-Pair Authentication (End-to-End)
  - [ ] Generate key pair (openssl commands)
  - [ ] Extract public key
  - [ ] Upload to Snowflake (link to Snowflake docs)
  - [ ] Create profile with key
  - [ ] Test connection
- [ ] Section 3: OAuth/SSO Setup
- [ ] Section 4: Password Authentication (with security warning)
- [ ] Section 5: Troubleshooting Each Method

#### Update getting-started.md
- [ ] Line 29: Add link to full authentication guide
- [ ] Add key generation commands before snow connection add

### Account Identifier Help (Est. 30 minutes)
- [ ] Add callout box explaining account identifier format
- [ ] Include examples: `xy12345.us-east-1`, `abc123.europe-west1`
- [ ] Link to Snowflake documentation
- [ ] Explain how to find your account identifier

---

## Priority 3: CLI Documentation (Est. 4 hours)

### Create CLI Reference (Est. 3 hours)

#### Create docs/cli-reference.md
- [ ] Command overview section
- [ ] Global options (`-p`, `-c`, etc.)
- [ ] Commands:
  - [ ] `snowflake-cli query` - Execute SQL
  - [ ] `snowflake-cli catalog` - Build catalog
  - [ ] `snowflake-cli lineage` - Analyze lineage
  - [ ] `snowflake-cli depgraph` - Dependency graph
  - [ ] `snowflake-cli verify` - Test connection
  - [ ] `snowflake-cli mcp` - Start MCP server
- [ ] Each command should include:
  - Description
  - All options with types and defaults
  - 2-3 practical examples
  - Common errors and solutions

### Create Automation Guide (Est. 1 hour)

#### Create docs/guides/automation.md
- [ ] Scripting examples (bash, python)
- [ ] CI/CD integration patterns
- [ ] Cron job examples
- [ ] Error handling in scripts
- [ ] Output parsing examples

---

## Priority 4: Complete Tool Documentation (Est. 2 hours)

### Create Missing Tool Docs
- [ ] docs/api/tools/query_lineage.md
  - Parameters: object_name, direction, depth, format, etc.
  - Return format examples
  - Common use cases
- [ ] docs/api/tools/build_dependency_graph.md
  - Parameters and options
  - Output formats (JSON, DOT)
  - Visualization examples
- [ ] docs/api/tools/get_catalog_summary.md
  - What it returns
  - When to use vs build_catalog
- [ ] docs/api/tools/profile_table.md (if it exists in MCP)
  - Table profiling details
  - Statistical analysis

### Update Existing Tool Docs
- [ ] execute_query.md: Remove references to deleted tools
- [ ] All tool docs: Ensure version consistency
- [ ] All tool docs: Update configuration links

---

## Priority 5: Polish & Structure (Est. 2 hours)

### Create Documentation Index
- [ ] Create docs/README.md with categorized links:
  - Getting Started
  - User Guides
  - API Reference
  - Architecture
  - Advanced Topics

### Create Error Catalog
- [ ] docs/api/errors.md
  - Common ValueError scenarios
  - Common RuntimeError scenarios
  - Solutions for each
  - How to enable verbose errors

### Update Contributing Guide
- [ ] Create CONTRIBUTING.md if missing
- [ ] Include documentation contribution guidelines
- [ ] Link from README

---

## Testing & Validation (Ongoing)

### User Testing
- [ ] Have 3 new users follow getting-started.md
- [ ] Document where they get stuck
- [ ] Update docs based on feedback

### Link Validation
- [ ] Run automated link checker on all .md files
- [ ] Fix any broken internal links
- [ ] Verify external links are still valid

### Version Audit
- [ ] Search all .md files for version references
- [ ] Ensure all match pyproject.toml
- [ ] Add version to doc metadata

---

## Quick Reference

### Files That Need Version Updates
```bash
# Quick search command:
grep -r "1\.5\.0\|1\.7\.0\|1\.8\.0" docs/ README.md

# Files to update:
README.md (2 locations)
docs/getting-started.md (1 location)
docs/architecture.md (2 locations)
docs/api/README.md (check)
```

### Files to Create
```
docs/configuration.md (CRITICAL)
docs/mcp-integration.md (redirect)
docs/api-reference.md (redirect)
docs/cli-reference.md (NEW)
docs/guides/automation.md (NEW)
docs/getting-started/authentication.md (NEW)
docs/api/tools/query_lineage.md (NEW)
docs/api/tools/build_dependency_graph.md (NEW)
docs/api/tools/get_catalog_summary.md (NEW)
docs/api/errors.md (NEW)
docs/README.md (index)
CONTRIBUTING.md (if missing)
```

### Files to Remove (Duplicates)
```
docs/mcp_server_user_guide.md (keep docs/mcp/ version)
docs/mcp_server_technical_guide.md (keep docs/mcp/ version)
```

---

## Success Criteria

### Week 1 Success (Priority 1 Complete)
- [ ] All version references consistent (v1.9.0)
- [ ] Zero broken internal links
- [ ] Core docs exist (configuration, api-reference, mcp-integration)
- [ ] No duplicate files

### Week 2 Success (Priority 2 Complete)
- [ ] New user can complete getting-started.md without confusion
- [ ] Installation path is clear (user vs developer)
- [ ] Authentication has end-to-end guide
- [ ] All verification steps show expected output

### Week 3 Success (Priority 3 Complete)
- [ ] CLI has same quality documentation as MCP
- [ ] Automation guide exists with examples
- [ ] All MCP tools fully documented

### Final Success (All Priorities Complete)
- [ ] Documentation score improves from 6.5/10 to 8.5/10
- [ ] User testing shows <5% confusion rate on getting started
- [ ] Zero broken links
- [ ] Consistent version references throughout
- [ ] Both CLI and MCP well-documented

---

**Notes:**
- Check off items as you complete them
- Update time estimates based on actual time spent
- Add notes about any blockers or issues encountered
- Review this checklist weekly and adjust priorities as needed

**Created:** October 7, 2025
**Last Updated:** October 7, 2025
