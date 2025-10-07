# Quick Fixes - Immediate Documentation Changes Needed

**Date**: October 7, 2025
**Purpose**: Actionable list of immediate fixes to unblock new users

---

## P0 - Critical (Blocks All Users)

These issues prevent users from successfully installing and using the tool at all.

### Fix 1: Correct Command Syntax Throughout Docs

**Issue**: Documentation shows `-p` flag that doesn't exist

**Files to Fix**:
- `/Users/evandekim/Documents/snowcli_tools/README.md`
- `/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md`
- All other docs with command examples

**Search and Replace**:
```bash
# Find all occurrences
grep -r "\-p " docs/ README.md

# Wrong patterns to fix:
"verify -p my-profile"          → "verify" (use global --profile flag)
"catalog -p prod"               → "catalog" (use global --profile flag)
"lineage MY_TABLE -p profile"   → "lineage MY_TABLE" (use global --profile flag)
```

**Correct Examples**:
```bash
# Method 1: Global flag (BEFORE subcommand)
snowflake-cli --profile my-profile verify
snowflake-cli --profile my-profile catalog -d MY_DB
snowflake-cli --profile my-profile lineage MY_TABLE

# Method 2: Environment variable
export SNOWFLAKE_PROFILE=my-profile
snowflake-cli verify
snowflake-cli catalog -d MY_DB

# Method 3: Use default profile (no flag needed)
snowflake-cli verify
```

**Estimated Time**: 15 minutes
**Impact**: HIGH - Unblocks all command execution

---

### Fix 2: Standardize Version Numbers

**Issue**: Five different version numbers across codebase

**Current State**:
- README.md line 7: "v1.7.0 New Features"
- README.md line 209: "Version 1.5.0"
- pyproject.toml line 3: version = "1.9.0"
- cli.py line 58: `@click.version_option(version="1.6.0")`
- docs/getting-started.md line 250: "Version 1.5.0"

**Decision Needed**: What is the actual version?
- Suggest using: **1.9.0** (from pyproject.toml as source of truth)

**Files to Fix**:
```bash
# 1. README.md
# Line 7: Change "v1.7.0" → "v1.9.0"
# Line 209: Change "Version 1.5.0" → "Version 1.9.0"

# 2. src/snowcli_tools/cli.py
# Line 58: Change version="1.6.0" → version="1.9.0"

# 3. docs/getting-started.md
# Line 250: Change "Version 1.5.0" → "Version 1.9.0"

# 4. Search all docs for old versions
grep -r "1\.5\.0\|1\.6\.0\|1\.7\.0" docs/ README.md
```

**Recommended Automation**:
```python
# Add to CI/CD: Check version consistency
import toml
import re

with open('pyproject.toml') as f:
    version = toml.load(f)['project']['version']

# Check all files match
files_to_check = ['README.md', 'src/snowcli_tools/cli.py', 'docs/*.md']
for file in files_to_check:
    # Verify version matches
    pass
```

**Estimated Time**: 10 minutes
**Impact**: HIGH - Reduces confusion about which version users have

---

### Fix 3: Add Snowflake CLI Installation to Prerequisites

**Issue**: Required prerequisite not mentioned

**File**: `/Users/evandekim/Documents/snowcli_tools/README.md`

**Location**: Line 121-124 (Prerequisites section)

**Current**:
```markdown
### Prerequisites
- **Python 3.12+** with pip or uv
- **Snowflake account** with appropriate permissions
```

**Add**:
```markdown
### Prerequisites

**Required**:
1. **Python 3.12+** with pip or uv
   - Check: `python --version`
   - Install: https://www.python.org/downloads/

2. **Snowflake CLI** (Official package - separate from this tool)
   - Install: `pip install snowflake-cli`
   - Check: `snow --version`
   - Docs: https://docs.snowflake.com/en/developer-guide/snowflake-cli/
   - Purpose: Manages Snowflake authentication profiles

3. **Snowflake account** with appropriate permissions
   - Need: USAGE on warehouse/database/schema
   - Need: SELECT on INFORMATION_SCHEMA
   - Contact your Snowflake admin if unsure

**Recommended**:
4. **Private key file** for authentication (see Authentication Setup below)
```

**Also Update**: `docs/getting-started.md` line 5-9

**Estimated Time**: 10 minutes
**Impact**: HIGH - Users won't get stuck on "snow: command not found"

---

### Fix 4: Add Profile Setup Instructions

**Issue**: `snow connection add` command shown with no context

**Files**:
- `/Users/evandekim/Documents/snowcli_tools/README.md` (line 26-29)
- `/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md` (line 25-43)

