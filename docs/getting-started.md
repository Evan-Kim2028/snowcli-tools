# Getting Started with SnowCLI Tools

> **Quick Start**: Set up your Snowflake profile → Install SnowCLI Tools → Start using powerful data operations and MCP integration

## Prerequisites

**Required**:
1. **Python 3.12+** with `uv` or pip package manager
   - Check: `python --version`
   - Install: https://www.python.org/downloads/

2. **Snowflake CLI** (Official package - separate from this tool)
   - Install: `pip install nanuk`
   - Check: `snow --version`
   - Docs: https://docs.snowflake.com/en/developer-guide/nanuk/
   - Purpose: Manages Snowflake authentication profiles

3. **Snowflake account** with appropriate permissions
   - Need: USAGE on warehouse/database/schema
   - Need: SELECT on INFORMATION_SCHEMA
   - Contact your Snowflake admin if unsure

**Recommended**:
4. **Private key file** (for key-pair authentication) or use other auth methods

## Step 1: Install SnowCLI Tools

### Installation Methods

**Option 1: PyPI Installation (Recommended for most users)**
```bash
pip install nanuk-mcp
```

**Option 2: Development Installation (For contributors and latest features)**
```bash
# Clone and install the project
git clone https://github.com/Evan-Kim2028/nanuk-mcp
cd nanuk-mcp

# Install with uv (recommended)
uv sync
```

### Command Prefixes: `uv run` vs Direct Commands

**When to use `uv run`**:
- ✅ Development installation (git clone + uv sync)
- ✅ Testing new features
- ✅ Contributing to the project

**When to use direct commands**:
- ✅ PyPI installation (`pip install nanuk-mcp`)
- ✅ Production environments
- ✅ CI/CD pipelines

**Examples**:
```bash
# Development installation (use uv run)
uv run nanuk --profile my-profile verify
uv run nanuk --profile my-profile catalog -d MY_DB

# PyPI installation (direct commands)
nanuk --profile my-profile verify
nanuk --profile my-profile catalog -d MY_DB
```

**Quick check**: If you installed with `pip install nanuk-mcp`, use direct commands. If you installed with `git clone` + `uv sync`, use `uv run` prefix.

## Step 2: Set Up Your Snowflake Profile

**This is the most critical step** - SnowCLI Tools requires a properly configured Snowflake CLI profile for authentication and connection management.

### Option A: Key-Pair Authentication (Recommended)

#### Step 1: Generate RSA Key Pair

```bash
# Create .snowflake directory
mkdir -p ~/.snowflake

# Generate private key (unencrypted for simplicity)
openssl genrsa -out ~/.snowflake/snowflake_rsa_key.pem 2048

# Generate public key
openssl rsa -in ~/.snowflake/snowflake_rsa_key.pem \
    -pubout -out ~/.snowflake/snowflake_rsa_key.pub

# Set proper permissions (important!)
chmod 400 ~/.snowflake/snowflake_rsa_key.pem
chmod 400 ~/.snowflake/snowflake_rsa_key.pub
```

#### Step 2: Upload Public Key to Snowflake

```sql
-- Copy your public key (remove header/footer)
-- From: ~/.snowflake/snowflake_rsa_key.pub
-- Remove "-----BEGIN PUBLIC KEY-----" and "-----END PUBLIC KEY-----"
-- Remove all newlines to create single-line string

-- In Snowflake, run:
ALTER USER <your_username> SET RSA_PUBLIC_KEY='<your_public_key_string>';

-- Verify it was set
DESC USER <your_username>;
-- Look for RSA_PUBLIC_KEY_FP (fingerprint)
```

**Helper Script**:
```bash
# Format public key for Snowflake
cat ~/.snowflake/snowflake_rsa_key.pub | \
    grep -v "BEGIN PUBLIC KEY" | \
    grep -v "END PUBLIC KEY" | \
    tr -d '\n'

echo ""
echo "Copy the above string and run in Snowflake:"
echo "ALTER USER <username> SET RSA_PUBLIC_KEY='<paste here>';"
```

#### Step 3: Create Profile

