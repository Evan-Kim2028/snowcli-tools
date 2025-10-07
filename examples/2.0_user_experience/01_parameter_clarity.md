# Snowflake Parameter Clarity Guide

**Issue**: New users confused about which Snowflake parameters are required vs optional
**Impact**: High - Causes 30+ minutes of trial-and-error
**Severity**: Critical for onboarding

---

## Current Problem

### What Users See Now ❌

```bash
snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --private-key-file "/path/to/key.p8" \
  --database "DB" \
  --warehouse "WH"
```

**Problems**:
1. All parameters shown equally - no indication of required vs optional
2. Doesn't explain what each parameter does
3. Doesn't explain when you need each parameter
4. Shows private-key but doesn't mention password alternative
5. No indication of parameter interdependencies

---

## Improved Documentation

### Parameter Reference Table

| Parameter | Required | When Needed | Purpose | Example |
|-----------|----------|-------------|---------|---------|
| `--connection-name` | ✅ Always | Profile creation | Name for this connection profile | `"my-snowflake"` |
| `--account` | ✅ Always | Authentication | Your Snowflake account identifier | `"mycompany-prod.us-east-1"` |
| `--user` | ✅ Always | Authentication | Your Snowflake username | `"alex.chen"` |
| **Authentication** (pick ONE) | | | | |
| `--password` | 🟡 Optional | Password auth | Interactive password prompt | (prompts) |
| `--private-key-file` | 🟡 Optional | Key-pair auth | Path to private key file | `"~/.snowflake/key.pem"` |
| `--authenticator` | 🟡 Optional | SSO/OAuth | Authentication method | `"externalbrowser"` |
| **Context** (optional defaults) | | | | |
| `--warehouse` | 🟢 Optional | Running queries | Default warehouse for queries | `"COMPUTE_WH"` |
| `--database` | 🟢 Optional | Database queries | Default database context | `"ANALYTICS_DB"` |
| `--schema` | 🟢 Optional | Schema queries | Default schema context | `"PUBLIC"` |
| `--role` | 🟢 Optional | Access control | Default role to assume | `"ANALYST"` |
| **Advanced** (rarely needed) | | | | |
| `--host` | 🟢 Optional | Custom endpoint | Override default host | `"custom.snowflakecomputing.com"` |
| `--passcode` | 🟢 Optional | MFA | Multi-factor auth code | `"123456"` |
| `--private-key-file-pwd` | 🟢 Optional | Encrypted keys | Password for encrypted private key | `"keypassword"` |

### Legend

- ✅ **Required**: Must provide this parameter
- 🟡 **Authentication** (pick ONE): Must provide at least one authentication method
- 🟢 **Optional**: Can omit; can be set later or per-query

---

## Minimal Connection Examples

### Example 1: Password Authentication (Simplest)

**Absolute minimum to connect**:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --password
```

**What happens**:
- ✅ Profile created
- ✅ Can connect to Snowflake
- ✅ Can list databases/tables
- ❌ Cannot run queries yet (no warehouse)

**Next step**: Either add warehouse to profile or specify per-query.

---

### Example 2: Production-Ready Profile

**Recommended for real use**:
```bash
snow connection add \
  --connection-name "prod-profile" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "PROD_WH" \
  --database "ANALYTICS" \
  --role "DATA_ANALYST"
```

**What you get**:
- ✅ Secure key-pair authentication
- ✅ Default warehouse (can run queries immediately)
- ✅ Default database (don't need to specify each time)
- ✅ Default role (consistent permissions)

---

### Example 3: SSO/Browser Authentication

**For companies using SSO**:
```bash
snow connection add \
  --connection-name "sso-profile" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --authenticator "externalbrowser" \
  --warehouse "COMPUTE_WH"
```

**What happens**:
- Browser opens for SSO login
- Credentials cached locally
- No password or key needed

---

## Understanding Parameter Contexts

### Connection-Level vs Query-Level

#### Connection-Level Parameters (One-time setup)
These are set when creating the profile:

```bash
--account "mycompany-prod.us-east-1"  # Can't change per-query
--user "alex.chen"                     # Can't change per-query
--password                             # Can't change per-query
```

#### Context Parameters (Can override per-query)
These can be set as defaults but overridden:

```bash
# Set defaults in profile:
--warehouse "DEFAULT_WH"
--database "DEFAULT_DB"
--role "DEFAULT_ROLE"