**Add New Section Before Profile Setup**:
```markdown
## Authentication Setup

### Step 1: Generate Key Pair (Recommended Method)

```bash
# Generate private key in PKCS#8 format
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

Store the private key securely:
```bash
mkdir -p ~/Documents/snowflake_keys
mv rsa_key.p8 ~/Documents/snowflake_keys/
chmod 600 ~/Documents/snowflake_keys/rsa_key.p8
```

### Step 2: Upload Public Key to Snowflake

**Option A: Via Snowflake Web UI**
1. Log into Snowflake web interface
2. Click your user name (top right) → "Edit Profile"
3. Copy the public key content:
   ```bash
   cat rsa_key.pub
   ```
4. Paste into "Public Key" field (remove header/footer and line breaks)
5. Click "Save"

**Option B: Via SQL**
```sql
-- Format public key (remove header, footer, newlines)
ALTER USER your_username SET RSA_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...';
```

### Step 3: Find Your Account Identifier

Your Snowflake account URL shows your account identifier:
```
https://abc12345.us-west-2.snowflakecomputing.com/
         ^^^^^^^^ ^^^^^^^^^
         account  region
```
Account identifier: `abc12345.us-west-2`

### Step 4: Create Profile

Now run the connection setup:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "abc12345.us-west-2" \
  --user "your.email@company.com" \
  --private-key-file "$HOME/Documents/snowflake_keys/rsa_key.p8" \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE" \
  --role "YOUR_ROLE"
```

### Step 5: Verify Profile

```bash
# List profiles
snow connection list

# Test connection
snow sql -q "SELECT CURRENT_VERSION()" --connection my-profile

# Should output Snowflake version
```
```

**Estimated Time**: 20 minutes
**Impact**: CRITICAL - Unblocks authentication setup

---

## P1 - High Priority (Major Confusion)

These issues cause significant confusion but have workarounds.

### Fix 5: Add Command Quick Reference

**File**: `/Users/evandekim/Documents/snowcli_tools/README.md`

**Location**: After "Quick Start" section (after line 40)

**Add**:
```markdown
## Command Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Check version | `snowflake-cli --version` | Should show 1.9.0 |
| Verify setup | `snowflake-cli --profile PROF verify` | Tests connectivity |
| Show config | `snowflake-cli --profile PROF config` | View current settings |
| Build catalog | `snowflake-cli --profile PROF catalog -d DB -o ./output` | Scans database metadata |
| Query lineage | `snowflake-cli --profile PROF lineage TABLE_NAME` | After catalog built |
| Dependency graph | `snowflake-cli --profile PROF depgraph -d DB` | Visual dependencies |
| Start MCP server | `SNOWFLAKE_PROFILE=PROF snowflake-cli mcp` | For AI assistants |

**Note**: Replace `PROF` with your profile name, `DB` with database, `TABLE_NAME` with table.

**Profile Selection Options**:
- **Global flag**: `snowflake-cli --profile PROFILE_NAME COMMAND` (explicit)
- **Environment variable**: `export SNOWFLAKE_PROFILE=PROFILE_NAME` (session)
- **Default profile**: Set with `snow connection set-default PROFILE_NAME` (implicit)
```

**Estimated Time**: 10 minutes
**Impact**: HIGH - Reduces "how do I" questions

---

### Fix 6: Clarify MCP Dependencies

**Issue**: MCP dependencies listed as both required and optional

**File**: `/Users/evandekim/Documents/snowcli_tools/pyproject.toml`

**Current** (lines 10-30):
```toml
dependencies = [
    "mcp>=1.0.0",
    "fastmcp>=2.8.1",
    "snowflake-labs-mcp>=1.3.3",
    ...
]

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",
    "fastmcp>=2.8.1",
    "snowflake-labs-mcp>=1.3.3",
]
```

**Decision Needed**: Are MCP dependencies required or optional?

**Option A: MCP is Required** (Current behavior)
```toml
dependencies = [
    "mcp>=1.0.0",
    "fastmcp>=2.8.1",
    "snowflake-labs-mcp>=1.3.3",
    ...
]

# REMOVE the optional-dependencies section entirely
```

**Option B: MCP is Optional**
```toml
dependencies = [
    # Remove MCP packages from here
    "click>=8.0.0",
    ...
]

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",
    "fastmcp>=2.8.1",
    "snowflake-labs-mcp>=1.3.3",
]
```

**Recommendation**: Option A (MCP Required)
- Simpler for users
- MCP server is a key feature
- No confusion about extras

