# Profile Configuration & Troubleshooting Guide

## Overview

Starting with v1.4.4, nanuk-mcp includes robust profile validation and enhanced error reporting that makes it easier to diagnose and fix configuration issues. This guide provides comprehensive troubleshooting steps for common profile-related problems.

## Key Improvements in v1.4.4+

### ✅ What's New
- **Startup Validation**: Profile issues are detected immediately when starting the MCP server
- **Clear Error Messages**: No more confusing timeout errors - you get specific, actionable guidance
- **Diagnostic Tools**: New MCP tools for checking profile health and configuration status
- **Enhanced Error Reporting**: MCP-compliant error responses with detailed context

### ✅ Before vs After

**Before v1.4.4 (Confusing Experience):**
```bash
$ nanuk-mcp
Starting MCP server...
# Server appears to start successfully, but first tool call fails with:
Connection timeout error after 30 seconds
```

**After v1.4.4 (Clear Feedback):**
```bash
$ nanuk-mcp
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: evan-oauth, mystenlabs-keypair
To fix this issue:
1. Set SNOWFLAKE_PROFILE environment variable to one of the available profiles
2. Or pass --profile <profile_name> when starting the server
3. Or run 'snow connection add' to create a new profile
```

## Common Error Scenarios & Solutions

### 1. Profile Not Found

**Error Message:**
```bash
❌ Snowflake profile validation failed
Error: Snowflake profile 'default' not found
Available profiles: evan-oauth, mystenlabs-keypair
```

**Root Cause:** The specified profile doesn't exist in your Snowflake CLI configuration.

**Solutions:**

**Option A: Use an existing profile**
```bash
# Set environment variable (recommended)
export SNOWFLAKE_PROFILE=evan-oauth

# Or pass it when starting the server
nanuk-mcp --profile evan-oauth
```

**Option B: Create the missing profile**
```bash
# Interactive setup
snow connection add --connection-name default

# Non-interactive setup (example for key-pair auth)
snow connection add \
  --connection-name default \
  --account your-account \
  --user your-username \
  --authenticator SNOWFLAKE_JWT \
  --private-key /path/to/rsa_key.p8 \
  --warehouse your-warehouse \
  --database your-database \
  --schema your-schema \
  --default
```

### 2. No Profiles Configured

**Error Message:**
```bash
❌ Snowflake profile validation failed
Error: No Snowflake profiles found. Please run 'snow connection add' to create a profile.
Expected config file at: ~/Library/Application Support/snowflake/config.toml
```

**Root Cause:** No Snowflake CLI profiles have been configured on this system.

**Solution:**
```bash
# Create your first profile
snow connection add

# For automation (key-pair example)
snow connection add \
  --connection-name production \
  --account your-account \
  --user your-username \
  --authenticator SNOWFLAKE_JWT \
  --private-key /path/to/rsa_key.p8 \
  --warehouse COMPUTE_WH \
  --database ANALYTICS \
  --schema PUBLIC \
  --role ANALYST_ROLE \
  --default \
  --no-interactive
```

### 3. Profile Configuration Invalid

**Error Message:**
```bash
❌ Snowflake profile validation failed
Error: Profile 'my-profile' configuration is invalid: Missing required field 'account'
```

**Root Cause:** The profile exists but has incomplete or invalid configuration.

**Solution:**
```bash
# Check current profile configuration
snow connection list

# Edit the profile to fix missing fields
snow connection add \
  --connection-name my-profile \
  --account your-missing-account \
  --overwrite

# Or recreate the profile completely
snow connection add --connection-name my-profile
```

### 4. Authentication Failures

**Error Message:**
```bash
❌ Snowflake connection health check failed
Error: Authentication failed for profile 'my-profile'
Details: JWT token validation failed
```

**Root Cause:** Authentication credentials are invalid, expired, or incorrectly configured.

**Solutions:**

**For Key-Pair Authentication:**
```bash
# Verify private key path and permissions
ls -la /path/to/rsa_key.p8
chmod 600 /path/to/rsa_key.p8

# Test the key format
openssl rsa -in /path/to/rsa_key.p8 -noout -text

# Update the profile with correct key path
snow connection add \
  --connection-name my-profile \
  --private-key /correct/path/to/rsa_key.p8 \
  --overwrite
```

**For OAuth/Browser Authentication:**
```bash
# Test the connection to refresh tokens
snow connection test --connection-name my-profile

# If needed, re-authenticate
snow connection add \
  --connection-name my-profile \
  --authenticator externalbrowser \
  --overwrite
```

### 5. Permission Errors

**Error Message:**
```bash
❌ Snowflake connection health check failed
Error: Insufficient privileges for role 'PUBLIC'
Details: Role 'PUBLIC' does not have USAGE privilege on warehouse 'COMPUTE_WH'
```

**Root Cause:** The configured role lacks necessary permissions for the specified warehouse, database, or schema.

**Solution:**
```bash
# Check available roles and warehouses
snow sql -q "SHOW GRANTS TO USER <your-username>"
snow sql -q "SHOW WAREHOUSES"

# Update profile with a role that has appropriate permissions
snow connection add \
  --connection-name my-profile \
  --role ANALYST_ROLE \
  --warehouse SHARED_WH \
  --overwrite
```

