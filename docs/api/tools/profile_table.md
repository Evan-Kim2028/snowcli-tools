# profile_table

**Version:** 1.10.0 (Renamed from `discover_table_purpose`)
**Category:** Discovery & Documentation

---

## Description

Automatically profile Snowflake tables with SQL-based analysis, providing comprehensive schema documentation, column statistics, and optional AI-powered insights. This is the flagship discovery tool for understanding unfamiliar tables and generating data catalog documentation.

**Key Features:**
- **Fast SQL Profiling**: Column types, cardinality, null rates, sample values (~2-5s, $0.01)
- **Optional AI Analysis**: Business context inference, PII detection via Cortex Complete (~15-20s, $0.05)
- **Optional Relationship Discovery**: Foreign key inference via name patterns and value overlap (~25-30s, $0.08)
- **Automatic Caching**: LRU cache with DDL-based invalidation (1-hour TTL)
- **Batch Processing**: Profile multiple tables in a single operation

**Important Note:**
This tool profiles **Snowflake TABLE STRUCTURES** (schema, statistics, samples), NOT business entities or packages. Use this to understand what columns exist in a database table.

---

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `table_name` | string or array | ✅ Yes | - | Table name or list of tables. Supports fully-qualified names (DB.SCHEMA.TABLE) |
| `database` | string | ❌ No | session default | Database name override |
| `schema` | string | ❌ No | session default | Schema name override |
| `include_ai_analysis` | boolean | ❌ No | true | Use AI to infer business context and column meanings |
| `include_relationships` | boolean | ❌ No | false | Discover foreign key relationships (adds ~$0.03, ~10s) |
| `output_format` | string | ❌ No | "markdown" | Output format: "markdown" or "json" |
| `timeout_seconds` | integer | ❌ No | 60 | Maximum execution time (5-600 seconds) |
| `force_refresh` | boolean | ❌ No | false | Bypass cache and force fresh analysis |

---

## Returns

### Success Response

```json
{
  "success": true,
  "documentation": "# CUSTOMERS Table\n\n## Overview\n...",
  "cache_hit": false,
  "table_name": "CUSTOMERS",
  "execution_time_ms": 3450,
  "estimated_cost_usd": 0.05,
  "confidence_level": "high",
  "components_run": ["profiler", "llm_analyzer"]
}
```

### Batch Response

```json
{
  "success": true,
  "documentation": "Combined documentation for all tables...",
  "batch_summary": {
    "total": 3,
    "successful": 3,
    "failed": 0
  },
  "results": [...]
}
```

### Error Response

```json
{
  "success": false,
  "documentation": "# Error: Table Not Found\n\n...",
  "error": "Table 'INVALID_TABLE' not found",
  "table_name": "INVALID_TABLE"
}
```

---

## Cost Model

| Configuration | Cost | Time | Use Case |
|---------------|------|------|----------|
| **SQL Only** (default) | ~$0.01 | 2-5s | Fast schema inspection |
| **+ AI Analysis** (include_ai_analysis=true) | ~$0.05 | 15-20s | Business context, PII detection |
| **+ Relationships** (include_relationships=true) | ~$0.08 | 25-30s | Full schema understanding |

**Cost Limits:**
- Maximum cost per table: $1.00
- Maximum batch size: 50 tables
- Wide tables (>100 columns) may cost more

---

## Examples

### Example 1: Basic Table Profiling

**Quick schema inspection without AI analysis**

```python
# MCP Tool Call
profile_table(
    table_name="CUSTOMERS"
)
```

**Result:**
```markdown
# CUSTOMERS Table

## Schema
| Column | Type | Nulls | Unique Values |
|--------|------|-------|---------------|
| customer_id | NUMBER | 0% | 125,430 |
| email | VARCHAR | 0.2% | 125,180 |
| name | VARCHAR | 0% | 98,234 |
| created_at | TIMESTAMP | 0% | 89,123 |
| status | VARCHAR | 0% | 5 |

## Sample Data
[Shows 10 sample rows]

## Statistics
- Total Rows: 125,430
- Last Modified: 2025-10-01 15:30:00
```