**Also Update Documentation**:

In `README.md` (line 178-182), change:
```markdown
# OLD - implies optional
pip install "mcp>=1.0.0" "fastmcp>=2.8.1" "snowflake-labs-mcp>=1.3.3"

# NEW - clarify included
# MCP server is included by default - no additional installation needed
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp
```

In `docs/mcp/mcp_server_user_guide.md` (line 30-36), change:
```markdown
# OLD
uv add snowcli-tools[mcp]

# NEW
# MCP functionality is included by default
pip install snowcli-tools
```

**Estimated Time**: 15 minutes
**Impact**: HIGH - Eliminates installation confusion

---

### Fix 7: Fix MCP Config Examples

**Issue**: Wrong project directory name in examples

**Files**:
- `/Users/evandekim/Documents/snowcli_tools/docs/mcp/mcp_server_user_guide.md` (line 118, 134)
- `/Users/evandekim/Documents/snowcli_tools/examples/mcp_config_example.json` (line 6)

**Search and Replace**:
```bash
# Find all occurrences
grep -r "snowflake_connector_py" docs/ examples/

# Replace with correct project name
snowflake_connector_py → snowcli-tools
```

**Also Add Explanation** in mcp_server_user_guide.md:

```markdown
### Configuration Notes

**`cwd` (Current Working Directory)**:
- For PyPI install: Can be any directory (e.g., `"/home/user/projects"`)
- For development install: Must be project root (e.g., `"/path/to/snowcli-tools"`)
- Used for: Creating `mcp_service_config.json` (auto-generated, can ignore)

**Finding Installation Path**:
```bash
# PyPI install
pip show snowcli-tools | grep Location

# Development install
pwd  # from project root
```
```

**Estimated Time**: 10 minutes
**Impact**: MEDIUM - Prevents config errors

---

### Fix 8: Add Expected Output Examples

**Issue**: Users don't know what success looks like

**File**: `/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md`

**Add After Each Command Example**:

```markdown
### Verify Setup

```bash
snowflake-cli --profile my-profile verify
```

**Expected Output**:
```
✓ Verified Snow CLI and profile 'my-profile'.
```

---

### Build Catalog

```bash
snowflake-cli --profile my-profile catalog -d MY_DATABASE -o ./catalog
```

**Expected Output**:
```
Building catalog for database MY_DATABASE
Scanning INFORMATION_SCHEMA...
Found 42 schemas
Found 1,234 tables
Found 567 views
Fetching DDL for 1,801 objects...
Progress: [████████████████████] 100%

✓ Catalog complete
✓ Written to ./catalog/

Summary:
  Databases: 1
  Schemas: 42
  Tables: 1,234
  Views: 567
  Columns: 45,678
  Duration: 2m 34s
```

---

### Start MCP Server

```bash
SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp
```

**Expected Output**:
```
🚀 Starting Snowflake MCP Server...
ℹ  This server provides AI assistants access to your Snowflake data
💡 Press Ctrl+C to stop the server

FastMCP Server v2.8.1
════════════════════════════════════
Profile: my-profile
Account: abc12345.us-west-2
Database: MY_DATABASE
Warehouse: MY_WAREHOUSE

✓ Profile validated
✓ Connection test passed
✓ Health check passed

Server Status: RUNNING
Transport: stdio
Available Tools: 10
  - execute_query
  - preview_table
  - build_catalog
  - query_lineage
  - build_dependency_graph
  - test_connection
  - get_catalog_summary
  - health_check
  - profile_table

Ready for AI assistant connections.
[Server will stay running - press Ctrl+C to stop]
```

**What If It Fails**:
```
✗ Profile 'my-profile' not found
ℹ  Create with: snow connection add --connection-name my-profile ...
ℹ  Or use: --profile <existing_profile>
```
```

**Estimated Time**: 20 minutes
**Impact**: HIGH - Reduces "is it working?" questions

---

## P2 - Medium Priority (Quality of Life)

These improve usability but aren't blockers.

### Fix 9: Add Troubleshooting Section to README

**File**: `/Users/evandekim/Documents/snowcli_tools/README.md`

**Location**: Before "License" section

**Add**:
```markdown
## Troubleshooting

### "snow: command not found"
**Problem**: Snowflake CLI not installed
**Fix**: `pip install snowflake-cli`

### "No such option: -p"
**Problem**: Using old command syntax from docs
**Fix**: Use `--profile` BEFORE subcommand:
```bash
# Wrong
snowflake-cli verify -p my-profile

