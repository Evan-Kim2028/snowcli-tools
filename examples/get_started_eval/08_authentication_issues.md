# Authentication Setup Issues - New User Perspective

**Date**: October 7, 2025
**Focus**: Specific authentication and profile setup problems

---

## Overview

This document details all authentication-related confusion points a new user encounters when trying to set up SnowCLI Tools. Based on actual documentation review and testing.

---

## Issue 1: Missing Prerequisites - What is Snowflake CLI?

### Documentation Shows

README.md (Line 121-124):
```markdown
## Requirements

- **Python**: 3.12 or higher
- **Snowflake CLI**: Latest version recommended
- **Dependencies**: Automatically installed with package
- **Permissions**: `USAGE` on warehouse/database/schema, `SELECT` on `INFORMATION_SCHEMA`
```

### Problems

❌ **No explanation of what "Snowflake CLI" is**:
- Is it part of this package?
- Is it separate?
- Where to get it?
- How to install it?

❌ **No installation instructions**:
- Says "Latest version recommended"
- Doesn't say how to install it
- Doesn't link to documentation

❌ **Confusion with command names**:
- Uses `snow` command (Snowflake CLI)
- Uses `snowflake-cli` command (this package)
- New user doesn't know these are different

### What New User Needs

```markdown
### Prerequisites

1. **Python 3.12+**
   - Check: `python --version`
   - Install: https://www.python.org/downloads/

2. **Snowflake CLI (Official)** - Required separate package
   - Install: `pip install snowflake-cli`
   - Check: `snow --version`
   - Docs: https://docs.snowflake.com/en/developer-guide/snowflake-cli/
   - Purpose: Manages authentication profiles for Snowflake

3. **SnowCLI Tools (This Package)**
   - Install: `pip install snowcli-tools`
   - Check: `snowflake-cli --version`
   - Purpose: Enhanced analytics and MCP server
```

---

## Issue 2: Profile Setup - The `snow connection add` Mystery

### Documentation Shows (README Line 26-29)

```bash
# 2. Set up your Snowflake profile
snow connection add --connection-name "my-profile" \
  --account "your-account.region" --user "your-username" \
  --private-key-file "/path/to/key.p8" --database "DB" --warehouse "WH"
```

### Problems Identified

#### Problem A: Private Key Mystery

❌ **No explanation of private key requirement**:
- What is a private key?
- Why do I need it?
- Where do I get one?
- How do I generate it?

❌ **No mention of public key**:
- Private key alone doesn't work
- Need to upload public key to Snowflake
- This critical step is completely missing

❌ **File format confusion**:
- Shows `.p8` extension
- What is PKCS#8 format?
- Can I use `.pem` instead?

#### Problem B: Account Identifier Confusion

Example shows: `--account "your-account.region"`

❌ **Questions not answered**:
- What's my account identifier?
- Where do I find it in Snowflake?
- Is "region" literal or placeholder?
- Examples of valid formats?

**Actual format examples** (not in docs):
```
# Format 1: Account locator with region
abc12345.us-west-2

# Format 2: Organization name (newer accounts)
myorg-myaccount

# Format 3: With cloud provider
abc12345.us-west-2.aws
```

#### Problem C: Parameter Requirements Unclear

The command shows:
```bash
--account "your-account.region"
--user "your-username"
--private-key-file "/path/to/key.p8"
--database "DB"
--warehouse "WH"
```

❌ **Not specified**:
- Which parameters are required?
- Which are optional?
- What happens if I omit database?
- What happens if I omit warehouse?

**Reality** (discovered through testing):
- `--account`: REQUIRED
- `--user`: REQUIRED
- `--private-key-file`: REQUIRED (if using key auth)
- `--database`: OPTIONAL (can set later)
- `--warehouse`: OPTIONAL (can set later)
- `--role`: OPTIONAL (not shown in example!)
- `--schema`: OPTIONAL (not shown in example!)

### Problem D: No Verification Step

After running `snow connection add`, documentation doesn't say:
- How to verify it worked
- How to test the connection
- Where the profile is stored
- How to see profile details

### What New User Needs

```markdown
## Setting Up Authentication

### Step 1: Generate Key Pair

SnowCLI Tools recommends key-pair authentication for security.

```bash
# Generate private key (PKCS#8 format, no encryption)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Generate public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

**Security Note**: Store `rsa_key.p8` securely. Never commit to git.