# Override in nanuk-mcp:
nanuk-mcp --profile my-profile --warehouse DIFFERENT_WH
```

Or override in MCP tool calls:
```python
execute_query(
    statement="SELECT * FROM table",
    warehouse="ADHOC_WH",  # Override default
    database="DIFFERENT_DB"  # Override default
)
```

---

## Common Scenarios

### Scenario 1: "I just want to try it"

**Minimum viable setup**:
```bash
# 1. Create minimal profile
snow connection add \
  --connection-name "test" \
  --account "your-account.region" \
  --user "your-username" \
  --password

# 2. Start MCP server
SNOWFLAKE_PROFILE=test nanuk-mcp

# 3. In MCP queries, specify warehouse:
execute_query(
    statement="SELECT CURRENT_DATABASE()",
    warehouse="COMPUTE_WH"  # Specify since not in profile
)
```

**Pros**:
- ✅ Fastest setup (2 minutes)
- ✅ No key generation needed
- ✅ Works immediately

**Cons**:
- ❌ Must specify warehouse in every query
- ❌ Password auth (less secure)
- ❌ No default database context

---

### Scenario 2: "I'm a developer"

**Recommended setup**:
```bash
# 1. Generate key pair (one-time, see key setup guide)
openssl genrsa -out ~/.snowflake/key.pem 2048

# 2. Upload public key to Snowflake (one-time)
# See key setup guide

# 3. Create full profile
snow connection add \
  --connection-name "dev" \
  --account "mycompany-dev.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "DEV_WH" \
  --database "DEV_DB" \
  --schema "SCRATCH" \
  --role "DEVELOPER"

# 4. Start MCP server (no additional params needed)
nanuk-mcp --profile dev
```

**Pros**:
- ✅ Secure authentication
- ✅ All defaults set
- ✅ Queries "just work"
- ✅ Proper role/database isolation

---

### Scenario 3: "I work with multiple environments"

**Multi-profile setup**:
```bash
# Development
snow connection add \
  --connection-name "dev" \
  --account "mycompany-dev.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "DEV_WH" \
  --database "DEV_DB"

# Staging
snow connection add \
  --connection-name "staging" \
  --account "mycompany-staging.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "STAGING_WH" \
  --database "STAGING_DB"

# Production (read-only role)
snow connection add \
  --connection-name "prod-ro" \
  --account "mycompany-prod.us-east-1" \
  --user "alex.chen" \
  --private-key-file "~/.snowflake/key.pem" \
  --warehouse "PROD_RO_WH" \
  --database "PROD_DB" \
  --role "READONLY"

# Switch between environments:
nanuk-mcp --profile dev      # Development
nanuk-mcp --profile staging  # Staging
nanuk-mcp --profile prod-ro  # Production (read-only)
```

---

## Warehouse Deep Dive

### Why Warehouse is Special

**Key insight**: Warehouse behaves differently than other parameters.

#### For Connection: Optional
```bash
# This works (connection succeeds):
snow connection add \
  --connection-name "no-wh" \
  --account "mycompany.us-east-1" \
  --user "alex" \
  --password
# No warehouse specified ✅
```

#### For Queries: Required
```sql
-- This fails:
SELECT * FROM my_table;
-- Error: No warehouse specified

-- This works:
USE WAREHOUSE COMPUTE_WH;
SELECT * FROM my_table;
```

### Three Ways to Specify Warehouse

**Option 1: In Profile (Recommended)**
```bash
snow connection add ... --warehouse "DEFAULT_WH"
```
✅ Set once, use everywhere
❌ Can't easily switch warehouses

**Option 2: In MCP Server Startup**
```bash
nanuk-mcp --profile my-profile --warehouse "ADHOC_WH"
```
✅ Override profile default
❌ All queries use same warehouse

**Option 3: Per Query (Most Flexible)**
```python
execute_query(
    statement="SELECT ...",
    warehouse="LARGE_WH"  # For this query only
)
```
✅ Choose warehouse per query
❌ Must specify each time

### Warehouse Selection Guide

| Use Case | Recommended Warehouse | Why |
|----------|----------------------|-----|
| Development/Testing | `X-Small` or `Small` | Cheap, fast startup |
| Ad-hoc queries | `Small` or `Medium` | Balance cost/performance |
| Large scans | `Large` or `X-Large` | Better performance |
| Production ETL | `Large+` with auto-suspend | Optimized for workload |

**Pro tip**: Set a small warehouse in profile, override for heavy queries:
```bash
# Profile has small warehouse
snow connection add ... --warehouse "SMALL_WH"

