# Security Guide
**Version:** 1.10.0
**Last Updated:** 2025-10-06

---

## Overview

SnowCLI Tools is designed with security-first principles, providing safe AI-assisted Snowflake operations through read-only defaults, SQL injection protection, and query timeout controls.

**Core Security Principles:**
1. **Read-Only by Default** - No destructive operations without explicit override
2. **SQL Injection Protection** - Input validation and safe query parsing
3. **Query Timeouts** - Automatic execution limits
4. **Official Authentication** - Built on Snowflake CLI profiles
5. **Least Privilege** - Minimal permissions required

---

## Read-Only by Default

### Blocked Operations

By default, SnowCLI Tools blocks all destructive SQL operations:

| Operation | Blocked | Reason |
|-----------|---------|--------|
| `DROP` | ✅ Yes | Deletes objects |
| `DELETE` | ✅ Yes | Removes data |
| `TRUNCATE` | ✅ Yes | Clears tables |
| `ALTER` | ✅ Yes | Modifies schema |
| `CREATE` | ✅ Yes | Creates objects |
| `UPDATE` | ✅ Yes | Modifies data |
| `MERGE` | ✅ Yes | Modifies data |
| `INSERT` | ✅ Yes | Adds data |

### Allowed Operations

Safe operations that don't modify data or schema:

| Operation | Allowed | Use Case |
|-----------|---------|----------|
| `SELECT` | ✅ Yes | Query data |
| `SHOW` | ✅ Yes | List objects |
| `DESCRIBE` | ✅ Yes | Inspect schema |
| `EXPLAIN` | ✅ Yes | Analyze queries |
| `WITH` (CTE) | ✅ Yes | Query logic |

### How It Works

```python
# User: "Delete old records from CUSTOMERS"
# AI Assistant attempts: execute_query("DELETE FROM CUSTOMERS WHERE ...")

# Result: BLOCKED
{
  "error": "SQL statement type 'Delete' is not permitted.",
  "alternatives": [
    "soft_delete: UPDATE customers SET deleted_at = CURRENT_TIMESTAMP()",
    "archive: INSERT INTO customers_archive SELECT * FROM customers WHERE ..."
  ]
}
```

### Override for Advanced Users

**Not recommended in production. Use with caution.**

If write operations are absolutely required, contact your system administrator to configure write access (this is not exposed through standard MCP tools).

---

## SQL Injection Protection

### Protection Mechanisms

1. **sqlglot Parsing** - All SQL statements parsed and validated
2. **Input Validation** - Parameters sanitized before execution
3. **Parameterized Queries** - No string concatenation
4. **Pattern Detection** - Suspicious patterns flagged

### Blocked Injection Attempts

```python
# Example 1: SQL Injection via Comment
execute_query("SELECT * FROM users WHERE id = 1; --")
# Result: BLOCKED - Detected SQL injection attempt

# Example 2: Union-Based Injection
execute_query("SELECT * FROM products WHERE id = 1 UNION SELECT * FROM passwords")
# Result: BLOCKED - Detected SQL injection pattern

# Example 3: Stacked Queries
execute_query("SELECT * FROM orders; DROP TABLE customers")
# Result: BLOCKED - Multiple statements not allowed
```

### Safe Query Patterns

```python
# SAFE: Parameterized WHERE clause
execute_query("SELECT * FROM customers WHERE status = 'active'")

# SAFE: Aggregate queries
execute_query("SELECT COUNT(*), AVG(amount) FROM orders WHERE date >= '2025-01-01'")

# SAFE: Complex JOINs
execute_query("""
SELECT c.name, COUNT(o.id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.name
""")
```

### Validation Process

```
User Input
    ↓
Input Sanitization
    ↓
sqlglot Parsing
    ↓
Operation Type Check (SELECT/SHOW/DESCRIBE only)
    ↓
Injection Pattern Detection
    ↓
Parameter Validation
    ↓
Safe Execution
```

---

## Query Timeout Controls

### Default Timeouts