### Step 2: Upload Public Key to Snowflake

1. Copy public key content:
   ```bash
   cat rsa_key.pub
   ```

2. In Snowflake web UI:
   - Go to your user profile (top right)
   - Click "Edit"
   - Paste public key in "Public Key" field
   - Remove "-----BEGIN PUBLIC KEY-----" header
   - Remove "-----END PUBLIC KEY-----" footer
   - Remove all line breaks
   - Click "Save"

3. Or use SQL:
   ```sql
   ALTER USER your_username SET RSA_PUBLIC_KEY='YOUR_PUBLIC_KEY_HERE';
   ```

### Step 3: Find Your Account Identifier

In Snowflake web UI, your URL shows your account:
```
https://abc12345.us-west-2.snowflakecomputing.com/
         ^^^^^^^^ ^^^^^^^^^
         account  region
```

Your account identifier is: `abc12345.us-west-2`

### Step 4: Create Profile

```bash
snow connection add \
  --connection-name "my-profile" \
  --account "abc12345.us-west-2" \
  --user "your.email@company.com" \
  --private-key-file "/absolute/path/to/rsa_key.p8" \
  --database "MY_DATABASE" \
  --warehouse "MY_WAREHOUSE" \
  --role "MY_ROLE"
```

**Important**:
- Use absolute path for private key file
- Account identifier is case-insensitive
- User is your Snowflake username (often an email)

### Step 5: Verify Profile

```bash
# List all profiles
snow connection list

# Test connection
snow sql -q "SELECT CURRENT_VERSION()" --connection my-profile

# Expected output:
# +-------------------+
# | CURRENT_VERSION() |
# +-------------------+
# | 8.12.0            |
# +-------------------+
```

### Troubleshooting

**"JWT token is invalid"**:
- Check public key is uploaded to Snowflake correctly
- Ensure no line breaks in public key
- Verify private key matches public key

**"Account not found"**:
- Check account identifier format
- Try adding region: `account.region`
- Try adding cloud: `account.region.aws`

**"User not found"**:
- Check username is exactly as in Snowflake
- Usernames are case-insensitive
- Use email if that's your Snowflake login
```

---

## Issue 3: Config File Location - Undocumented

### What Documentation Shows

Nothing. The config file location is never mentioned in:
- README.md
- docs/getting-started.md
- docs/profile_validation_quickstart.md
- docs/profile_troubleshooting_guide.md

### Actual Behavior

After running `snow connection add`, profile is stored at:

**macOS**:
```
/Users/username/Library/Application Support/snowflake/config.toml
```

**Linux**:
```
~/.snowflake/config.toml
```

**Windows**:
```
%USERPROFILE%\.snowflake\config.toml
```

### Example Config File Content

```toml
default_connection_name = "mystenlabs-keypair"

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

### Problems for New Users

❌ **Can't troubleshoot**:
- Don't know where to look for profiles
- Can't verify profile was created
- Can't manually fix issues

❌ **Can't understand authenticator types**:
- What is "SNOWFLAKE_JWT"?
- Other options available?
- How to use password auth?
- How to use OAuth?

### What New User Needs

```markdown
## Profile Configuration File

### Location

Snowflake CLI stores profiles at:
- **macOS**: `~/Library/Application Support/snowflake/config.toml`
- **Linux**: `~/.snowflake/config.toml`
- **Windows**: `%USERPROFILE%\.snowflake\config.toml`

### View Config

```bash
# List all profiles
snow connection list

# View config file
cat ~/Library/Application\ Support/snowflake/config.toml
```

### Manual Editing

You can manually edit `config.toml`:

```toml
# Set default connection
default_connection_name = "my-profile"

# Define connection
[connections.my-profile]
account = "abc12345.us-west-2"
user = "your.email@company.com"
database = "MY_DATABASE"
warehouse = "MY_WAREHOUSE"
role = "MY_ROLE"

