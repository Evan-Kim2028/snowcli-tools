# Profile Validation Quick-Start Guide

## Overview

Nanuk MCP v2.0+ features robust profile validation that provides clear, actionable guidance when configuration issues occur. This guide helps you set up and validate your Snowflake profiles for use with the MCP server.

## 🚀 Before You Start

### What You Need
1. **Snowflake CLI installed**: The `snow` command-line tool for profile management
2. **Valid Snowflake account**: Access to a Snowflake instance
3. **Authentication credentials**: Key-pair, OAuth, or password credentials
4. **nanuk-mcp v2.0+**: Latest MCP-only version
5. **AI Assistant**: Claude Code, Cline, Continue, Zed, or any MCP-compatible client

### Quick Installation Check
```bash
# Check if snow CLI is installed
snow --version

# Check nanuk-mcp version
python -c "import nanuk_mcp; print(nanuk_mcp.__version__)"
# Should show 2.0.0 or higher

# Install/upgrade if needed
pip install --upgrade nanuk-mcp
```

## 🎯 Quick Profile Setup

### Option 1: Password Authentication (Quickest for Getting Started)

```bash
# Create profile with password
snow connection add \
  --connection-name quickstart \
  --account <your-account>.<region> \
  --user <your-username> \
  --password \
  --warehouse <your-warehouse>

# Password will be prompted securely
```

**Best for**: Testing, development, getting started quickly

### Option 2: Key-Pair Authentication (Recommended for Production)

```bash
# 1. Generate RSA key pair
mkdir -p ~/.snowflake
openssl genrsa -out ~/.snowflake/key.pem 2048
openssl rsa -in ~/.snowflake/key.pem -pubout -out ~/.snowflake/key.pub
chmod 400 ~/.snowflake/key.pem

# 2. Upload public key to Snowflake (see instructions below)

# 3. Create profile
snow connection add \
  --connection-name quickstart \
  --account <your-account>.<region> \
  --user <your-username> \
  --private-key-file ~/.snowflake/key.pem \
  --warehouse <your-warehouse> \
  --database <your-database> \
  --default
```

**Best for**: Automation, production, CI/CD

**Upload public key**:
```bash
# Format key for Snowflake
cat ~/.snowflake/key.pub | grep -v "BEGIN\|END" | tr -d '\n'

# In Snowflake, run:
ALTER USER <your_username> SET RSA_PUBLIC_KEY='<paste_key_here>';
```

### Option 3: OAuth/SSO Authentication (Interactive)

```bash
# Create profile with browser authentication
snow connection add \
  --connection-name quickstart \
  --account <your-account>.<region> \
  --user <your-username> \
  --authenticator externalbrowser \
  --warehouse <your-warehouse> \
  --default
```

**Best for**: Enterprise SSO environments, interactive development

## ✅ Validation Testing

### Step 1: Verify Profile Creation
```bash
# List all profiles
snow connection list

# Test the connection
snow sql -q "SELECT CURRENT_VERSION()" --connection quickstart

# Set as environment default
export SNOWFLAKE_PROFILE=quickstart
```

### Step 2: Configure Your AI Assistant

Add this to your AI assistant's MCP configuration:

**Claude Code** (`~/.config/claude-code/mcp.json`):
```json
{
  "mcpServers": {
    "snowflake": {
      "command": "nanuk-mcp",
      "args": ["--profile", "quickstart"]
    }
  }
}
```

**Cline/Continue** (`~/.continue/config.json`):
```json
{
  "mcpServers": {
    "snowflake": {
      "command": "nanuk-mcp",
      "args": ["--profile", "quickstart"]
    }
  }
}
```

**Restart your AI assistant** after configuration.

### Step 3: Test MCP Connection

In your AI assistant, try:

```
"Test my Snowflake connection"
```

Expected: ✅ Connection successful with profile details

```
"Check the MCP server health"
```

Expected: Server health status showing:
- ✓ Profile validation successful
- ✓ Snowflake connection healthy
- ✓ Available tools listed

## 🔧 Troubleshooting Common Issues

### Issue 1: "Profile not found"

**Error in AI assistant:**
```
❌ Snowflake profile 'default' not found
Available profiles: quickstart, production
```

**Solution:**
```bash
# Option A: Use existing profile
# Update your MCP config to use "quickstart" instead of "default"

# Option B: Create missing profile
snow connection add --connection-name default
```

### Issue 2: "No profiles configured"

**Error:**
```
❌ No Snowflake profiles found
Please run 'snow connection add' to create a profile
```

**Solution:**
```bash
# Create your first profile
snow connection add \
  --connection-name my-first-profile \
  --account <your-account>.<region> \
  --user <your-username> \
  --password
```

### Issue 3: "Authentication failed"

**Error:**
```
❌ Authentication failed for profile 'quickstart'
```

**Solution for Key-Pair:**
```bash
# Check private key file permissions
chmod 400 ~/.snowflake/key.pem

# Verify key is uploaded to Snowflake
# Run in Snowflake: DESC USER <your_username>;
# Look for RSA_PUBLIC_KEY_FP

# Re-upload if needed (see Option 2 above)
```

**Solution for Password:**
```bash
# Re-create profile with new password
snow connection add \
  --connection-name quickstart \
  --password
# Enter correct password when prompted
```

**Solution for OAuth:**
```bash
# Re-authenticate with browser
snow sql -q "SELECT 1" --connection quickstart
# Follow browser authentication flow
```