| Tool | Default Timeout | Max Timeout | Configurable |
|------|----------------|-------------|--------------|
| `execute_query` | 120s | 3600s (1 hour) | ✅ Yes |
| `profile_table` | 60s | 600s (10 min) | ✅ Yes |
| `build_catalog` | None | None | ❌ No |
| `query_lineage` | None | None | ❌ No |

### Configuring Timeouts

```python
# Example 1: Short timeout for quick queries
execute_query(
    statement="SELECT COUNT(*) FROM orders",
    timeout_seconds=30
)

# Example 2: Long timeout for complex analytics
execute_query(
    statement="SELECT ... FROM large_table ...",
    timeout_seconds=600  # 10 minutes
)

# Example 3: Table profiling timeout
profile_table(
    table_name="WIDE_TABLE",  # 200+ columns
    timeout_seconds=120
)
```

### Timeout Behavior

**When timeout occurs:**
1. Query execution immediately canceled
2. Partial results discarded
3. Clear error message returned
4. Snowflake resources released

**Timeout Error Example:**
```json
{
  "error": "Query timeout after 120s",
  "recommendations": [
    "Increase timeout: execute_query(..., timeout_seconds=300)",
    "Add WHERE clause to reduce data volume",
    "Use LIMIT clause for testing",
    "Consider using a larger warehouse"
  ],
  "query_preview": "SELECT * FROM huge_table WHERE..."
}
```

---

## Authentication & Credentials

### How Authentication Works

```
AI Assistant
    ↓
MCP Server (SnowCLI Tools)
    ↓
Snowflake CLI Profiles (~/.snowflake/config.toml)
    ↓
Snowflake Authentication (Key-Pair/OAuth/SSO)
    ↓
Snowflake Data Cloud
```

### Supported Authentication Methods

| Method | Security Level | Setup Complexity | Recommended For |
|--------|---------------|------------------|-----------------|
| **Key-Pair** | High | Medium | Production |
| **OAuth/SSO** | High | Low | Enterprise |
| **External Browser** | High | Low | Development |
| **Password** | Medium | Low | Testing only |

### Key-Pair Authentication (Recommended)

**Why Key-Pair?**
- No password storage
- No credential exposure
- Automatic key rotation support
- Enterprise-grade security

**Setup:**
```bash
# 1. Generate key pair
ssh-keygen -t rsa -b 4096 -m PEM -f ~/.ssh/snowflake_key

# 2. Add public key to Snowflake user
# (In Snowflake UI: User Settings → Public Keys → Add)

# 3. Create profile
snow connection add \
  --connection-name "prod-profile" \
  --account "myorg-myaccount" \
  --user "analyst" \
  --private-key-file "~/.ssh/snowflake_key" \
  --database "ANALYTICS" \
  --warehouse "COMPUTE_WH"
```

### Credential Security Best Practices

**DO:**
- ✅ Use key-pair authentication for production
- ✅ Rotate keys regularly (every 90 days)
- ✅ Store private keys securely (encrypted filesystem)
- ✅ Use separate profiles for dev/prod environments
- ✅ Set minimal permissions (USAGE + SELECT only)

**DON'T:**
- ❌ Store passwords in plain text
- ❌ Share profiles between users
- ❌ Commit credentials to version control
- ❌ Use production credentials in development
- ❌ Grant unnecessary privileges

---

## Permission Requirements

### Minimum Permissions (Read-Only)

For safe, read-only operations:

```sql
-- Warehouse access
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE analyst_role;

-- Database access
GRANT USAGE ON DATABASE ANALYTICS TO ROLE analyst_role;

-- Schema access
GRANT USAGE ON SCHEMA ANALYTICS.PUBLIC TO ROLE analyst_role;

-- Metadata access
GRANT SELECT ON ALL TABLES IN SCHEMA INFORMATION_SCHEMA TO ROLE analyst_role;

-- Data access (for specific tables)
GRANT SELECT ON ANALYTICS.PUBLIC.CUSTOMERS TO ROLE analyst_role;
GRANT SELECT ON ANALYTICS.PUBLIC.ORDERS TO ROLE analyst_role;
```

### Optional: Cortex Complete Access