```bash
# Create a new profile with private key authentication
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --private-key-file "~/.snowflake/snowflake_rsa_key.pem" \
  --database "YOUR_DATABASE" \
  --schema "YOUR_SCHEMA" \
  --warehouse "YOUR_WAREHOUSE" \
  --role "YOUR_ROLE"
```

### Option B: Other Authentication Methods

```bash
# Browser-based OAuth
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --authenticator "externalbrowser" \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE"

# Username/password (not recommended for production)
uv run snow connection add \
  --connection-name "my-profile" \
  --account "your-account.region" \
  --user "your-username" \
  --password \
  --database "YOUR_DATABASE" \
  --warehouse "YOUR_WAREHOUSE"
```

### Verify Your Profile

```bash
# List all configured profiles
uv run snow connection list

# Test your profile works
uv run nanuk --profile my-profile verify
```

**Expected output**: ✅ "Verified Snow CLI and profile 'my-profile'"

## Step 3: Basic Usage

### CLI Operations

```bash
# Execute SQL queries
uv run nanuk --profile my-profile query "SELECT CURRENT_VERSION()"

# Build data catalog
uv run nanuk --profile my-profile catalog

# Generate dependency graphs
uv run nanuk --profile my-profile depgraph

# Analyze lineage
uv run nanuk --profile my-profile lineage MY_TABLE
```

### MCP Server (AI Assistant Integration)

```bash
# Start the MCP server for AI assistants
SNOWFLAKE_PROFILE=my-profile uv run nanuk mcp
```