## Diagnostic Commands

### Check Profile Status

**List all available profiles:**
```bash
snow connection list
```

**Test specific profile connection:**
```bash
snow connection test --connection-name my-profile
```

**Check nanuk-mcp configuration status:**
```bash
nanuk config status
```

### MCP Server Diagnostics (v1.4.4+)

When the MCP server is running, you can use these diagnostic tools through your AI assistant:

**Check overall health:**
```
health_check
```

**Check profile configuration:**
```
check_profile_config
```

**Get resource availability status:**
```
get_resource_status
```

## Profile Management Best Practices

### 1. Environment-Specific Profiles

Create separate profiles for different environments:

```bash
# Development profile
snow connection add \
  --connection-name dev \
  --account dev-account \
  --warehouse DEV_WH \
  --database DEV_DB \
  --role DEV_ROLE

# Production profile
snow connection add \
  --connection-name prod \
  --account prod-account \
  --warehouse PROD_WH \
  --database PROD_DB \
  --role PROD_ROLE
```

### 2. Set Default Profile

```bash
# Set a default profile
snow connection set-default dev

# Or use environment variables
export SNOWFLAKE_PROFILE=dev
```

### 3. Secure Key Management

```bash
# Store private keys securely
chmod 600 ~/.ssh/snowflake_rsa_key.p8

# Use absolute paths in profiles
snow connection add \
  --connection-name secure-profile \
  --private-key ~/.ssh/snowflake_rsa_key.p8
```

## Advanced Troubleshooting

### Enable Debug Logging

```bash
# Enable debug logging for detailed error information
export SNOWCLI_MCP_LOG_LEVEL=DEBUG
nanuk-mcp
```

### Configuration File Locations

**macOS:**
```
~/Library/Application Support/snowflake/config.toml
```

**Linux:**
```
~/.config/snowflake/config.toml
```

**Windows:**
```
%APPDATA%\snowflake\config.toml
```

### Manual Configuration File Check

```bash
# View the configuration file directly
cat "~/Library/Application Support/snowflake/config.toml"

# Check file permissions
ls -la "~/Library/Application Support/snowflake/config.toml"
```

### Network and Connectivity Issues

**Test basic connectivity:**
```bash
# Test if you can reach Snowflake
ping your-account.snowflakecomputing.com

# Test HTTPS connectivity
curl -I https://your-account.snowflakecomputing.com
```

**Common network issues:**
- Corporate firewalls blocking Snowflake endpoints
- VPN connectivity problems
- DNS resolution issues
- Proxy configuration problems

## Error Code Reference

### MCP Error Codes (v1.4.4+)

| Error Code | Category | Description |
|------------|----------|-------------|
| -32001 | Configuration Error | Profile configuration invalid |
| -32002 | Connection Error | Network or connectivity issue |
| -32003 | Authentication Error | Credentials invalid or expired |
| -32004 | Profile Error | Profile not found or misconfigured |
| -32005 | Resource Unavailable | Required resources not accessible |

### Common Snowflake Error Codes

| Error Code | Description | Common Causes |
|------------|-------------|---------------|
| 250001 | Invalid username/password | Incorrect credentials |
| 250003 | Invalid account | Wrong account identifier |
| 390201 | Warehouse does not exist | Incorrect warehouse name |
| 002003 | SQL compilation error | Invalid SQL or missing objects |

## Getting Help

### Self-Diagnosis Checklist

Before seeking help, run through this checklist:

- [ ] **Check available profiles**: `snow connection list`
- [ ] **Test profile connection**: `snow connection test --connection-name <profile>`
- [ ] **Verify environment variables**: `echo $SNOWFLAKE_PROFILE`
- [ ] **Check configuration file exists**: `ls "~/Library/Application Support/snowflake/config.toml"`
- [ ] **Test basic CLI functionality**: `nanuk query "SELECT CURRENT_VERSION()"`
- [ ] **Enable debug logging**: `export SNOWCLI_MCP_LOG_LEVEL=DEBUG`

### Information to Include When Reporting Issues

1. **Error message** (complete output)
2. **nanuk-mcp version**: `nanuk --version`
3. **Operating system** and version
4. **Profile configuration** (sanitized - remove sensitive data)
5. **Steps to reproduce** the issue
6. **Expected vs actual behavior**

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check latest documentation for updates
- **Snowflake Community**: General Snowflake CLI questions

## Conclusion

The enhanced profile validation in v1.4.4+ significantly improves the user experience by providing immediate, actionable feedback when configuration issues occur. The diagnostic tools and clear error messages make it much easier to identify and resolve problems quickly.

Remember that most issues are related to:
1. **Profile selection** - Make sure you're using an existing, valid profile
2. **Authentication** - Ensure credentials are correct and not expired
3. **Permissions** - Verify your role has necessary access to resources
4. **Network connectivity** - Check firewall and VPN settings

Following the troubleshooting steps in this guide should resolve the vast majority of profile-related issues.
