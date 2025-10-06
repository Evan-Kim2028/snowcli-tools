# get_catalog_summary

**Version:** 1.9.0+
**Category:** Catalog & Metadata

---

## Description

Retrieve summary information from an existing data catalog, providing quick statistics about cataloged objects without re-scanning the database. This tool reads the pre-generated `_catalog_metadata.json` file created by `build_catalog`.

**Use this tool when:**
- You need quick catalog statistics
- Want to check catalog status before running queries
- Need object counts for documentation or dashboards
- Verifying catalog build completion

---

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `catalog_dir` | string | ❌ No | "./data_catalogue" | Path to catalog directory |

---

## Returns

```json
{
  "catalog_dir": "./data_catalogue",
  "summary": {
    "build_date": "2025-10-06T10:30:45",
    "build_type": "incremental",
    "databases": ["ANALYTICS", "PROD_DB"],
    "totals": {
      "tables": 127,
      "views": 45,
      "materialized_views": 8,
      "dynamic_tables": 3,
      "functions": 156,
      "procedures": 23,
      "tasks": 12,
      "total_objects": 374
    },
    "size_bytes": 4563200,
    "version": "1.9.0"
  }
}
```

---

## Errors

### FileNotFoundError

```
FileNotFoundError: No catalog found in './data_catalogue'.
Run build_catalog first to generate the catalog.
```

**Solution:** Run `build_catalog` to generate the catalog before calling this tool.

### RuntimeError

```
RuntimeError: Failed to load catalog summary: Invalid JSON format
```

**Solution:** Catalog may be corrupted. Re-run `build_catalog` with `--force` flag.

---

## Examples

### Example 1: Check Default Catalog

```python
get_catalog_summary()
```

**Result:**
```json
{
  "catalog_dir": "./data_catalogue",
  "summary": {
    "build_date": "2025-10-06T10:30:45",
    "totals": {
      "tables": 127,
      "views": 45,
      "total_objects": 374
    }
  }
}
```

### Example 2: Custom Catalog Location

```python
get_catalog_summary(catalog_dir="/path/to/my_catalog")
```

### Example 3: AI Assistant Usage

```
User: "How many tables are in my catalog?"
AI: Let me check the catalog summary.
→ get_catalog_summary()
→ Returns: "Your catalog contains 127 tables, 45 views, and 374 total objects."
```

---

## Use Cases

### 1. Catalog Status Check
**Before running expensive queries, verify catalog exists**

```
AI: "Do we have a catalog built?"
→ get_catalog_summary()
→ Returns: Catalog exists with 374 objects or FileNotFoundError
```

### 2. Dashboard Reporting
**Populate data governance dashboards**

```
AI: "Give me object counts for the dashboard"
→ get_catalog_summary()
→ Returns: Structured statistics for visualization
```

### 3. Catalog Validation
**Verify catalog completeness after build**

```
AI: "Did the catalog build complete successfully?"
→ get_catalog_summary()
→ Returns: Build date and object counts
```

---

## Performance

- **Latency:** <50ms (reads single JSON file)
- **No Snowflake Queries:** Operates entirely on local cached data
- **Lightweight:** Suitable for frequent polling

---

## Related Tools

- **[build_catalog](build_catalog.md)** - Generate catalog (prerequisite)
- **[query_lineage](query_lineage.md)** - Query lineage (requires catalog)
- **[build_dependency_graph](build_dependency_graph.md)** - Build dependencies (requires catalog)

---

## See Also

- [Incremental Catalog Guide](../../incremental_catalog_guide.md) - Catalog building strategies
- [Workflows Guide](../../workflows.md) - Catalog workflows

---

**Last Updated:** 2025-10-06
**Version:** 1.9.0
