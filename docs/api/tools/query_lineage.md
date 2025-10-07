# Tool: query_lineage

## Purpose

Analyzes data lineage for Snowflake objects, showing dependencies and relationships between tables, views, and other database objects.

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object_name` | string | Yes | Name of the object to analyze lineage for |
| `direction` | string | No | Direction of lineage analysis: "upstream", "downstream", or "both" (default: "both") |
| `depth` | integer | No | Maximum depth of lineage analysis (default: 3) |
| `format` | string | No | Output format: "json", "dot", or "text" (default: "json") |
| `catalog_dir` | string | No | Directory containing catalog data (default: "./data_catalogue") |
| `cache_dir` | string | No | Directory for caching lineage data (default: "./cache") |

## Returns

Returns a dictionary containing:
- `lineage`: Lineage data in the requested format
- `summary`: Text summary of lineage relationships
- `object_name`: The analyzed object name
- `direction`: The analysis direction
- `depth`: The analysis depth

## Examples

### Basic Lineage Analysis
```json
{
  "tool": "query_lineage",
  "arguments": {
    "object_name": "MY_DATABASE.MY_SCHEMA.MY_TABLE"
  }
}
```

**Expected Output**:
```json
{
  "lineage": {
    "upstream": [
      {
        "object": "SOURCE_TABLE",
        "type": "table",
        "relationship": "direct"
      }
    ],
    "downstream": [
      {
        "object": "TARGET_VIEW",
        "type": "view",
        "relationship": "direct"
      }
    ]
  },
  "summary": "MY_TABLE has 1 upstream dependency and 1 downstream dependency",
  "object_name": "MY_DATABASE.MY_SCHEMA.MY_TABLE",
  "direction": "both",
  "depth": 3
}
```

### Upstream-Only Analysis
```json
{
  "tool": "query_lineage",
  "arguments": {
    "object_name": "MY_TABLE",
    "direction": "upstream",
    "depth": 2
  }
}
```

### DOT Format Output
```json
{
  "tool": "query_lineage",
  "arguments": {
    "object_name": "MY_TABLE",
    "format": "dot"
  }
}
```

**Expected Output**:
```json
{
  "lineage": "digraph lineage {\n  \"SOURCE_TABLE\" -> \"MY_TABLE\";\n  \"MY_TABLE\" -> \"TARGET_VIEW\";\n}",
  "summary": "DOT format lineage graph",
  "object_name": "MY_TABLE",
  "direction": "both",
  "depth": 3
}
```

## Common Use Cases

### Impact Analysis
Use `direction: "downstream"` to see what objects depend on a table before making changes.

### Data Source Tracking
Use `direction: "upstream"` to trace data back to its original sources.

### Documentation Generation
Use `format: "dot"` to generate visual diagrams of data flow.

### Change Management
Analyze lineage before schema changes to understand potential impacts.

## Troubleshooting

### Object Not Found
**Error**: `Object 'MY_TABLE' not found`
**Solution**:
- Verify object name spelling
- Check object exists in catalog
- Ensure proper database.schema.object format

### No Lineage Data
**Error**: `No lineage data found`
**Solution**:
- Build catalog first using `build_catalog` tool
- Check if object has dependencies
- Verify lineage depth settings

### Performance Issues
**Error**: `Query timeout`
**Solution**:
- Reduce lineage depth
- Use specific direction instead of "both"
- Check Snowflake warehouse size

## Related Tools

- [build_catalog](build_catalog.md) - Build catalog before lineage analysis
- [get_catalog_summary](get_catalog_summary.md) - Check catalog status
- [build_dependency_graph](build_dependency_graph.md) - Visual dependency mapping
- [preview_table](preview_table.md) - Preview table structure

## Notes

- Lineage analysis requires a built catalog
- Performance depends on lineage depth and object complexity
- DOT format output can be rendered with Graphviz
- Lineage data is cached for performance
