# Profile Validation Quick-Start Guide

## Overview

The v1.4.4+ release of nanuk-mcp introduces robust profile validation that transforms the user experience from cryptic timeout errors to clear, actionable guidance. This quick-start guide helps you get up and running with the enhanced profile validation system.

## 🚀 Before You Start

### What You Need
1. **Snowflake CLI installed**: The `snow` command-line tool
2. **Valid Snowflake account**: Access to a Snowflake instance
3. **Authentication credentials**: Key-pair, OAuth, or password credentials
4. **nanuk-mcp v1.4.4+**: Latest version with profile validation

### Quick Installation Check
```bash
# Check if snow CLI is installed
snow --version

# Check nanuk-mcp version
nanuk --version
# Should show v1.4.4 or higher

# Install/upgrade if needed
uv pip install --upgrade nanuk-mcp[mcp]
```

## 🎯 Quick Profile Setup

### Option 1: Key-Pair Authentication (Recommended for Automation)

```bash
# Generate RSA key pair (if you don't have one)
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

# Create profile
snow connection add \
  --connection-name quickstart \
  --account YOUR_ACCOUNT \
  --user YOUR_USERNAME \
  --authenticator SNOWFLAKE_JWT \
  --private-key ./rsa_key.p8 \
  --warehouse YOUR_WAREHOUSE \
  --database YOUR_DATABASE \
  --schema YOUR_SCHEMA \
  --role YOUR_ROLE \
  --default
```

### Option 2: OAuth/SSO Authentication (Interactive)

```bash
# Create profile with browser authentication
snow connection add \
  --connection-name quickstart \
  --account YOUR_ACCOUNT \
  --user YOUR_USERNAME \
  --authenticator externalbrowser \
  --warehouse YOUR_WAREHOUSE \
  --database YOUR_DATABASE \
  --schema YOUR_SCHEMA \
  --role YOUR_ROLE \
  --default
```

### Option 3: Username/Password Authentication

```bash
# Create profile with password (less secure)
snow connection add \
  --connection-name quickstart \
  --account YOUR_ACCOUNT \
  --user YOUR_USERNAME \
  --password \
  --warehouse YOUR_WAREHOUSE \
  --database YOUR_DATABASE \
  --schema YOUR_SCHEMA \
  --role YOUR_ROLE \
  --default
```

## ✅ Validation Testing

### Step 1: Verify Profile Creation
```bash
# List all profiles
snow connection list

# Test the connection
snow connection test --connection-name quickstart

# Set as environment default
export SNOWFLAKE_PROFILE=quickstart
```

### Step 2: Test with nanuk-mcp
```bash
# Test basic functionality
nanuk query "SELECT CURRENT_VERSION()"

# Check configuration status
nanuk config status
```

### Step 3: Test MCP Server Startup
```bash
# Start MCP server (should show validation success)
nanuk-mcp

# Expected output:
# ✓ Snowflake profile validation successful: quickstart
# ✓ Profile health check passed for: quickstart
# ✓ Snowflake connection health check passed
# Starting FastMCP server using transport=stdio
```

## 🔧 Troubleshooting Common Issues

### Issue 1: "Profile not found"

**Error:**
```bash
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: quickstart, production
```

**Solution:**
```bash
# Option A: Use existing profile
export SNOWFLAKE_PROFILE=quickstart

# Option B: Create missing profile
snow connection add --connection-name default
```

### Issue 2: "No profiles configured"

**Error:**
```bash
❌ Snowflake profile validation failed
Error: No Snowflake profiles found. Please run 'snow connection add' to create a profile.
```

**Solution:**
```bash
# Create your first profile
snow connection add --connection-name my-first-profile
```

### Issue 3: "Authentication failed"

**Error:**
```bash
❌ Snowflake connection health check failed
Error: Authentication failed for profile 'quickstart'
```

**Solution for Key-Pair:**
```bash
# Check private key file permissions
chmod 600 ./rsa_key.p8

# Verify key format
openssl rsa -in ./rsa_key.p8 -noout -text

# Update profile with correct key path
snow connection add \
  --connection-name quickstart \
  --private-key $(pwd)/rsa_key.p8 \
  --overwrite
```

**Solution for OAuth:**
```bash
# Re-authenticate with browser
snow connection test --connection-name quickstart
# Follow browser authentication flow
```

### Issue 4: "Insufficient privileges"

**Error:**
```bash
❌ Snowflake connection health check failed
Error: Insufficient privileges for role 'PUBLIC'
```

**Solution:**
```bash
# Check available roles
snow sql -q "SHOW GRANTS TO USER $(whoami)"

# Update profile with appropriate role
snow connection add \
  --connection-name quickstart \
  --role ANALYST_ROLE \
  --overwrite
```