# Key-pair authentication
authenticator = "SNOWFLAKE_JWT"
private_key_file = "/path/to/rsa_key.p8"
```

### Authenticator Types

| Type | Value | When to Use |
|------|-------|-------------|
| Key-pair | `SNOWFLAKE_JWT` | Recommended for automation |
| OAuth | `externalbrowser` | Interactive login |
| Password | `snowflake` (default) | Not recommended |
| Okta | `https://your-okta-url.com` | Enterprise SSO |
```

---

## Issue 4: Authentication Method Options - Incomplete

### Documentation Shows (Getting Started Line 44-64)

Three options shown:
1. Key-pair authentication (recommended)
2. Browser-based OAuth
3. Username/password

### Problems

#### OAuth Example Issues

```bash
# Browser-based OAuth
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --authenticator "externalbrowser" \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE"
```

❌ **Missing information**:
- What happens after running this?
- Browser should open - not mentioned
- How to handle if browser doesn't open?
- Can I use this for automated scripts? (No!)

#### Password Auth Warning

```bash
# Username/password (not recommended for production)
```

❌ **Inadequate warning**:
- Should explain WHY not recommended
- Should mention it prompts for password
- Should warn about credential storage

#### Missing Auth Methods

❌ **Not documented**:
- Okta SSO
- Azure AD
- Other SAML providers
- Service account best practices

### What New User Needs

```markdown
## Authentication Methods Comparison

### Key-Pair Authentication (Recommended)

**Best for**: Production, automation, CI/CD

**Pros**:
- Most secure
- No password storage
- Works in scripts
- No browser required

**Cons**:
- Requires key generation
- Requires Snowflake admin to upload public key

**Setup**:
```bash
# 1. Generate keys (see above)
# 2. Upload public key to Snowflake
# 3. Create profile
snow connection add \
  --connection-name "my-profile" \
  --account "account.region" \
  --user "username" \
  --private-key-file "/path/to/rsa_key.p8" \
  --authenticator "SNOWFLAKE_JWT"
```

### OAuth (External Browser)

**Best for**: Interactive development, local testing

**Pros**:
- Easy setup
- Uses existing Snowflake login
- Works with SSO

**Cons**:
- Requires browser
- Can't use in automation
- Session expires

**Setup**:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "account.region" \
  --user "username" \
  --authenticator "externalbrowser"
```

**Usage**:
- First command will open browser
- Authenticate in browser
- Token cached for ~4 hours
- Will re-prompt when expired

### Username/Password (Not Recommended)

**Best for**: Quick testing only

**Pros**:
- Simplest setup

**Cons**:
- **Security risk**: Password stored in config
- **Not for production**: Violates security best practices
- **Will break**: If password changes

**Setup**:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "account.region" \
  --user "username" \
  --password  # Will prompt
```

### Enterprise SSO (Okta, Azure AD, etc.)

**Best for**: Enterprise environments with SSO

**Setup**:
```bash
snow connection add \
  --connection-name "my-profile" \
  --account "account.region" \
  --user "username" \
  --authenticator "https://your-okta-url.okta.com"
```

**Note**: Contact your Snowflake admin for exact authenticator URL.
```

---

## Issue 5: Profile Selection - Inconsistent Documentation

### Three Different Methods Shown

#### Method 1: Command Flag (README)
```bash
snowflake-cli verify -p my-profile
```
❌ **Doesn't work!** (No `-p` flag exists)

#### Method 2: Global Flag (Actual)
```bash
snowflake-cli --profile my-profile verify
```
✅ **Works** but not shown in many examples

#### Method 3: Environment Variable (README Line 115)
```bash
export SNOWFLAKE_PROFILE=my-profile
```
✅ **Works** but precedence not explained

### Problems

❌ **No precedence explanation**:
- What if both flag and env var set?
- What if config file has default?
- Which takes priority?

❌ **Inconsistent examples**:
- Some use `-p` (wrong)
- Some use `--profile` (correct)
- Some use env var
- Some omit entirely

### Testing Results

Tested with existing profile "mystenlabs-keypair":

```bash
# Test 1: Wrong syntax from docs
$ uv run snowflake-cli verify -p mystenlabs-keypair
Error: No such option: -p
❌ FAIL

# Test 2: Correct global flag
$ uv run snowflake-cli --profile mystenlabs-keypair verify
✓ Verified Snow CLI and profile 'mystenlabs-keypair'.
✅ SUCCESS

# Test 3: Environment variable
$ SNOWFLAKE_PROFILE=mystenlabs-keypair uv run snowflake-cli verify
✓ Verified Snow CLI and profile 'mystenlabs-keypair'.
✅ SUCCESS

# Test 4: No profile specified
$ uv run snowflake-cli verify
✓ Verified Snow CLI and profile 'mystenlabs-keypair'.
✅ SUCCESS (uses default from config)
```

### What New User Needs

```markdown
## Specifying Which Profile to Use