### Example 2: AI-Powered Analysis

**Include business context and PII detection**

```python
profile_table(
    table_name="CUSTOMERS",
    include_ai_analysis=True
)
```

**Additional AI Output:**
```markdown
## Business Purpose
Customer master data with contact information and account status tracking.

## PII Analysis
- email (CONFIRMED - Email addresses)
- name (LIKELY - Personal names)
- phone (CONFIRMED - Phone numbers)

## Column Insights
- customer_id: Unique identifier, likely primary key
- email: Contact information, contains PII
- status: Categorical field with 5 distinct values (active, inactive, etc.)
```

### Example 3: Full Discovery with Relationships

**Complete schema understanding for data modeling**

```python
profile_table(
    table_name="ORDERS",
    include_ai_analysis=True,
    include_relationships=True
)
```

**Additional Relationship Output:**
```markdown
## Relationships

### Foreign Keys (Inferred)
- customer_id → CUSTOMERS.customer_id (confidence: HIGH)
  - Name match: ✓
  - Value overlap: 98.5%

- product_id → PRODUCTS.product_id (confidence: HIGH)
  - Name match: ✓
  - Value overlap: 95.2%
```

### Example 4: Batch Profiling

**Profile multiple tables in one operation**

```python
profile_table(
    table_name=["CUSTOMERS", "ORDERS", "PRODUCTS"],
    include_ai_analysis=False,  # Faster for batch
    output_format="json"
)
```

**Result:**
```json
{
  "success": true,
  "batch_summary": {
    "total": 3,
    "successful": 3,
    "failed": 0
  },
  "results": [
    {"table_name": "CUSTOMERS", "success": true, ...},
    {"table_name": "ORDERS", "success": true, ...},
    {"table_name": "PRODUCTS", "success": true, ...}
  ]
}
```

### Example 5: Cached Result

**Subsequent requests hit cache (if DDL unchanged)**

```python
profile_table(
    table_name="CUSTOMERS"
)
```

**Result:**
```json
{
  "success": true,
  "documentation": "[cached documentation]",
  "cache_hit": true,
  "execution_time_ms": 0,
  "estimated_cost_usd": 0.0
}
```

### Example 6: Force Refresh

**Bypass cache for debugging or stale metadata**

```python
profile_table(
    table_name="CUSTOMERS",
    force_refresh=True
)
```

---

## Use Cases

### 1. Database Onboarding
**Scenario:** New team member needs to understand unfamiliar database

```
AI: "Profile all tables in the ANALYTICS schema"
→ profile_table(table_name=["TABLE1", "TABLE2", ...])
→ Returns: Complete schema documentation for quick orientation
```

### 2. PII Detection & Compliance
**Scenario:** Identify tables containing personally identifiable information

```
AI: "Find all PII in the CUSTOMERS table"
→ profile_table(table_name="CUSTOMERS", include_ai_analysis=True)
→ Returns: PII columns identified with confidence levels
```

### 3. Data Catalog Generation
**Scenario:** Automate documentation for data governance

```
AI: "Document all tables in PROD_DB for our data catalog"
→ profile_table(table_name=[list_of_tables], output_format="json")
→ Returns: Structured JSON for catalog ingestion
```

### 4. Impact Analysis Preparation
**Scenario:** Understand table dependencies before schema changes

```
AI: "Show me relationships for the ORDERS table"
→ profile_table(table_name="ORDERS", include_relationships=True)
→ Returns: Foreign key relationships for impact assessment
```

### 5. Quick Schema Inspection
**Scenario:** Fast lookup during development

```
AI: "What columns are in the USER_ACTIVITY table?"
→ profile_table(table_name="USER_ACTIVITY", include_ai_analysis=False)
→ Returns: Schema and stats in <5 seconds
```

---

## Caching Behavior

### Cache Strategy
- **Cache Key**: `(table_name, include_relationships, include_ai_analysis)`
- **TTL**: 1 hour
- **Invalidation**: Automatic if DDL timestamp changes
- **LRU Eviction**: Oldest entries removed when cache reaches 100 items