### Issue 4: "MCP tools not showing"

**Problem**: AI assistant doesn't show Snowflake tools

**Solution:**
1. Verify nanuk-mcp is installed: `which nanuk-mcp`
2. Check MCP config JSON is valid (no syntax errors)
3. **Restart AI assistant completely** (most common fix)
4. Check AI assistant logs for startup errors

### Issue 5: "Insufficient privileges"

**Error:**
```
❌ Insufficient privileges for role 'PUBLIC'
```

**Solution:**
```bash
# Check available roles
snow sql -q "SHOW GRANTS TO USER <your_username>"

# Update profile with appropriate role
snow connection add \
  --connection-name quickstart \
  --role ANALYST_ROLE
```

## 🎪 Interactive Validation via AI Assistant

### Demo 1: Health Check

Ask your AI assistant:
```
"Check the MCP server health"
```

Expected response includes:
- ✓ Server status (healthy/degraded/unhealthy)
- ✓ Profile validation status
- ✓ Available profiles list
- ✓ Connection health
- ✓ Available MCP tools

### Demo 2: Profile Configuration

Ask your AI assistant:
```
"What Snowflake profile am I using?"
```

Expected response includes:
- Current profile name
- Profile validation status
- Connection parameters (account, warehouse, etc.)

### Demo 3: Test Query

Ask your AI assistant:
```
"Show me my Snowflake databases"
```

Expected: List of databases you have access to

## 📋 Validation Checklist

Use this checklist to ensure your profile validation setup is correct:

### Basic Setup
- [ ] **Snowflake CLI installed**: `snow --version` works
- [ ] **nanuk-mcp v2.0+**: `python -c "import nanuk_mcp; print(nanuk_mcp.__version__)"` shows 2.0.0+
- [ ] **Profile created**: `snow connection list` shows your profile
- [ ] **Profile tested**: `snow sql -q "SELECT 1" --connection <profile>` succeeds
- [ ] **AI assistant configured**: MCP config includes nanuk-mcp with correct profile

### MCP Integration
- [ ] **MCP config valid**: JSON syntax is correct
- [ ] **AI assistant restarted**: Restarted after configuration
- [ ] **Tools visible**: AI assistant shows Snowflake MCP tools
- [ ] **Connection works**: "Test my Snowflake connection" succeeds in AI assistant

### Error Handling
- [ ] **Invalid profile handled**: Clear error when using nonexistent profile
- [ ] **No profiles handled**: Clear guidance when no profiles exist
- [ ] **Authentication errors clear**: Specific guidance for auth failures
- [ ] **Permission errors actionable**: Clear next steps for privilege issues

## 🚀 Next Steps

Once your profile validation is working:

1. **Explore MCP Tools**: Try catalog building, lineage analysis, and table profiling
2. **Set up production profiles**: Create profiles for dev/staging/prod environments
3. **Improve security**: Switch to key-pair authentication if using password
4. **Learn advanced features**: Check out [MCP Server User Guide](mcp/mcp_server_user_guide.md)
5. **Review troubleshooting**: Familiarize yourself with [comprehensive troubleshooting guide](profile_troubleshooting_guide.md)

## 💡 Pro Tips

### Environment Management
```bash
# Create environment-specific profiles
export SNOWFLAKE_PROFILE=dev     # For development
export SNOWFLAKE_PROFILE=staging # For staging
export SNOWFLAKE_PROFILE=prod    # For production

# Or configure multiple MCP servers in your AI assistant:
{
  "mcpServers": {
    "snowflake-dev": {
      "command": "nanuk-mcp",
      "args": ["--profile", "dev"]
    },
    "snowflake-prod": {
      "command": "nanuk-mcp",
      "args": ["--profile", "prod"]
    }
  }
}
```

### Security Best Practices
```bash
# Use restrictive permissions for private keys
chmod 400 ~/.snowflake/key.pem

# Never commit private keys to version control
echo "*.pem" >> .gitignore

# Use key-pair auth for automation/CI/CD
# Use OAuth/SSO for interactive development
```

### Configuration Backup
```bash
# Backup your configuration
# macOS:
cp ~/Library/Application\ Support/snowflake/config.toml ~/snowflake-config-backup.toml

# Linux:
cp ~/.config/snowflake/config.toml ~/snowflake-config-backup.toml
```

### Multiple Profile Management
```bash
# List all profiles
snow connection list

# Set default profile (used when --profile not specified)
snow connection set-default my-main-profile

# Test specific profile
snow sql -q "SELECT CURRENT_USER()" --connection my-profile
```

## 🆘 Need Help?

If you encounter issues not covered in this quick-start guide:

1. **Check detailed troubleshooting**: [Profile Troubleshooting Guide](profile_troubleshooting_guide.md)
2. **Review getting started guide**: [Getting Started Guide](getting-started.md)
3. **Check AI assistant logs**: Look for MCP connection errors
4. **Verify Snow CLI works**: Ensure `snow sql -q "SELECT 1"` works independently
5. **Ask the community**: [GitHub Discussions](https://github.com/Evan-Kim2028/nanuk-mcp/discussions)

The profile validation in v2.0+ provides clear, actionable error messages to help you quickly resolve configuration issues!

---

**🐻‍❄️ Nanuk MCP v2.0.0 - MCP-Only Architecture**

*For users migrating from v1.x: See [CLI Migration Guide](cli-to-mcp-migration.md)*