### Method 1: Global Flag (Explicit)

```bash
snowflake-cli --profile PROFILE_NAME COMMAND
```

**Example**:
```bash
snowflake-cli --profile prod verify
snowflake-cli --profile dev catalog -d MY_DB
```

**Note**: `--profile` must come BEFORE the subcommand.

### Method 2: Environment Variable (Session)

```bash
export SNOWFLAKE_PROFILE=PROFILE_NAME
snowflake-cli COMMAND
```

**Example**:
```bash
export SNOWFLAKE_PROFILE=prod
snowflake-cli verify
snowflake-cli catalog -d MY_DB
```

### Method 3: Default Profile (Implicit)

Set in Snowflake CLI config:
```bash
snow connection set-default PROFILE_NAME
```

Then just run commands:
```bash
snowflake-cli verify
snowflake-cli catalog -d MY_DB
```

### Precedence Order

1. **Global flag** `--profile` (highest priority)
2. **Environment variable** `SNOWFLAKE_PROFILE`
3. **Default profile** in config file
4. **Error** if none set

### Checking Current Profile

```bash
# Method 1: View config
snowflake-cli config

# Method 2: Check Snow CLI default
snow connection list
# Look for "(default)" next to profile name
```

### Common Mistakes

❌ **Wrong**: `snowflake-cli verify -p my-profile`
✅ **Right**: `snowflake-cli --profile my-profile verify`

❌ **Wrong**: `snowflake-cli catalog --profile prod`
✅ **Right**: `snowflake-cli --profile prod catalog`

**Remember**: Global flags go BEFORE subcommand!
```

---

## Issue 6: Permissions - Vague Requirements

### Documentation Shows (README Line 174)

```markdown
- **Permissions**: `USAGE` on warehouse/database/schema, `SELECT` on `INFORMATION_SCHEMA`
```

### Problems

❌ **Too vague**:
- What role needs these permissions?
- Are there different requirements for different commands?
- What about `SHOW` privilege?
- What about specific object types?

❌ **No SQL examples**:
- How to grant these permissions?
- What if I'm not admin?
- How to check current permissions?

❌ **No troubleshooting**:
- What errors indicate permission issues?
- How to diagnose permission problems?

### What New User Needs

```markdown
## Required Snowflake Permissions

### Minimum Permissions

Your Snowflake user/role needs:

```sql
-- Warehouse access
GRANT USAGE ON WAREHOUSE your_warehouse TO ROLE your_role;

-- Database access
GRANT USAGE ON DATABASE your_database TO ROLE your_role;

-- Schema access
GRANT USAGE ON SCHEMA your_database.your_schema TO ROLE your_role;

-- Read metadata
GRANT SELECT ON ALL TABLES IN SCHEMA your_database.INFORMATION_SCHEMA TO ROLE your_role;
GRANT SELECT ON ALL VIEWS IN SCHEMA your_database.INFORMATION_SCHEMA TO ROLE your_role;

-- Show objects (for catalog/lineage)
GRANT MONITOR ON ACCOUNT TO ROLE your_role;
```

### Permissions by Command

| Command | Required Permissions | Why |
|---------|---------------------|-----|
| `verify` | Basic connection | Test auth |
| `query` | SELECT on target objects | Run queries |
| `catalog` | USAGE on DB/schema, SELECT on INFORMATION_SCHEMA, SHOW | Scan metadata |
| `lineage` | Same as catalog + access history | Track dependencies |
| `depgraph` | Same as catalog | Build graph |

### Checking Your Permissions

```sql
-- See current role
SELECT CURRENT_ROLE();

-- See grants for your role
SHOW GRANTS TO ROLE your_role;

-- Test database access
SHOW DATABASES;

-- Test warehouse access
SHOW WAREHOUSES;

-- Test schema access
SHOW SCHEMAS IN DATABASE your_database;
```

### Common Permission Errors

**"SQL access control error"**:
```
Access denied on INFORMATION_SCHEMA
```
Fix: Need SELECT on INFORMATION_SCHEMA
```sql
GRANT SELECT ON SCHEMA your_database.INFORMATION_SCHEMA TO ROLE your_role;
```