### Cache Performance
- **Cache Hit**: <100ms latency
- **Cache Miss**: Full profiling time (2-30s depending on options)

### Force Refresh
Use `force_refresh=True` when:
- Debugging cache issues
- Table metadata is stale
- Need guaranteed fresh results

---

## Error Handling

### ValueError: Invalid Parameters

```
ValueError: timeout_seconds must be between 5 and 600, got 700
```
**Solution:** Use valid timeout range (5-600 seconds)

### ValueError: Table Not Found

```
Table 'INVALID_TABLE' not found in database
```
**Solution:** Verify table name, database, and schema. Check permissions.

### ValueError: Batch Size Exceeded

```
Batch size limited to 50 tables, got 75
```
**Solution:** Split batch into multiple requests

### ValueError: Cost Limit Exceeded

```
Estimated cost $1.25 exceeds maximum $1.00. Table has 250 columns.
```
**Solution:** Use `include_ai_analysis=False` or `include_relationships=False`

### RuntimeError: Query Timeout

```
Query timeout after 60s
```
**Solution:** Increase `timeout_seconds` for large tables (e.g., 120-300s)

---

## Performance Tips

### 1. Optimize for Speed
```python
# Fastest: SQL profiling only
profile_table(table_name="LARGE_TABLE", include_ai_analysis=False)
```

### 2. Batch Without AI
```python
# For batch operations, skip AI to reduce cost/time
profile_table(
    table_name=["TABLE1", "TABLE2", "TABLE3"],
    include_ai_analysis=False
)
```

### 3. Cache Warming
```python
# Profile frequently-used tables during off-hours
profile_table(table_name="CRITICAL_TABLE")
# Future requests hit cache
```

### 4. Large Tables
```python
# Increase timeout for tables with >100 columns
profile_table(
    table_name="WIDE_TABLE",
    timeout_seconds=120
)
```

---

## Related Tools

- **[build_catalog](build_catalog.md)** - Extract metadata for entire database
- **[get_catalog_summary](get_catalog_summary.md)** - Get catalog statistics
- **[query_lineage](query_lineage.md)** - Trace data flow for profiled tables
- **[build_dependency_graph](build_dependency_graph.md)** - Map table relationships

---

## Migration from v1.9.0

### Tool Renamed
```python
# OLD (v1.9.0 and earlier)
discover_table_purpose(table_name="CUSTOMERS")

# NEW (v1.10.0+)
profile_table(table_name="CUSTOMERS")
```

### Simplified Parameters
```python
# OLD: depth parameter
discover_table_purpose(table_name="CUSTOMERS", depth="deep")

# NEW: Boolean flags
profile_table(
    table_name="CUSTOMERS",
    include_ai_analysis=True,
    include_relationships=True
)
```

### Parameter Mapping
| Old (v1.9.0) | New (v1.10.0) |
|--------------|---------------|
| `depth="quick"` | `include_ai_analysis=False, include_relationships=False` |
| `depth="standard"` | `include_ai_analysis=True, include_relationships=False` (default) |
| `depth="deep"` | `include_ai_analysis=True, include_relationships=True` |

---

## Version History

### v1.10.0 (Current)
- ✅ Tool renamed: `discover_table_purpose` → `profile_table`
- ✅ Simplified parameters: Boolean flags replace depth enum
- ✅ Automatic caching with DDL-based invalidation
- ✅ 40% reduction in MCP token usage

### v1.9.0
- Initial release as `discover_table_purpose`
- SQL-based profiling
- Cortex Complete AI analysis
- Relationship discovery

---

## See Also

- [MCP Quick Start Guide](../../mcp_quick_start.md) - Setup instructions
- [Security Guide](../../security.md) - Read-only defaults, SQL injection protection
- [Workflows Guide](../../workflows.md) - End-to-end examples
- [Troubleshooting Guide](../../troubleshooting.md) - Common issues

---

**Last Updated:** 2025-10-06
**Version:** 1.10.0