**Success indicators**:
- ✅ FastMCP 2.0 banner appears
- ✅ Profile validation succeeds
- ✅ Health checks pass
- ✅ Server shows "running" status
- ✅ No error messages in output
- ✅ Server stays running (doesn't exit immediately)

**Expected output**:
```
FastMCP 2.0 Server Starting...
✓ Profile 'my-profile' validated successfully
✓ Health checks passed
✓ MCP server running on stdio
✓ Ready for AI assistant connections
```

**If you see errors**:
- "Profile not found" → Check profile exists with `snow connection list`
- "Permission denied" → Verify key file permissions (`chmod 400`)
- "JWT token invalid" → Re-upload public key to Snowflake
- "Account not found" → Check account identifier format

## Step 4: Configuration (Optional)

### Profile Configuration File

Snowflake CLI stores your profiles in a configuration file:

**Location**:
- **macOS**: `~/Library/Application Support/snowflake/config.toml`
- **Linux**: `~/.snowflake/config.toml`
- **Windows**: `%USERPROFILE%\.snowflake\config.toml`

**View your profiles**:
```bash
# List all configured profiles
snow connection list

# View the config file directly
cat ~/.snowflake/config.toml  # Linux/Mac
# or
cat ~/Library/Application\ Support/snowflake/config.toml  # macOS
```

**Example config file**:
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

**Manual editing**: You can edit this file directly if needed, but using `snow connection add` is recommended.

### Environment Variables

```bash
# Set default profile
export SNOWFLAKE_PROFILE=my-profile

# Set default paths
export SNOWCLI_CATALOG_DIR=./my_catalog
export SNOWCLI_LINEAGE_DIR=./my_lineage
```

### Configuration File

```yaml
# ~/.nanuk-mcp/config.yml
snowflake:
  profile: "my-profile"

catalog:
  output_dir: "./data_catalogue"

lineage:
  cache_dir: "./lineage_cache"
  max_depth: 3
```

## Common Workflows

### 1. Data Discovery Workflow

```bash
# 1. Build comprehensive catalog
uv run nanuk --profile my-profile catalog

# 2. Explore dependencies
uv run nanuk --profile my-profile depgraph --format dot

# 3. Analyze specific table lineage
uv run nanuk --profile my-profile lineage MY_IMPORTANT_TABLE --depth 2
```

### 2. AI Assistant Integration Workflow

```bash
# 1. Start MCP server
SNOWFLAKE_PROFILE=my-profile uv run nanuk mcp &

# 2. Configure your AI assistant (VS Code, Claude Code, etc.) to connect
# 3. Use AI assistant to query data, analyze schemas, generate insights
```

### 3. Development Workflow

```bash
# 1. Set up profile for development environment
uv run snow connection add --connection-name "dev-profile" ...

# 2. Run operations with explicit profile
uv run nanuk --profile dev-profile query "..."

# 3. Switch between environments easily
SNOWFLAKE_PROFILE=prod-profile uv run nanuk mcp
```

## Architecture Overview

SnowCLI Tools uses a **layered architecture**:

```
┌─────────────────────────────────────┐
│        Your Applications            │
├─────────────────────────────────────┤
│     SnowCLI Tools MCP Server        │  ← AI Assistant Interface
│  (Catalog, Lineage, Dependencies)   │
├─────────────────────────────────────┤
│      Snowflake Labs MCP             │  ← Authentication & Core Tools
│   (Auth, Connection, Security)      │
├─────────────────────────────────────┤
│       Snowflake CLI                 │  ← Profile Management
├─────────────────────────────────────┤
│         Snowflake                   │  ← Your Data Warehouse
└─────────────────────────────────────┘
```

**Key Benefits**:
- **Secure**: Leverages Snowflake's official authentication
- **Powerful**: Combines official tools with advanced analytics
- **Integrated**: Single MCP endpoint for AI assistants
- **Flexible**: Support for multiple profiles and environments

## Troubleshooting

### Authentication Errors

#### "JWT token is invalid"
**Cause**: Public key not properly uploaded to Snowflake or key mismatch

**Solution**:
1. Check public key format:
   ```bash
   # Verify key format
   openssl rsa -in rsa_key.p8 -noout -text
   ```

2. Re-upload public key to Snowflake:
   ```bash
   # Get public key content (remove headers/footers)
   cat rsa_key.pub | grep -v "BEGIN PUBLIC KEY" | grep -v "END PUBLIC KEY" | tr -d '\n'
   ```

3. In Snowflake web UI:
   - Go to your user profile → Edit
   - Paste public key (no headers/footers, no line breaks)
   - Save changes

#### "Account not found"
**Cause**: Incorrect account identifier format

**Solution**:
- Check account format: `account_locator.region` (e.g., `abc12345.us-west-2`)
- Try adding region if missing: `account.region`
- Try adding cloud provider: `account.region.aws`
- Verify account name in Snowflake web UI URL

#### "User not found"
**Cause**: Incorrect username or user doesn't exist

**Solution**:
- Check username spelling (case-insensitive)
- Use email if that's your Snowflake login
- Verify user exists in Snowflake

#### "Permission denied" on key file
**Cause**: Incorrect file permissions

**Solution**:
```bash
# Set correct permissions
chmod 400 rsa_key.p8
chmod 400 rsa_key.pub

# Verify permissions
ls -la rsa_key.p8
# Should show: -r--------
```

### Profile Issues

```bash
# Check if profile exists
uv run snow connection list

# Test Snow CLI directly
uv run snow sql -q "SELECT 1" --connection my-profile

# Recreate profile if needed
uv run snow connection delete --connection-name my-profile
uv run snow connection add --connection-name my-profile ...
```

### Permission Issues

Common permissions needed:
- `USAGE` on warehouse, database, schema
- `SELECT` on `INFORMATION_SCHEMA` tables
- `SHOW` privileges for object discovery
- Role with appropriate access to your data

### MCP Server Issues

```bash
# Check for missing dependencies
uv add "mcp>=1.0.0" "fastmcp>=2.8.1" "snowflake-labs-mcp>=1.3.3"

# Test with debug output
SNOWFLAKE_PROFILE=my-profile uv run nanuk mcp --log-level DEBUG
```

## Next Steps

- **Read the [Architecture Guide](./architecture.md)** to understand the service layer design
- **Explore [MCP Integration](./mcp/mcp_server_user_guide.md)** for AI assistant setup
- **Check [API Reference](./api/README.md)** for programmatic usage
- **Review [Configuration](./configuration.md)** for advanced settings

## Support

- **Documentation**: Check `/docs` folder for detailed guides
- **Issues**: Report problems via GitHub issues
- **Examples**: See `/examples` directory for common use cases

---

*Version 1.9.0 | Updated: 2025-10-07*