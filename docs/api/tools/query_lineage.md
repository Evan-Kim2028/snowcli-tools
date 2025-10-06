# query_lineage

**Version:** 1.9.0+
**Category:** Analysis & Lineage

---

## Description

Query the cached lineage graph to trace data flow and dependencies between Snowflake objects. Analyze upstream sources (where data comes from) and downstream consumers (where data flows to) with configurable traversal depth.

**Key Features:**
- Bidirectional lineage traversal (upstream/downstream/both)
- Configurable depth (1-10 levels)
- Multiple output formats (text/JSON)
- Supports tables, views, materialized views, dynamic tables, and tasks
- Fast cached lookups (no re-parsing SQL)

**Prerequisites:**
- Catalog must be built first using `build_catalog`
- Lineage graph automatically generated from catalog SQL definitions

---

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `object_name` | string | ✅ Yes | - | Object name to analyze (e.g., DATABASE.SCHEMA.TABLE) |
| `direction` | string | ❌ No | "both" | Traversal direction: "upstream", "downstream", or "both" |
| `depth` | integer | ❌ No | 3 | Traversal depth (1-10 levels) |
| `format` | string | ❌ No | "text" | Output format: "text" or "json" |
| `catalog_dir` | string | ❌ No | "./data_catalogue" | Catalog directory path |
| `cache_dir` | string | ❌ No | "./lineage" | Lineage cache directory path |

---

## Returns

### Text Format

```json
{
  "object": "ANALYTICS.PUBLIC.CUSTOMER_ORDERS",
  "direction": "both",
  "depth": 3,
  "format": "text",
  "result": "
ANALYTICS.PUBLIC.CUSTOMER_ORDERS
├── Upstream (Sources)
│   ├── ANALYTICS.PUBLIC.CUSTOMERS
│   ├── ANALYTICS.PUBLIC.ORDERS
│   └── ANALYTICS.PUBLIC.ORDER_ITEMS
│       └── ANALYTICS.PUBLIC.PRODUCTS
└── Downstream (Consumers)
    ├── ANALYTICS.PUBLIC.DAILY_REVENUE
    └── ANALYTICS.PUBLIC.CUSTOMER_LIFETIME_VALUE
"
}
```

### JSON Format

```json
{
  "object": "ANALYTICS.PUBLIC.CUSTOMER_ORDERS",
  "direction": "both",
  "depth": 3,
  "format": "json",
  "result": {
    "nodes": [
      {
        "id": "ANALYTICS.PUBLIC.CUSTOMER_ORDERS",
        "type": "view",
        "database": "ANALYTICS",
        "schema": "PUBLIC",
        "name": "CUSTOMER_ORDERS"
      },
      ...
    ],
    "edges": [
      {
        "from": "ANALYTICS.PUBLIC.CUSTOMERS",
        "to": "ANALYTICS.PUBLIC.CUSTOMER_ORDERS",
        "type": "table_dependency"
      },
      ...
    ]
  }
}
```

---

## Errors

### ValueError: Object Not Found

```
ValueError: Object 'INVALID_TABLE' not found in lineage graph.
Ensure catalog has been built for this object.
```

**Solution:**
1. Verify object name spelling
2. Run `build_catalog` to include the object
3. Check database/schema qualifiers

### ValueError: Invalid Direction

```
ValueError: Invalid direction 'sideways'. Must be 'upstream', 'downstream', or 'both'
```

**Solution:** Use one of the three valid direction values.

### ValueError: Invalid Depth

```
ValueError: Depth must be between 1 and 10, got 15
```

**Solution:** Use depth between 1 and 10. For very deep graphs, use multiple queries.

### RuntimeError: Lineage Query Failed

```
RuntimeError: Lineage query failed: Catalog not found
```

**Solution:** Run `build_catalog` first to generate the catalog and lineage cache.

---

## Examples

### Example 1: Upstream Dependencies

**Find all tables that feed into a view**

```python
query_lineage(
    object_name="CUSTOMER_ORDERS",
    direction="upstream",
    depth=3
)
```

**Result:**
```
ANALYTICS.PUBLIC.CUSTOMER_ORDERS
└── Upstream Sources
    ├── ANALYTICS.PUBLIC.CUSTOMERS
    ├── ANALYTICS.PUBLIC.ORDERS
    └── ANALYTICS.PUBLIC.ORDER_ITEMS
        └── ANALYTICS.PUBLIC.PRODUCTS
```

### Example 2: Downstream Consumers

**Find all objects that depend on a table**

```python
query_lineage(
    object_name="CUSTOMERS",
    direction="downstream",
    depth=2
)
```

**Result:**
```
ANALYTICS.PUBLIC.CUSTOMERS
└── Downstream Consumers
    ├── ANALYTICS.PUBLIC.CUSTOMER_ORDERS
    ├── ANALYTICS.PUBLIC.CUSTOMER_SUMMARY
    └── ANALYTICS.PUBLIC.DAILY_REVENUE
```

### Example 3: Bidirectional (Full Context)

**Understand complete data flow**

```python
query_lineage(
    object_name="ORDER_ITEMS",
    direction="both",
    depth=2
)
```