**"Object does not exist"**:
```
Database 'MY_DB' does not exist or not authorized
```
Fix: Need USAGE on database
```sql
GRANT USAGE ON DATABASE my_db TO ROLE your_role;
```

**"Insufficient privileges"**:
```
Insufficient privileges to operate on warehouse 'MY_WH'
```
Fix: Need USAGE on warehouse
```sql
GRANT USAGE ON WAREHOUSE my_wh TO ROLE your_role;
```

### If You're Not Admin

Contact your Snowflake administrator and request:
1. Role with appropriate grants
2. Access to specific warehouse
3. Access to databases you need to catalog
4. MONITOR privilege for lineage tracking

Provide them this SQL template they can run:
```sql
-- Grant necessary permissions for SnowCLI Tools
GRANT USAGE ON WAREHOUSE your_warehouse TO ROLE your_role;
GRANT USAGE ON DATABASE your_database TO ROLE your_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE your_database TO ROLE your_role;
GRANT SELECT ON ALL TABLES IN SCHEMA your_database.INFORMATION_SCHEMA TO ROLE your_role;
GRANT MONITOR ON ACCOUNT TO ROLE your_role;
```
```

---

## Summary of Authentication Documentation Gaps

### Critical Gaps

1. ✗ No Snowflake CLI installation instructions
2. ✗ No key generation steps
3. ✗ No public key upload instructions
4. ✗ No config file location documentation
5. ✗ Command syntax errors (`-p` vs `--profile`)

### High Priority Gaps

6. ✗ No authenticator comparison guide
7. ✗ No profile verification steps
8. ✗ No permission troubleshooting
9. ✗ No account identifier format examples
10. ✗ No precedence explanation for profile selection

### Medium Priority Gaps

11. ✗ No SQL permission grant examples
12. ✗ No error message explanations
13. ✗ No "where to find" guides (account ID, etc.)
14. ✗ No OAuth session management info
15. ✗ No enterprise SSO details

---

## Recommendations

### Quick Wins (< 1 hour)

1. Add Snowflake CLI installation to Prerequisites
2. Fix all `-p` flags to `--profile`
3. Add config file location to docs
4. Add profile verification step after creation
5. Add "Checking Current Profile" section

### Medium Effort (2-4 hours)

6. Write complete key-pair auth tutorial
7. Add authentication method comparison table
8. Document profile selection precedence
9. Add permission checking SQL examples
10. Create troubleshooting section for auth errors

### High Effort (1-2 days)

11. Create video/screenshot tutorial for key upload
12. Write comprehensive permission guide
13. Add interactive troubleshooting flowchart
14. Create auth method decision tree
15. Build profile testing script

---

## Test Script for Documentation

Suggested script to validate auth docs:

```bash
#!/bin/bash
# Test authentication documentation accuracy

echo "=== Authentication Setup Test ==="

# Test 1: Check Snowflake CLI installed
echo "Test 1: Snowflake CLI availability"
if command -v snow &> /dev/null; then
    echo "✓ snow command found"
else
    echo "✗ snow command not found - DOCS SHOULD MENTION THIS"
fi

# Test 2: Check snowcli-tools installed
echo "Test 2: SnowCLI Tools availability"
if command -v snowflake-cli &> /dev/null; then
    echo "✓ snowflake-cli command found"
else
    echo "✗ snowflake-cli command not found"
fi

# Test 3: Find config file
echo "Test 3: Config file location"
if [ -f "$HOME/.snowflake/config.toml" ]; then
    echo "✓ Found at ~/.snowflake/config.toml"
elif [ -f "$HOME/Library/Application Support/snowflake/config.toml" ]; then
    echo "✓ Found at ~/Library/Application Support/snowflake/config.toml"
else
    echo "✗ Config file not found"
fi

# Test 4: Test command syntax from docs
echo "Test 4: Command syntax from docs"
if snowflake-cli verify -p test 2>&1 | grep -q "No such option"; then
    echo "✗ Docs show 'verify -p' but it doesn't work"
else
    echo "? Command syntax test inconclusive"
fi

echo "=== Test Complete ==="
```

---

## Conclusion

**Authentication setup is the #1 blocker for new users.**

Current state: 🔴 **Unusable without external research**

Needed: Complete rewrite of authentication section with:
- Step-by-step tutorial
- Command examples that work
- Verification steps
- Troubleshooting guide
- Visual aids (screenshots/diagrams)

**Priority**: P0 - Blocks all usage
