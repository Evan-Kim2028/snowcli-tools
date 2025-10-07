# New User Walkthrough: First-Time Setup Experience

**Date**: October 7, 2025
**Perspective**: Completely new user with no prior knowledge of the project
**Goal**: Follow documentation to install, set up, and use SnowCLI Tools

---

## Summary

This document simulates a completely new user trying to set up SnowCLI Tools by following the official documentation. It captures every confusion point, missing step, and documentation issue encountered during the process.

**Overall Experience**: 🔴 **Challenging** - Multiple documentation inconsistencies and missing critical setup steps.

---

## Step 1: Initial Discovery - Reading README.md

### What I See First

✅ **Good First Impressions**:
- Clear feature list with icons
- Quick Start section visible early
- Version badges present (PyPI, Python 3.12+)

❌ **Immediate Confusion Points**:

1. **Version Mismatch Crisis** (Line 7-15):
   - README says "v1.7.0 New Features"
   - pyproject.toml says version = "1.9.0"
   - Git branch is named "v1.10.0_discovery_assistant"
   - Bottom of README says "Version 1.5.0"
   - **Question**: Which version am I using?

2. **Installation Method Confusion** (Line 22-39):
   ```bash
   # 1. Install SnowCLI Tools
   pip install snowcli-tools

   # 2. Set up your Snowflake profile
   snow connection add --connection-name "my-profile" ...
   ```
   - **Problem**: Where does the `snow` command come from?
   - **Problem**: Is this included in snowcli-tools or separate?
   - No mention of installing Snowflake CLI first

3. **Command Name Inconsistency** (Line 32-36):
   - Line 32: Uses `snowflake-cli verify`
   - Line 34: Uses `snowflake-cli catalog`
   - Line 39: Uses `snowflake-cli mcp`
   - BUT Line 27: Uses `snow connection add` (different command!)
   - **Question**: Are these different CLIs?

### Action Taken

I try to understand the prerequisites by reading further...

---

## Step 2: Following Quick Start Installation

### Attempt 1: Direct Installation

```bash
pip install snowcli-tools
```

**Expected**: Tool installs and I can run commands
**Actual**: ❓ Unknown (not attempted in simulation)

**Question**: Do I need to install Snowflake CLI separately first?

### Documentation Check: Prerequisites (Line 121-124)

```
- **Python**: 3.12 or higher
- **Snowflake CLI**: Latest version recommended
- **Dependencies**: Automatically installed with package
- **Permissions**: `USAGE` on warehouse/database/schema, `SELECT` on `INFORMATION_SCHEMA`
```

🔴 **CRITICAL ISSUE**:
- Says "Snowflake CLI: Latest version recommended"
- No instructions on HOW to install Snowflake CLI
- No link to Snowflake CLI documentation
- **Assumption**: User must already know about Snowflake CLI

### The Profile Setup Mystery (Line 140-158)

```bash
# Key-pair authentication (recommended)
snow connection add --connection-name "my-profile" \
  --account "your-account.region" \
  --user "username" \
  --private-key-file "/path/to/key.p8" \
  --database "DATABASE" \
  --warehouse "WAREHOUSE"
```

❌ **Multiple Problems**:

1. **Where do I get a private key?**
   - No explanation of key generation
   - No link to Snowflake documentation on key-pair auth
   - Example shows ".p8" file - what is this?

2. **Account format unclear**:
   - Shows "your-account.region"
   - Is this literal? Or example?
   - Where do I find my account identifier in Snowflake?

3. **Required vs Optional unclear**:
   - Database and warehouse shown
   - Are these required?
   - What if I don't specify them?

### Action Taken

Searching for more detailed instructions...

---

## Step 3: Reading Getting Started Guide (docs/getting-started.md)

### First Issue: Installation Command Mismatch (Line 11-23)

Getting Started Guide says:
```bash
# Clone and install the project
git clone <repository-url>
cd snowcli-tools

# Install with uv (recommended)
uv sync

# Or install from PyPI (when published)
pip install snowcli-tools
```

