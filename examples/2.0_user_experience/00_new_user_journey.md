# New User Journey - Nanuk MCP v2.0.0

**Date**: October 7, 2025
**Version**: 2.0.0
**Perspective**: Brand new Snowflake user with no prior setup
**Goal**: Evaluate the onboarding experience from first impression to successful MCP connection

---

## Executive Summary

This document walks through the **complete new user experience** for Nanuk MCP v2.0.0, identifying friction points and recommending improvements.

### Key Findings

**Strengths** ✅
- Clear MCP-only architecture messaging
- Comprehensive Snowflake CLI setup documentation
- Multiple authentication methods supported

**Friction Points** ⚠️
1. **Snowflake parameter confusion**: Which params are required vs optional not clear
2. **Profile vs direct connection**: When to use which approach unclear
3. **First-time setup complexity**: Too many steps before "hello world"
4. **Error messages**: Need more helpful guidance for common mistakes
5. **Missing quickstart**: No "5-minute getting started" guide

---

## User Persona

**Name**: Alex Chen
**Role**: Data Analyst
**Background**:
- Has Snowflake account (company provided)
- Never used Snowflake CLI before
- Familiar with Python, wants to use Claude Code for data exploration
- Has used databases but not MCP before

**Starting Point**:
- ✅ Has Snowflake credentials (username/password)
- ✅ Has Python 3.12 installed
- ❌ No Snowflake CLI installed
- ❌ No private key setup
- ❌ Never heard of MCP before

---

## Journey Map

### Step 0: Discovery (Before Documentation)

**User Action**: Searches "Snowflake Claude Code integration"

**Finds**: Nanuk MCP GitHub/PyPI page

**First Impression**:
```
# Nanuk MCP - Snowflake MCP Server

> 🐻‍❄️ AI-first Snowflake operations via Model Context Protocol
```

✅ **Good**:
- Clear value proposition
- Friendly branding
- Immediately obvious it's for AI assistants

❌ **Confusion**:
- "What's MCP?" (not explained upfront)
- "Do I need this or just use Snowflake directly in Claude?"
- "Is this official Snowflake or third-party?"

**Recommendation**: Add 2-sentence MCP explanation in hero section.

---

### Step 1: Reading README (5 minutes)

**User reads**: Main README.md

**Questions that arise**:

1. ❓ **"What's the difference between Snowflake CLI and Nanuk MCP?"**
   - README mentions both but relationship unclear
   - Answer buried in docs

2. ❓ **"Do I need to install both?"**
   - Yes, but not obvious why
   - Snowflake CLI is just for auth profiles

3. ❓ **"What's a profile?"**
   - Term used before explained
   - Should define early

4. ✅ **"How do I install?"** - Clear
   ```bash
   pip install nanuk-mcp
   ```

5. ❓ **"Quick Start looks scary"**
   ```bash
   snow connection add --connection-name "my-profile" \
     --account "your-account.region" --user "your-username" \
     --private-key-file "/path/to/key.p8" --database "DB" --warehouse "WH"
   ```
   - Lots of parameters
   - Which are required? Which are optional?
   - What if I don't have a private key?
   - What's "your-account.region" format exactly?

**Time spent**: 5 minutes reading, 10 minutes confused

---

### Step 2: Installing Prerequisites (15 minutes)

**User follows**: Getting Started docs

#### 2.1: Install Snowflake CLI

```bash
pip install snowflake-cli-labs
```

✅ **Works** - No issues

#### 2.2: Understanding Account Identifier

❌ **Stuck**: "What's my account identifier?"

**README says**: `--account "your-account.region"`

**User tries**:
- ❌ `mycompany.snowflakecomputing.com` (wrong - includes suffix)
- ❌ `mycompany.us-east-1` (wrong - region format)
- ✅ `mycompany-prod.us-east-1` (correct but found via trial/error)

**Where they found help**:
- Had to search Snowflake docs (not Nanuk docs)
- Found: https://docs.snowflake.com/en/user-guide/admin-account-identifier

**Recommendation**: Add section explaining account identifier formats with examples.

---

### Step 3: First Connection Attempt (20 minutes)

#### 3.1: Simplest Auth (Username/Password)

**User thinks**: "I'll start simple with password, add key later"

**Tries**:
```bash
snow connection add \
  --connection-name "test-profile" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --password
```

✅ **Prompts for password** - Good UX

❌ **Error**:
```
Error: Missing required parameter: --warehouse
```

**User's reaction**: "Wait, is warehouse required or optional?"

**Looking at docs**:
- README Quick Start shows warehouse
- But doesn't say it's required
- Confusion: Can I connect without specifying warehouse?

**Answer** (not in docs):
- Warehouse is OPTIONAL for connection
- But REQUIRED for running queries
- This distinction is never explained

---

#### 3.2: Understanding Required vs Optional Parameters

**User question**: "What do I actually NEED?"

**Current documentation** ❌:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --private-key-file "/path/to/key.p8" \
  --database "DB" \
  --warehouse "WH"
```

Shows all parameters but doesn't indicate:
- Which are **REQUIRED** for connection
- Which are **REQUIRED** for queries
- Which are **OPTIONAL** for convenience
- What happens if you omit optional ones

**What user needs** ✅:
```bash
# REQUIRED (must provide):
--connection-name "profile-name"    # Name for this profile
--account "account.region"          # Your Snowflake account
--user "username"                   # Your username

# AUTHENTICATION (pick ONE):
--password                          # Interactive password prompt
--private-key-file "path/to/key"    # OR key-pair auth
--authenticator "externalbrowser"   # OR SSO

