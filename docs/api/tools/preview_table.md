# preview_table

Quick preview of table contents without writing SQL.

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `table_name` | string | ✅ Yes | - | Fully qualified table name |
| `limit` | integer | ❌ No | 100 | Row limit (1-10000) |
| `warehouse` | string | ❌ No | profile | Warehouse override |
| `database` | string | ❌ No | profile | Database override |
| `schema` | string | ❌ No | profile | Schema override |
| `role` | string | ❌ No | profile | Role override |

## Returns

```json
{
  "statement": "SELECT * FROM customers LIMIT 100",
  "rowcount": 100,
  "rows": [...]
}
```

## Examples

```python
# Simple preview
preview_table(table_name="customers", limit=10)

# With overrides
preview_table(
    table_name="analytics.prod.sales",
    limit=500,
    warehouse="LARGE_WH"
)
```

## Related

- [execute_query](execute_query.md) - For complex queries