## 🎪 Interactive Validation Demo

Try this step-by-step validation demo:

### Demo 1: Health Check Through MCP

1. **Start MCP server:**
   ```bash
   nanuk-mcp
   ```

2. **In your AI assistant, ask:**
   ```
   "Check the MCP server health"
   ```

3. **Expected response includes:**
   - Server status (healthy/degraded/unhealthy)
   - Profile validation status
   - Available profiles list
   - Connection health
   - Resource availability

### Demo 2: Profile Configuration Check

1. **In your AI assistant, ask:**
   ```
   "Check my Snowflake profile configuration"
   ```

2. **Expected response includes:**
   - Current profile name
   - Profile validation status
   - Available profiles
   - Configuration recommendations

### Demo 3: Error Scenario Testing

1. **Break the configuration intentionally:**
   ```bash
   export SNOWFLAKE_PROFILE=nonexistent-profile
   nanuk-mcp
   ```

2. **Observe clear error message:**
   ```bash
   ❌ Snowflake profile validation failed
   Error: Snowflake profile 'nonexistent-profile' not found
   Available profiles: quickstart, production
   To fix this issue:
   1. Set SNOWFLAKE_PROFILE environment variable to one of the available profiles
   2. Or pass --profile <profile_name> when starting the server
   3. Or run 'snow connection add' to create a new profile
   ```

3. **Fix the configuration:**
   ```bash
   export SNOWFLAKE_PROFILE=quickstart
   nanuk-mcp
   ```

## 📋 Validation Checklist

Use this checklist to ensure your profile validation setup is working correctly:

### Basic Setup
- [ ] **Snowflake CLI installed**: `snow --version` works
- [ ] **nanuk-mcp v1.4.4+**: `nanuk --version` shows correct version
- [ ] **Profile created**: `snow connection list` shows your profile
- [ ] **Profile tested**: `snow connection test --connection-name <profile>` succeeds

### Validation Features
- [ ] **Environment variable set**: `echo $SNOWFLAKE_PROFILE` shows your profile
- [ ] **MCP server starts cleanly**: No errors during `nanuk-mcp` startup
- [ ] **Health check works**: AI assistant can check server health
- [ ] **Profile diagnostics work**: AI assistant can validate profile configuration

### Error Handling
- [ ] **Invalid profile handled**: Clear error when using nonexistent profile
- [ ] **No profiles handled**: Clear guidance when no profiles exist
- [ ] **Authentication errors clear**: Specific guidance for auth failures
- [ ] **Permission errors actionable**: Clear next steps for privilege issues

## 🚀 Next Steps

Once your profile validation is working:

1. **Explore diagnostic tools**: Use the health monitoring MCP tools
2. **Set up production profiles**: Create profiles for different environments
3. **Configure automation**: Use environment variables for CI/CD
4. **Review advanced features**: Check out lineage analysis and catalog building
5. **Read troubleshooting guide**: Familiarize yourself with the [comprehensive troubleshooting guide](profile_troubleshooting_guide.md)

## 💡 Pro Tips

### Environment Management
```bash
# Create environment-specific profiles
export SNOWFLAKE_PROFILE=dev     # For development
export SNOWFLAKE_PROFILE=staging # For staging
export SNOWFLAKE_PROFILE=prod    # For production
```

### Security Best Practices
```bash
# Use restrictive permissions for private keys
chmod 600 ~/.ssh/snowflake_rsa_key.p8

# Store keys in secure locations
mkdir -p ~/.ssh
mv rsa_key.p8 ~/.ssh/snowflake_rsa_key.p8
```

### Configuration Backup
```bash
# Backup your configuration
cp ~/Library/Application\ Support/snowflake/config.toml ~/Desktop/snowflake-config-backup.toml
```

### Multiple Profile Management
```bash
# List all profiles
snow connection list

# Set default profile
snow connection set-default my-main-profile

# Use specific profile for one command
nanuk --profile special-profile query "SELECT 1"
```

## 🆘 Need Help?

If you encounter issues not covered in this quick-start guide:

1. **Check the detailed troubleshooting guide**: [Profile Troubleshooting Guide](profile_troubleshooting_guide.md)
2. **Enable debug logging**: `export SNOWCLI_MCP_LOG_LEVEL=DEBUG`
3. **Test with diagnostic tools**: Use the MCP health monitoring tools
4. **Verify underlying CLI**: Ensure `snow` CLI works independently

The enhanced profile validation in v1.4.4+ is designed to catch and clearly explain configuration issues, making it much easier to get up and running quickly!