# OPTIONAL (can be set later or per-query):
--database "DB"                     # Default database
--warehouse "WH"                    # Default warehouse (required for queries)
--role "ROLE"                       # Default role
--schema "SCHEMA"                   # Default schema
```

**Recommendation**: Create parameter reference table showing required/optional/purpose.

---

#### 3.3: Successful Profile Creation

After understanding requirements:

```bash
snow connection add \
  --connection-name "my-snowflake" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --password \
  --warehouse "COMPUTE_WH" \
  --database "ANALYTICS_DB"
```

✅ **Success**: Profile created

**User verifies**:
```bash
snow connection list
```

Output shows profile exists ✅

---

### Step 4: Starting MCP Server (5 minutes)

#### 4.1: First Start Attempt

```bash
nanuk-mcp --profile my-snowflake
```

❌ **Error**:
```
Error: Profile 'my-snowflake' not found
```

**User confusion**: "I just created it! `snow connection list` shows it!"

**Problem**: Nanuk looks in different config location? Or different naming?

**After investigation** (10 more minutes):
- Profile name is correct
- Issue was environment/config path
- Not clearly documented

**Recommendation**: Add troubleshooting section for "profile not found" errors.

---

#### 4.2: Successful MCP Server Start

After fixing config:

```bash
SNOWFLAKE_PROFILE=my-snowflake nanuk-mcp
```

✅ **Output**:
```
INFO: Starting Snowflake MCP server
INFO: Profile: my-snowflake
INFO: Listening on stdio
```

**User reaction**: "Great! But now what?"

❌ **Problem**: Server is running but:
- User doesn't know how to test it
- No "hello world" command shown
- Needs to configure Claude Code next (not explained here)

---

### Step 5: Claude Code Integration (15 minutes)

#### 5.1: Finding Configuration Instructions

**User searches docs for**: "Claude Code setup"

**Finds** (eventually): README MCP Integration section

```json
{
  "mcpServers": {
    "nanuk": {
      "command": "nanuk-mcp",
      "args": ["--profile", "my-profile"]
    }
  }
}
```

✅ **Clear example**

❌ **Missing**:
- Where exactly is this config file?
- How do I know if it worked?
- Do I need to restart Claude Code?

---

#### 5.2: Configuration Steps

**User follows** (from general MCP knowledge):

1. Open `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Add configuration
3. Restart Claude Code
4. Check for MCP server in tools menu

✅ **Works**

**Time to first success**: 10 minutes (with MCP experience), 30+ minutes (without)

---

### Step 6: First Query (10 minutes)

#### 6.1: Testing in Claude Code

**User asks Claude**: "Show me my Snowflake databases"

**Claude uses**: `execute_query` tool

✅ **Success**: Returns database list

**User reaction**: "This is amazing!"

---

## Pain Points Summary

### Critical Issues 🔴

1. **Parameter Documentation**
   - Required vs optional params not clearly labeled
   - Purpose of each parameter not explained
   - Examples don't show minimal vs full setups

2. **Account Identifier Confusion**
   - Format not explained with examples
   - Common mistakes not documented
   - No validation/error messages to guide user

3. **Missing Quickstart**
   - No "5-minute getting started"
   - Current quickstart has too many steps
   - No "hello world" equivalent

### Medium Issues 🟡

4. **Warehouse Requirement Confusion**
   - Connection works without warehouse
   - Queries fail without warehouse
   - This distinction never explained

5. **Profile Troubleshooting**
   - "Profile not found" errors hard to debug
   - No guidance on config file locations
   - Environment variable usage not clear

6. **MCP Concepts**
   - MCP never explained for newcomers
   - Difference from direct Snowflake connection unclear
   - Benefits not obvious until you use it

### Minor Issues 🟢

7. **Post-Install Next Steps**
   - After MCP server starts, unclear what to do
   - No testing instructions
   - No verification steps

8. **Claude Code Setup**
   - Config file location OS-specific (docs only show macOS)
   - Restart requirement not mentioned
   - Success indicators not documented

---

## Time to First Success

**Ideal Target**: 10 minutes
**Current Reality**: 60-90 minutes

**Breakdown**:
- Reading docs: 15 min
- Installing prerequisites: 15 min
- Creating profile (with trial/error): 30 min
- Starting MCP server: 5 min
- Claude Code config: 10 min
- First successful query: 5 min

**If docs improved**: Could be ~20 minutes

---

## Recommended Improvements

See individual documents:
- `01_parameter_clarity.md` - Required vs optional params
- `02_5_minute_quickstart.md` - Fast path to success
- `03_common_errors.md` - Troubleshooting guide
- `04_account_identifier_guide.md` - Account ID formats
- `05_mcp_concepts.md` - MCP explainer for newcomers

---

## Positive Aspects

**What worked well** ✅

1. **Clear Installation**
   - `pip install nanuk-mcp` just works
   - No dependency conflicts
   - Fast install

2. **Good Examples**
   - Code examples are accurate
   - JSON configs are copy-pasteable
   - Multiple auth methods documented

3. **MCP-Only Messaging**
   - Clear that CLI is removed
   - Migration guide for upgraders
   - Consistent architecture

4. **Professional Documentation**
   - Well-organized
   - Good structure
   - Nice branding

---

## Next Steps

1. Create improved parameter documentation (See `01_parameter_clarity.md`)
2. Write 5-minute quickstart guide (See `02_5_minute_quickstart.md`)
3. Add troubleshooting section (See `03_common_errors.md`)
4. Improve account identifier docs (See `04_account_identifier_guide.md`)
5. Add MCP concepts explainer (See `05_mcp_concepts.md`)

---

**Conclusion**: Nanuk MCP v2.0.0 is functionally solid but needs **documentation improvements** to reduce time-to-first-success from 60+ minutes to ~20 minutes.