# Right
snowflake-cli --profile my-profile verify
```

### "Profile 'xyz' not found"
**Problem**: Profile doesn't exist or typo
**Fix**:
```bash
# List all profiles
snow connection list

# Recreate profile
snow connection add --connection-name my-profile ...
```

### "Connection failed" or "Authentication failed"
**Problem**: Credentials incorrect or key mismatch
**Fix**:
```bash
# Test Snow CLI directly
snow sql -q "SELECT 1" --connection my-profile

# Check config file
cat ~/Library/Application\ Support/snowflake/config.toml

# Verify public key in Snowflake matches private key
```

### "Object does not exist" or "Access denied"
**Problem**: Insufficient Snowflake permissions
**Fix**: Contact Snowflake admin for:
- USAGE on warehouse/database/schema
- SELECT on INFORMATION_SCHEMA
- MONITOR on account (for lineage)

### Commands Exit Immediately
**Problem**: Profile not set or connection failed
**Fix**:
```bash
# Check current config
snowflake-cli config

# Verify profile
snowflake-cli --profile my-profile verify

# Set default profile
export SNOWFLAKE_PROFILE=my-profile
```

### MCP Server Won't Start
**Problem**: Various config issues
**Fix**:
```bash
# Test connection first
snowflake-cli --profile my-profile test

# Check for errors
DEBUG=1 snowflake-cli --profile my-profile mcp

# Verify MCP config
cat ~/.vscode/mcp.json  # or appropriate location
```

**Still stuck?** Check detailed guides:
- [Profile Setup](docs/profile_validation_quickstart.md)
- [Profile Troubleshooting](docs/profile_troubleshooting_guide.md)
- [MCP Server Guide](docs/mcp/mcp_server_user_guide.md)
```

**Estimated Time**: 15 minutes
**Impact**: MEDIUM - Helps users self-serve

---

### Fix 10: Document Config File Location

**File**: `/Users/evandekim/Documents/snowcli_tools/docs/getting-started.md`

**Location**: After profile setup section

**Add**:
```markdown
## Configuration Files

### Snowflake CLI Config

Profiles created with `snow connection add` are stored at:

**macOS**:
```
~/Library/Application Support/snowflake/config.toml
```

**Linux**:
```
~/.snowflake/config.toml
```

**Windows**:
```
%USERPROFILE%\.snowflake\config.toml
```

**View Your Config**:
```bash
# macOS
cat ~/Library/Application\ Support/snowflake/config.toml

# Linux
cat ~/.snowflake/config.toml

# All platforms
snow connection list
```

**Example Config**:
```toml
default_connection_name = "my-profile"

[connections.my-profile]
account = "abc12345.us-west-2"
user = "your.email@company.com"
database = "MY_DATABASE"
warehouse = "MY_WAREHOUSE"
role = "MY_ROLE"
authenticator = "SNOWFLAKE_JWT"
private_key_file = "/path/to/rsa_key.p8"
```

### MCP Server Config

MCP server creates `mcp_service_config.json` in current directory on first run.

**Note**: This file is auto-generated but not actually used. The server uses your Snowflake CLI profile. You can safely ignore or delete this file.

### SnowCLI Tools Config (Optional)

You can create `~/.snowcli-tools/config.yml` for tool defaults:

```yaml
snowflake:
  profile: "my-profile"

catalog:
  output_dir: "./data_catalogue"
  format: "json"
  include_ddl: true

lineage:
  cache_dir: "./lineage"
  max_depth: 3
```

**Note**: Environment variables and CLI flags override config file settings.
```

**Estimated Time**: 15 minutes
**Impact**: MEDIUM - Helps with troubleshooting and manual edits

---

## Implementation Checklist

Copy this checklist for tracking fixes:

### P0 - Critical
- [ ] Fix 1: Correct `-p` to `--profile` in all docs (15 min)
- [ ] Fix 2: Standardize version to 1.9.0 everywhere (10 min)
- [ ] Fix 3: Add Snowflake CLI to prerequisites (10 min)
- [ ] Fix 4: Add complete profile setup instructions (20 min)

**Total P0 Time**: ~55 minutes

### P1 - High Priority
- [ ] Fix 5: Add command quick reference table (10 min)
- [ ] Fix 6: Clarify MCP dependencies in pyproject.toml (15 min)
- [ ] Fix 7: Fix MCP config examples (10 min)
- [ ] Fix 8: Add expected output examples (20 min)

**Total P1 Time**: ~55 minutes

### P2 - Medium Priority
- [ ] Fix 9: Add troubleshooting section to README (15 min)
- [ ] Fix 10: Document config file locations (15 min)