# Override for heavy query:
execute_query(
    statement="SELECT * FROM huge_table",
    warehouse="XLARGE_WH"  # Just for this query
)
```

---

## Account Identifier Format

### The Most Common Confusion

**What users try** ❌:
- `mycompany.snowflakecomputing.com` (includes domain)
- `mycompany` (missing region)
- `mycompany.us-east-1.snowflakecomputing.com` (too complete)

**Correct format** ✅:
```
<account_locator>.<region>
```

### Finding Your Account Identifier

**Method 1: From Snowflake URL**

Your Snowflake URL:
```
https://abc12345.us-east-1.snowflakecomputing.com
```

Your account identifier:
```
abc12345.us-east-1
```

**Method 2: From Snowflake UI**

1. Log into Snowflake web UI
2. Bottom left corner shows account
3. Copy everything before `.snowflakecomputing.com`

**Method 3: Ask Your Admin**

They should provide format like:
```
<organization>-<account_name>.<region>
```

Example: `mycompany-prod.us-east-1`

### Common Formats

| Format | Example | When Used |
|--------|---------|-----------|
| Legacy locator | `abc12345.us-east-1` | Older accounts |
| Org-based | `myorg-myaccount.us-east-1` | Newer accounts |
| AWS | `myaccount.us-east-1.aws` | Explicit cloud |
| Azure | `myaccount.east-us-2.azure` | Azure accounts |
| GCP | `myaccount.us-central1.gcp` | GCP accounts |

**Rule of thumb**: Copy from your Snowflake URL, remove `.snowflakecomputing.com`

---

## Validation & Testing

### Test Your Profile

After creating profile:

```bash
# 1. List profiles
snow connection list

# 2. Test connection
snow connection test --connection-name "my-profile"

# 3. Run simple query
snow sql --connection-name "my-profile" \
  --query "SELECT CURRENT_USER();"
```

Expected output:
```
CURRENT_USER()
--------------
ALEX.CHEN
```

### Common Errors & Fixes

**Error**: `Invalid account identifier`
**Fix**: Check format - should be `account.region`, not full URL

**Error**: `Incorrect username or password`
**Fix**: Verify credentials, check for typos

**Error**: `No warehouse specified`
**Fix**: Add `--warehouse` to profile or specify in query

**Error**: `Profile not found`
**Fix**: Check profile name, verify with `snow connection list`

---

## Quick Reference

### Minimal Profile (Testing)
```bash
snow connection add \
  --connection-name "NAME" \
  --account "ACCOUNT.REGION" \
  --user "USERNAME" \
  --password
```

### Standard Profile (Development)
```bash
snow connection add \
  --connection-name "NAME" \
  --account "ACCOUNT.REGION" \
  --user "USERNAME" \
  --private-key-file "PATH/TO/KEY" \
  --warehouse "WAREHOUSE" \
  --database "DATABASE"
```

### Full Profile (Production)
```bash
snow connection add \
  --connection-name "NAME" \
  --account "ACCOUNT.REGION" \
  --user "USERNAME" \
  --private-key-file "PATH/TO/KEY" \
  --warehouse "WAREHOUSE" \
  --database "DATABASE" \
  --schema "SCHEMA" \
  --role "ROLE"
```

---

## Next Steps

1. Create profile using appropriate example above
2. Test with `snow connection test`
3. Start Nanuk MCP: `nanuk-mcp --profile NAME`
4. Try first query in Claude Code

**See also**:
- `02_5_minute_quickstart.md` - Fast setup guide
- `04_account_identifier_guide.md` - More account ID examples
- `03_common_errors.md` - Troubleshooting

---

**Key Takeaway**: Start with minimal profile for testing, add parameters as needed. Most confusion comes from trying to set everything at once without understanding what's required vs optional.