For AI-powered `profile_table` analysis:

```sql
-- Grant Cortex Complete usage
GRANT USAGE ON FUNCTION SNOWFLAKE.CORTEX.COMPLETE TO ROLE analyst_role;
```

**Cost:** ~$0.04 per table profiled with AI analysis

### Permission Validation

Before operations, verify permissions:

```python
# Test connection and permissions
test_connection()

# Expected output:
{
  "status": "connected",
  "profile": "analyst-profile",
  "permissions": {
    "warehouse": "COMPUTE_WH",
    "database": "ANALYTICS",
    "schema": "PUBLIC",
    "role": "analyst_role"
  }
}
```

---

## Threat Model

### Protected Against

| Threat | Protection | Effectiveness |
|--------|------------|---------------|
| **SQL Injection** | sqlglot parsing + validation | High |
| **Destructive Operations** | Read-only mode | High |
| **Runaway Queries** | Timeout controls | High |
| **Credential Exposure** | Profile-based auth | High |
| **Privilege Escalation** | Snowflake RBAC | High |

### Not Protected Against

| Threat | Mitigation | Responsibility |
|--------|-----------|----------------|
| **Data Exfiltration via SELECT** | Row-level security | Snowflake Admin |
| **Excessive Compute Usage** | Warehouse limits | Snowflake Admin |
| **Profile Misconfiguration** | Validation checks | User |
| **Social Engineering** | User training | Organization |

### Security Assumptions

1. **Snowflake accounts are properly secured** (MFA enabled, roles configured)
2. **Private keys are stored securely** (encrypted filesystem, key management)
3. **Users follow least privilege principle** (only necessary permissions granted)
4. **Network security is in place** (VPN, firewall rules)

---

## Compliance Considerations

### PII Handling

**`profile_table` Tool:**
- Detects PII columns automatically
- Does NOT extract or store actual PII values
- Uses statistical sampling only
- AI analysis operates on metadata, not data

**Data Sampling:**
- Limited to 10 rows per table
- Sample data never cached
- Used only for schema inference

### Data Residency

- **No data leaves Snowflake** - All processing in-database
- **Metadata cached locally** - Schema info, not actual data
- **Cortex Complete** - Runs within Snowflake (same region)

### Audit Trail

All operations logged by Snowflake:

```sql
-- Query audit trail
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE USER_NAME = 'analyst'
ORDER BY START_TIME DESC
LIMIT 100;
```

---

## Security Checklist

### Deployment Checklist

- [ ] Key-pair authentication configured (not password)
- [ ] Private keys stored securely (encrypted)
- [ ] Minimum permissions granted (USAGE + SELECT only)
- [ ] Separate dev/prod profiles configured
- [ ] MFA enabled on Snowflake account
- [ ] Query timeout limits set appropriately
- [ ] Profile validation tested successfully
- [ ] Audit logging enabled in Snowflake

### Ongoing Security

- [ ] Review query history monthly
- [ ] Rotate keys every 90 days
- [ ] Audit permissions quarterly
- [ ] Update SnowCLI Tools regularly
- [ ] Monitor for suspicious activity
- [ ] Test disaster recovery procedures

---

## Reporting Security Issues

**Found a security vulnerability?**

**DO NOT** file a public GitHub issue.

**Instead:**
1. Email: security@[project-domain].com
2. Include: Detailed description, steps to reproduce
3. Wait for acknowledgment (24-48 hours)
4. Coordinate disclosure timeline

**Responsible Disclosure:**
- Report privately first
- Allow time for fix (typically 90 days)
- Coordinate public disclosure

---

## See Also

- **[MCP Quick Start](mcp_quick_start.md)** - Secure setup guide
- **[Troubleshooting](troubleshooting.md)** - Permission issues
- **[execute_query](api/tools/execute_query.md)** - SQL safety features
- **[Snowflake Security Best Practices](https://docs.snowflake.com/en/user-guide/security)** - Official docs

---

**Last Updated:** 2025-10-06
**Version:** 1.10.0
**Security Contact:** Via GitHub Issues (for non-sensitive questions)