🔴 **Contradictions**:
- README says: `pip install snowcli-tools` (implying it's published)
- Getting Started says: "Or install from PyPI (when published)" (implying it's NOT published)
- Also mentions "uv" package manager - never mentioned in README
- **Question**: Can I actually install from PyPI or not?

### Second Issue: Running Commands (Line 68-76)

```bash
# List all configured profiles
uv run snow connection list

# Test your profile works
uv run snowflake-cli verify -p my-profile
```

❌ **Command Confusion**:
- Uses `uv run snow connection list` (with `uv run`)
- Uses `uv run snowflake-cli verify -p my-profile` (with `uv run`)
- README didn't mention `uv run` prefix at all
- **Question**: Do I need `uv run` or not?

### Third Issue: Profile Flag Testing

Tried commands from documentation:
```bash
uv run snowflake-cli verify -p mystenlabs-keypair
```

**Result**: ❌ ERROR
```
Error: No such option: -p
```

Then tried:
```bash
uv run snowflake-cli --profile mystenlabs-keypair verify
```

**Result**: ✅ SUCCESS

🔴 **CRITICAL DOCUMENTATION BUG**:
- Documentation consistently shows: `snowflake-cli verify -p my-profile`
- Actual syntax is: `snowflake-cli --profile my-profile verify`
- The `-p` flag is a GLOBAL flag, not a command flag
- **This appears in multiple places throughout documentation**

---

## Step 4: Understanding Authentication

### Finding Config File (Not in Docs!)

Documentation never mentions where Snowflake CLI stores profiles!

Through investigation, found:
```
~/.snowflake/config.toml (macOS/Linux)
or
~/Library/Application Support/snowflake/config.toml (macOS)
```

Example of actual config:
```toml
[connections.mystenlabs-keypair]
account = "HKB47976.us-west-2"
user = "evan.kim@mystenlabs.com"
database = "PIPELINE_V2_GROOT_DB"
schema = "PIPELINE_V2_GROOT_SCHEMA"
warehouse = "PRESET_WH"
role = "SECURITYADMIN"
authenticator = "SNOWFLAKE_JWT"
private_key_file = "/Users/evandekim/Documents/snowflake_keys_evan/rsa_key_evan.p8"
```

❌ **Documentation Gaps**:
1. No mention of config file location
2. No mention that you can manually edit this file
3. No mention of `authenticator = "SNOWFLAKE_JWT"` for key-pair auth
4. No troubleshooting for "where did my profile go?"

### Understanding the Snow CLI Requirement

After testing, discovered:
- `snow` command (from Snowflake CLI package) is separate
- `snowflake-cli` command (from this package) wraps/uses it
- You need BOTH installed
- This is never clearly stated

**Correct Installation Order** (Not in docs):
```bash
# Step 1: Install official Snowflake CLI
pip install snowflake-cli

# Step 2: Set up profile using Snow CLI
snow connection add --connection-name "my-profile" ...

# Step 3: Install SnowCLI Tools
pip install snowcli-tools

# Step 4: Use enhanced tools
snowflake-cli catalog -d MY_DATABASE
```

---

## Step 5: Attempting to Use MCP Server

### Following MCP Documentation (docs/mcp/mcp_server_user_guide.md)

#### Installation Confusion (Line 30-36)

```bash
# Install with MCP support
uv add snowcli-tools[mcp]
```

❌ **Problems**:
1. Uses `uv add` - what about pip users?
2. pyproject.toml shows MCP dependencies are ALREADY in main dependencies (lines 18-21)
3. Also has `[project.optional-dependencies]` section with same MCP deps
4. **Question**: Do I need the `[mcp]` extra or is it already included?

Testing with actual pyproject.toml:
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

🔴 **CONTRADICTION**: MCP deps are in BOTH places - main dependencies AND optional!

### Starting MCP Server

Documentation shows:
```bash
uv run snowflake-cli mcp
```

✅ **This works!** But then what?

#### Missing Information:

1. **No output explanation**:
   - What should I see when server starts?
   - Is there a success message?
   - Does it run in foreground or background?

2. **Environment variable confusion**:
   - Docs say: `export SNOWFLAKE_PROFILE=my-profile`
   - Also say: `SNOWFLAKE_PROFILE=my-profile snowflake-cli mcp`
   - Which approach to use?
   - Does the global `--profile` flag work?

3. **How to test it's working?**:
   - No instructions to verify MCP server is running
   - No test commands
   - No debug output

### Configuring AI Assistant (Line 108-122)

Example for VS Code:
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

❌ **Multiple Issues**:

1. **Wrong directory name**: Shows "snowflake_connector_py" but project is "snowcli-tools"
2. **cwd confusion**: What should this path be?
   - Project root?
   - Installed package location?
   - Not specified

3. **Config file location not mentioned**:
   - Says "usually `~/.vscode/mcp.json`"
   - Very vague
   - No alternative locations mentioned

4. **No verification steps**:
   - How do I know it's configured correctly?
   - No test query examples
   - No troubleshooting section for MCP setup

---

## Step 6: Trying Basic Commands

### Test 1: Verify Command

**Documentation says**:
```bash
uv run snowflake-cli verify -p my-profile
```

**Actual working command**:
```bash
uv run snowflake-cli --profile my-profile verify
```

**Help output shows**:
```
Usage: snowflake-cli verify [OPTIONS]

Options:
  --help  Show this message and exit.
```

No `-p` option at all! It's a global option before the subcommand.

### Test 2: Catalog Command

**Documentation shows multiple ways**:
```bash
# Example 1 (README line 34)
snowflake-cli catalog -p prod

# Example 2 (README line 91)
snowflake-cli catalog -p prod

# Example 3 (Getting Started line 143)
uv run snowflake-cli catalog -p my-profile
```

**Actual command that works**:
```bash
SNOWFLAKE_PROFILE=mystenlabs-keypair uv run snowflake-cli catalog -d PIPELINE_V2_GROOT_DB -o ./catalog_output
```

**Note**: The `-d` (database) flag is helpful but never explained in Quick Start!

### Config Command Discovery

Found useful command not mentioned in Quick Start:
```bash
snowflake-cli config
```

**Output**:
```
            Snowflake Configuration
┌────────────────────────┬────────────────────┐
│ Profile                │ mystenlabs-keypair │
│ Warehouse              │                    │
│ Database               │                    │
│ Schema                 │                    │
│ Role                   │ None               │
└────────────────────────┴────────────────────┘
```

💡 **This should be in Getting Started!** Helps users verify their setup.

---

## Step 7: Reading MCP Server Technical Guide

### Architecture Understanding (docs/mcp/mcp_architecture.md)

Actually helpful! But buried in docs.

Key insight not in Getting Started:
```
┌─────────────────────────────────────┐
│        Your Applications            │
├─────────────────────────────────────┤
│     SnowCLI Tools MCP Server        │  ← This package
├─────────────────────────────────────┤
│      Snowflake Labs MCP             │  ← Separate dependency
├─────────────────────────────────────┤
│       Snowflake CLI                 │  ← Official CLI
├─────────────────────────────────────┤
│         Snowflake                   │  ← Database
└─────────────────────────────────────┘
```

❌ **Should be in README prominently!** Explains the three-layer dependency.

---

## Major Pain Points Summary

### 1. Version Confusion (CRITICAL)

**Found in project**:
- README.md line 7: "v1.7.0 New Features"
- README.md line 209: "Version 1.5.0"
- pyproject.toml line 3: version = "1.9.0"
- Git branch: "v1.10.0_discovery_assistant"
- cli.py line 58: `@click.version_option(version="1.6.0")`
- Getting Started line 250: "Version 1.5.0 | Updated: 2025-09-28"

🔴 **FIVE DIFFERENT VERSIONS** in the codebase! Which one is real?

### 2. Command Syntax Inconsistency (CRITICAL)

**Documentation consistently shows**:
```bash
snowflake-cli verify -p my-profile
snowflake-cli catalog -p my-profile
snowflake-cli lineage MY_TABLE -p my-profile
```

**Actual syntax**:
```bash
snowflake-cli --profile my-profile verify
snowflake-cli --profile my-profile catalog
snowflake-cli --profile my-profile lineage MY_TABLE
```

The `-p` flag doesn't exist at command level. It's `--profile` at global level.

### 3. Installation Prerequisites Unclear

**What's actually needed** (through investigation):
1. Python 3.12+
2. pip or uv
3. Snowflake CLI (separate package): `pip install snowflake-cli`
4. SnowCLI Tools: `pip install snowcli-tools`
5. Snowflake account with credentials
6. Private key file for auth (or other auth method)

**What the Quick Start says**: Just `pip install snowcli-tools`

### 4. Profile Setup Missing Steps

**What documentation shows**:
```bash
snow connection add --connection-name "my-profile" ...
```

**What's missing**:
1. How to generate private key
2. How to upload public key to Snowflake
3. Where config file is stored
4. How to verify profile was created
5. How to troubleshoot auth failures
6. What each parameter means

### 5. MCP Server Setup Unclear

**Questions not answered**:
1. Is MCP included or optional?
2. What's the minimal config needed?
3. How to verify it's running?
4. What should AI assistant see?
5. How to test tools are available?
6. Where are logs?

### 6. Command Prefix Confusion

**Examples use inconsistently**:
- `snowflake-cli catalog` (bare command)
- `uv run snowflake-cli catalog` (with uv)
- `SNOWFLAKE_PROFILE=prod snowflake-cli catalog` (with env var)

**Not explained**:
- When to use `uv run` vs not
- Development install vs PyPI install differences
- Environment variable vs flag vs config file

---

## What Would Have Helped

### 1. Clear Installation Flow

```markdown
## Installation - Complete Guide

### Step 1: Install Prerequisites

1. **Python 3.12+**: Check with `python --version`
2. **Snowflake CLI**:
   ```bash
   pip install snowflake-cli
   ```
   Verify: `snow --version`

### Step 2: Set Up Snowflake Authentication

1. **Generate Key Pair** (if using key-pair auth):
   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
   openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
   ```

2. **Upload Public Key to Snowflake**:
   - Instructions with screenshots
   - Link to Snowflake docs

3. **Create Profile**:
   ```bash
   snow connection add \
     --connection-name "my-profile" \
     --account "abc12345.us-west-2" \
     --user "your.email@company.com" \
     --private-key-file "~/path/to/rsa_key.p8" \
     --database "MY_DATABASE" \
     --warehouse "MY_WAREHOUSE" \
     --role "MY_ROLE"
   ```

4. **Verify Profile**:
   ```bash
   snow connection list
   snow sql -q "SELECT CURRENT_VERSION()" --connection my-profile
   ```

### Step 3: Install SnowCLI Tools

```bash
pip install snowcli-tools
```

### Step 4: Verify Installation

```bash
snowflake-cli --version
snowflake-cli --profile my-profile verify
snowflake-cli --profile my-profile config
```

### Step 5: Run First Command

```bash
snowflake-cli --profile my-profile catalog -d MY_DATABASE -o ./catalog
```
```

### 2. Command Reference Card

A clear table showing ALL command syntax:

```markdown
## Command Quick Reference

| Task | Command | Notes |
|------|---------|-------|
| Check version | `snowflake-cli --version` | Should match pyproject.toml |
| Verify setup | `snowflake-cli --profile PROF verify` | Tests connectivity |
| Show config | `snowflake-cli --profile PROF config` | View current settings |
| Build catalog | `snowflake-cli --profile PROF catalog -d DB` | Requires database |
| Query lineage | `snowflake-cli --profile PROF lineage TABLE` | After catalog |
| Start MCP | `SNOWFLAKE_PROFILE=PROF snowflake-cli mcp` | For AI assistants |

**Profile Options**:
- Flag: `--profile PROFILE_NAME` (global, before subcommand)
- Env var: `export SNOWFLAKE_PROFILE=PROFILE_NAME`
- Config file: Set in `~/.snowcli-tools/config.yml`
```

### 3. Troubleshooting Section

```markdown
## Common Issues

### "No such option: -p"
- **Wrong**: `snowflake-cli verify -p my-profile`
- **Right**: `snowflake-cli --profile my-profile verify`
- Note: `-p` is shown in docs but not supported. Use `--profile` before subcommand.

### "snow: command not found"
- Install Snowflake CLI: `pip install snowflake-cli`
- This is a separate package required by SnowCLI Tools

### "Profile not found"
- Check profiles: `snow connection list`
- Config location: `~/.snowflake/config.toml` (Linux/Mac)
- Create profile: See "Set Up Snowflake Authentication" above
```

### 4. Version Consistency

Fix all version references to match:
- [ ] README.md header
- [ ] README.md footer
- [ ] pyproject.toml
- [ ] cli.py version option
- [ ] Getting Started footer
- [ ] All docs

### 5. Examples with Real Output

Show what success looks like:

```markdown
## Expected Output

### Successful Verification
```bash
$ snowflake-cli --profile my-profile verify
✓ Verified Snow CLI and profile 'my-profile'.
```

### Successful Catalog
```bash
$ snowflake-cli --profile prod catalog -d ANALYTICS_DB -o ./catalog
⠋ Building catalog for ANALYTICS_DB...
✓ Found 45 tables, 12 views, 3 schemas
✓ Catalog saved to ./catalog/
```
```

---

## Testing Checklist for Documentation

- [ ] Follow README Quick Start exactly as written
- [ ] Can a new user install without external research?
- [ ] Are all commands copy-paste ready?
- [ ] Do all command examples work as shown?
- [ ] Are error messages explained?
- [ ] Is authentication setup complete?
- [ ] Can user verify each step succeeded?
- [ ] Are all prerequisites listed upfront?
- [ ] Is version numbering consistent?
- [ ] Are command prefixes (`uv run`) used consistently?

**Current Status**: ❌ Fails most checks

---

## Recommendations Priority

### P0 - Critical (Blocks Users)

1. **Fix command syntax in ALL docs**: Change `-p` to `--profile` everywhere
2. **Fix version numbers**: Make them consistent (1.9.0 from pyproject.toml)
3. **Add Snowflake CLI installation**: Explicit prerequisite step
4. **Add profile setup tutorial**: With key generation steps

### P1 - High (Major Confusion)

5. **Clarify MCP dependencies**: Are they optional or not?
6. **Add command reference table**: All commands with correct syntax
7. **Explain `uv run` vs bare commands**: When to use what
8. **Add "Expected Output" sections**: Show what success looks like

### P2 - Medium (Quality of Life)

9. **Add troubleshooting section**: Common errors with solutions
10. **Config file location documentation**: Where profiles are stored
11. **Add verification steps**: After each major step
12. **Better examples with real data**: Not just placeholders

### P3 - Low (Nice to Have)

13. **Screenshots for key steps**: Especially Snowflake web UI
14. **Video walkthrough**: For complete setup
15. **FAQ section**: Anticipated questions
16. **Comparison with alternatives**: When to use this tool

---

## Conclusion

**Can a new user successfully set up SnowCLI Tools following current docs?**

**Answer**: ❌ **No** - Multiple blocking issues:
- Command syntax errors throughout docs
- Missing prerequisite installation steps
- Version numbering confusion
- Incomplete authentication setup
- Unclear MCP configuration

**Estimated Time for New User**:
- **Expected** (from docs): 10-15 minutes
- **Actual** (with troubleshooting): 2-4 hours
- **With perfect docs**: 30-45 minutes

**Sentiment**: Frustrated. The tool seems powerful but documentation needs significant work to be usable by newcomers.
