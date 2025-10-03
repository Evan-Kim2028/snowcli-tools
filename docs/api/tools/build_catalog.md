# build_catalog

Build comprehensive metadata catalog for Snowflake databases.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `output_dir` | string | ❌ No | ./data_catalogue | Catalog output directory |
| `database` | string | ❌ No | all | Specific database to catalog |
| `account` | boolean | ❌ No | false | Include entire account |
| `format` | string | ❌ No | json | Output format (json/jsonl) |
| `include_ddl` | boolean | ❌ No | true | Include object DDL statements |

## Returns

```json
{
  "output_dir": "./data_catalogue",
  "totals": {
    "databases": 3,
    "schemas": 15,
    "tables": 142,
    "views": 38
  }
}
```

## Examples

```python
# Build catalog for specific database
build_catalog(
    database="ANALYTICS",
    include_ddl=True,
    format="jsonl"
)

# Build entire account catalog
build_catalog(
    account=True,
    output_dir="./full_catalog"
)
```

## Performance

- **Small database (< 50 tables):** 5-10 seconds
- **Medium database (50-500 tables):** 10-30 seconds
- **Large database (500+ tables):** 30-120 seconds

## Related

- [get_catalog_summary](get_catalog_summary.md) - Read catalog info
- [query_lineage](query_lineage.md) - Query dependencies