**Total P2 Time**: ~30 minutes

---

## Total Estimated Time

- **P0 (Blockers)**: 55 minutes
- **P1 (High Priority)**: 55 minutes
- **P2 (Nice to Have)**: 30 minutes

**Complete Quick Fixes**: ~2.5 hours total

---

## Validation After Fixes

Run this checklist after implementing fixes:

### Documentation Validation

```bash
# 1. Check no old command syntax remains
grep -r "\-p " docs/ README.md
# Should return no results or only valid uses

# 2. Check version consistency
grep -r "1\.[0-9]\.[0-9]" docs/ README.md pyproject.toml src/
# All should show 1.9.0

# 3. Check MCP config examples
grep -r "snowflake_connector_py" docs/ examples/
# Should return no results

# 4. Verify prerequisites mention Snowflake CLI
grep -i "snowflake cli" README.md docs/getting-started.md
# Should find it in prerequisites
```

### Functional Validation

```bash
# 1. Test command syntax from docs works
snowflake-cli --profile test-profile verify

# 2. Test version consistency
snowflake-cli --version
# Should match pyproject.toml

# 3. Test MCP server starts
SNOWFLAKE_PROFILE=test-profile snowflake-cli mcp
# Should start without errors

# 4. Verify profile setup instructions work
# Follow docs/getting-started.md step by step
# Each command should work as written
```

### User Experience Validation

Have someone unfamiliar with the project:
1. Read README Quick Start
2. Follow Getting Started guide
3. Set up a profile
4. Run basic commands
5. Start MCP server
6. Report any confusion points

**Success Criteria**:
- Can complete setup in < 30 minutes
- No external research needed
- All commands work as shown
- Clear what success looks like
- Can troubleshoot basic issues

---

## Search and Replace Commands

For quick batch fixes:

```bash
# Fix 1: Command syntax
find docs README.md -type f -exec sed -i '' 's/verify -p /verify /g' {} +
find docs README.md -type f -exec sed -i '' 's/catalog -p /catalog /g' {} +
find docs README.md -type f -exec sed -i '' 's/lineage \([A-Z_]*\) -p /lineage \1 /g' {} +

# Fix 2: Version numbers (to 1.9.0)
find docs README.md -type f -exec sed -i '' 's/Version 1\.[567]\.0/Version 1.9.0/g' {} +
find docs README.md -type f -exec sed -i '' 's/v1\.[567]\.0/v1.9.0/g' {} +

# Fix 7: Project name
find docs examples -type f -exec sed -i '' 's/snowflake_connector_py/snowcli-tools/g' {} +

# Verify changes
git diff
```

**Note**: Test on a single file first, then apply to all!

---

## Before/After Examples

### Command Syntax

**Before**:
```bash
snowflake-cli verify -p my-profile
snowflake-cli catalog -p prod
```

**After**:
```bash
snowflake-cli --profile my-profile verify
snowflake-cli --profile prod catalog
```

### Prerequisites

**Before**:
```markdown
- **Python**: 3.12 or higher
- **Snowflake CLI**: Latest version recommended
```

**After**:
```markdown
1. **Python 3.12+**
   - Check: `python --version`

2. **Snowflake CLI** (separate package)
   - Install: `pip install snowflake-cli`
   - Check: `snow --version`

3. **SnowCLI Tools** (this package)
   - Install: `pip install snowcli-tools`
   - Check: `snowflake-cli --version`
```

### MCP Dependencies

**Before** (pyproject.toml):
```toml
dependencies = [
    "mcp>=1.0.0",
    ...
]

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",  # Duplicate!
    ...
]
```

**After**:
```toml
dependencies = [
    "mcp>=1.0.0",
    ...
]

# optional-dependencies.mcp section REMOVED
```

---

## Priority Matrix

| Fix # | Impact | Effort | Priority | Blocks Users? |
|-------|--------|--------|----------|---------------|
| 1 | HIGH | Low | P0 | YES |
| 2 | HIGH | Low | P0 | Partially |
| 3 | HIGH | Low | P0 | YES |
| 4 | CRITICAL | Medium | P0 | YES |
| 5 | HIGH | Low | P1 | No |
| 6 | MEDIUM | Low | P1 | Partially |
| 7 | MEDIUM | Low | P1 | No |
| 8 | HIGH | Medium | P1 | No |
| 9 | MEDIUM | Medium | P2 | No |
| 10 | MEDIUM | Low | P2 | No |

**Recommendation**: Complete all P0 fixes first (total ~1 hour), then P1 (total ~1 hour), then P2 as time permits.