**Result:**
```
ANALYTICS.PUBLIC.ORDER_ITEMS
├── Upstream Sources
│   ├── ANALYTICS.PUBLIC.PRODUCTS
│   └── ANALYTICS.PUBLIC.ORDERS
└── Downstream Consumers
    ├── ANALYTICS.PUBLIC.CUSTOMER_ORDERS
    └── ANALYTICS.PUBLIC.REVENUE_ANALYSIS
```

### Example 4: JSON Output (Programmatic)

**For automated analysis or visualization**

```python
query_lineage(
    object_name="CUSTOMER_ORDERS",
    direction="both",
    depth=3,
    format="json"
)
```

**Result:** Structured JSON with nodes and edges for graph processing.

### Example 5: Custom Catalog Location

```python
query_lineage(
    object_name="SALES_SUMMARY",
    direction="upstream",
    catalog_dir="/path/to/prod_catalog",
    cache_dir="/path/to/prod_lineage"
)
```

---

## Use Cases

### 1. Impact Analysis

**"What breaks if I change this table?"**

```
User: "What views depend on the ORDERS table?"
AI: Let me check the downstream lineage.
→ query_lineage(object_name="ORDERS", direction="downstream", depth=5)
→ Returns: All views, tables, and tasks that depend on ORDERS
```

### 2. Data Source Tracing

**"Where does this data come from?"**

```
User: "What tables feed the DAILY_REVENUE view?"
AI: I'll trace the upstream sources.
→ query_lineage(object_name="DAILY_REVENUE", direction="upstream", depth=3)
→ Returns: Complete source table lineage
```

### 3. Refactoring Planning

**"How deep is this dependency chain?"**

```
User: "Show me the full lineage for CUSTOMER_LIFETIME_VALUE"
AI: Analyzing complete data flow.
→ query_lineage(object_name="CUSTOMER_LIFETIME_VALUE", direction="both", depth=5)
→ Returns: Full upstream and downstream dependencies
```

### 4. Documentation Generation

**Automatic lineage documentation**

```
User: "Document the lineage for all reporting views"
AI: Generating lineage documentation.
→ query_lineage(object_name="REPORT_*", format="json")
→ Returns: Structured lineage for documentation systems
```

### 5. Data Governance

**"Which raw tables are used in this report?"**

```
User: "Trace the raw sources for the EXECUTIVE_DASHBOARD view"
AI: Finding all source tables.
→ query_lineage(object_name="EXECUTIVE_DASHBOARD", direction="upstream", depth=10)
→ Returns: Complete lineage back to raw data sources
```

---

## Direction Guide

| Direction | Use Case | Returns |
|-----------|----------|---------|
| **upstream** | Find data sources | Tables/views that THIS object reads from |
| **downstream** | Find data consumers | Tables/views that read from THIS object |
| **both** | Full context | Complete bidirectional lineage |

---

## Depth Strategy

| Depth | Use Case | Performance |
|-------|----------|-------------|
| **1-2** | Immediate dependencies | Fast (<100ms) |
| **3-5** | Typical analysis | Good (~500ms) |
| **6-8** | Deep impact analysis | Slower (~1-2s) |
| **9-10** | Complete lineage chains | Slowest (~3-5s) |

**Recommendation:** Start with depth=3, increase as needed.

---

## Performance Characteristics

### Lineage Cache
- **First Query:** Builds lineage graph from catalog (~2-5s)
- **Subsequent Queries:** Instant cache lookups (<100ms)
- **Cache Location:** `./lineage/` directory
- **Cache Invalidation:** Automatic when catalog rebuilt

### Query Performance
| Graph Size | Objects | Typical Query Time |
|------------|---------|-------------------|
| Small | <100 | <50ms |
| Medium | 100-1000 | 100-500ms |
| Large | 1000-10000 | 500ms-2s |
| Very Large | >10000 | 2-5s |

---

## Related Tools

- **[build_catalog](build_catalog.md)** - Generate catalog (prerequisite)
- **[build_dependency_graph](build_dependency_graph.md)** - Build complete dependency graph
- **[get_catalog_summary](get_catalog_summary.md)** - Check catalog status

---

## Troubleshooting

### Problem: Object Not Found

**Symptoms:** `ValueError: Object not found in lineage graph`

**Solutions:**
1. Verify object name: `SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'YOUR_TABLE'`
2. Rebuild catalog: `build_catalog(database="YOUR_DATABASE")`
3. Check fully-qualified name: Use `DATABASE.SCHEMA.TABLE` format

### Problem: Empty Results

**Symptoms:** No upstream or downstream objects returned

**Causes:**
- Object has no dependencies (e.g., base table)
- Object not included in catalog scope
- SQL parsing couldn't extract dependencies

**Solutions:**
1. Increase depth parameter
2. Try opposite direction (upstream vs downstream)
3. Rebuild catalog with broader scope

### Problem: Slow Queries

**Symptoms:** Lineage queries taking >5 seconds

**Solutions:**
1. Reduce depth parameter (start with 3)
2. Use more specific direction (upstream or downstream, not both)
3. Consider building dependency graph for better performance

---

## See Also

- [Advanced Lineage Guide](../../advanced_lineage_features.md) - Advanced lineage patterns
- [Workflows Guide](../../workflows.md) - Lineage analysis workflows
- [Architecture Guide](../../architecture.md) - Lineage system design

---

**Last Updated:** 2025-10-06
**Version:** 1.9.0
