# build_dependency_graph

**Version:** 1.9.0+
**Category:** Analysis & Dependencies

---

## Description

Build a complete object dependency graph from Snowflake metadata, mapping relationships between tables, views, materialized views, dynamic tables, tasks, procedures, and functions. The graph reveals the entire data architecture and cross-object dependencies.

**Key Features:**
- Maps all object relationships from Snowflake metadata
- Two output formats: JSON (programmatic) and DOT (visualization)
- Account-level or database/schema-level scoping
- Circular dependency detection
- Compatible with Graphviz for visual rendering

**Use Cases:**
- Visualize entire database architecture
- Detect circular dependencies
- Plan migrations or refactoring
- Generate architecture diagrams
- Understand cross-schema/database relationships

---

## Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `database` | string | ❌ No | null | Specific database to analyze (null = all databases) |
| `schema` | string | ❌ No | null | Specific schema to analyze (null = all schemas) |
| `account_scope` | boolean | ❌ No | true | Use ACCOUNT_USAGE for broader coverage |
| `format` | string | ❌ No | "json" | Output format: "json" or "dot" |

---

## Returns

### JSON Format

```json
{
  "format": "json",
  "nodes": [
    {
      "id": "ANALYTICS.PUBLIC.CUSTOMERS",
      "type": "table",
      "database": "ANALYTICS",
      "schema": "PUBLIC",
      "name": "CUSTOMERS",
      "metadata": {
        "row_count": 125430,
        "last_modified": "2025-10-01T15:30:00Z"
      }
    },
    ...
  ],
  "edges": [
    {
      "from": "ANALYTICS.PUBLIC.CUSTOMERS",
      "to": "ANALYTICS.PUBLIC.CUSTOMER_ORDERS",
      "type": "table_to_view",
      "relationship": "referenced_in"
    },
    ...
  ],
  "counts": {
    "nodes": 374,
    "edges": 892,
    "tables": 127,
    "views": 45,
    "materialized_views": 8,
    "procedures": 23,
    "functions": 156,
    "tasks": 12,
    "circular_dependencies": 2
  },
  "scope": {
    "database": null,
    "schema": null,
    "account_scope": true
  }
}
```

### DOT Format

```json
{
  "format": "dot",
  "content": "
digraph dependencies {
  node [shape=box];

  // Tables
  \"ANALYTICS.PUBLIC.CUSTOMERS\" [color=blue, shape=cylinder];
  \"ANALYTICS.PUBLIC.ORDERS\" [color=blue, shape=cylinder];

  // Views
  \"ANALYTICS.PUBLIC.CUSTOMER_ORDERS\" [color=green, shape=box];

  // Relationships
  \"ANALYTICS.PUBLIC.CUSTOMERS\" -> \"ANALYTICS.PUBLIC.CUSTOMER_ORDERS\";
  \"ANALYTICS.PUBLIC.ORDERS\" -> \"ANALYTICS.PUBLIC.CUSTOMER_ORDERS\";
}
",
  "node_count": 374,
  "edge_count": 892
}
```

---

## Errors

### ValueError: Invalid Format

```
ValueError: Invalid format 'xml'. Must be 'json' or 'dot'
```

**Solution:** Use `format="json"` or `format="dot"`

### RuntimeError: Graph Build Failed

```
RuntimeError: Dependency graph build failed: Access denied to ACCOUNT_USAGE
```

**Solution:**
- Ensure user has `USAGE` on `SNOWFLAKE.ACCOUNT_USAGE`
- Or use `account_scope=false` to limit to INFORMATION_SCHEMA

---

## Examples

### Example 1: Account-Wide Dependency Graph

**Map all objects across all databases**

```python
build_dependency_graph()
```

**Result:**
```json
{
  "format": "json",
  "counts": {
    "nodes": 1247,
    "edges": 3821,
    "tables": 412,
    "views": 198
  }
}
```

### Example 2: Single Database

**Focus on one database**

```python
build_dependency_graph(database="ANALYTICS")
```

**Result:**
```json
{
  "format": "json",
  "counts": {
    "nodes": 374,
    "edges": 892
  },
  "scope": {
    "database": "ANALYTICS",
    "schema": null
  }
}
```

### Example 3: Single Schema

**Narrow scope to specific schema**

```python
build_dependency_graph(
    database="ANALYTICS",
    schema="PUBLIC"
)
```

### Example 4: Graphviz Visualization

**Generate DOT format for Graphviz**

```python
build_dependency_graph(
    database="ANALYTICS",
    format="dot"
)
```

**Then render with Graphviz:**
```bash
# Save DOT content to file
echo "<dot_content>" > graph.dot

# Render as PNG
dot -Tpng graph.dot -o architecture.png

# Render as SVG (interactive)
dot -Tsvg graph.dot -o architecture.svg
```

### Example 5: Information Schema Only

**Skip ACCOUNT_USAGE for faster builds**

```python
build_dependency_graph(
    database="ANALYTICS",
    account_scope=False
)
```

**Trade-off:** Faster but may miss cross-database dependencies

---

## Use Cases

### 1. Architecture Visualization

**Generate diagrams for documentation**

```
User: "Create an architecture diagram for the ANALYTICS database"
AI: Building dependency graph for visualization.
→ build_dependency_graph(database="ANALYTICS", format="dot")
→ Returns: DOT graph for Graphviz rendering
```

### 2. Circular Dependency Detection

**Find problematic dependency cycles**

```
User: "Check for circular dependencies in PROD_DB"
AI: Analyzing dependency graph.
→ build_dependency_graph(database="PROD_DB")
→ Returns: Graph with circular_dependencies count
```

### 3. Migration Planning

**Understand dependencies before migration**

```
User: "Show me all dependencies for the REPORTING schema"
AI: Building complete dependency map.
→ build_dependency_graph(database="ANALYTICS", schema="REPORTING")
→ Returns: All objects and relationships in scope
```

### 4. Cross-Database Analysis

**Map relationships across databases**

```
User: "How are ANALYTICS and PROD_DB related?"
AI: Building account-wide dependency graph.
→ build_dependency_graph(account_scope=True)
→ Returns: Cross-database dependencies revealed
```

### 5. Refactoring Impact

**Before making schema changes**

```
User: "What's affected if I change the CUSTOMERS table structure?"
AI: Building dependency graph for impact analysis.
→ build_dependency_graph(database="ANALYTICS")
→ Then: query_lineage(object_name="CUSTOMERS", direction="downstream")
```

---

## Output Format Comparison

| Aspect | JSON | DOT |
|--------|------|-----|
| **Best For** | Programmatic analysis | Visualization |
| **Size** | Larger (detailed) | Smaller (graph structure only) |
| **Processing** | Parse with JSON libraries | Render with Graphviz |
| **Human Readable** | Medium | High (when rendered) |
| **Integration** | APIs, dashboards | Documentation, reports |

---

## Scope Strategy

| Scope | Use Case | Build Time | Graph Size |
|-------|----------|------------|------------|
| **Account-wide** | Complete architecture | Slowest (5-30min) | Largest |
| **Database-level** | Single database analysis | Medium (1-5min) | Medium |
| **Schema-level** | Focused analysis | Fast (10-60s) | Small |

**Recommendation:** Start narrow (schema), expand as needed.

---

## Graph Types

### Node Types
- **Tables**: Base storage objects (blue in DOT)
- **Views**: Virtual tables (green in DOT)
- **Materialized Views**: Cached query results (green in DOT)
- **Dynamic Tables**: Auto-updating tables (orange in DOT)
- **Tasks**: Scheduled procedures (yellow in DOT)
- **Procedures**: Stored procedures (purple in DOT)
- **Functions**: User-defined functions (purple in DOT)

### Edge Types
- **table_to_view**: Table referenced by view
- **view_to_view**: View builds on other views
- **table_to_task**: Task operates on table
- **procedure_calls**: Procedure invokes another

---

## Performance Characteristics

### Build Time
| Scope | Objects | ACCOUNT_USAGE | INFORMATION_SCHEMA |
|-------|---------|---------------|-------------------|
| Small (<100) | 10-30s | 5-10s |
| Medium (100-1000) | 1-5min | 30s-2min |
| Large (1000-10000) | 5-15min | 2-5min |
| Very Large (>10000) | 15-60min | 5-15min |

### Resource Usage
- **Memory**: ~1MB per 1000 objects
- **Network**: Metadata queries only (no data transfer)
- **Snowflake Credits**: Minimal (INFORMATION_SCHEMA queries)

---

## Visualization with Graphviz

### Install Graphviz

```bash
# macOS
brew install graphviz

# Ubuntu/Debian
apt-get install graphviz

# Windows
choco install graphviz
```

### Render Graph

```bash
# PNG (static image)
dot -Tpng graph.dot -o architecture.png

# SVG (scalable, interactive)
dot -Tsvg graph.dot -o architecture.svg

# PDF (printable)
dot -Tpdf graph.dot -o architecture.pdf

# Interactive HTML (with pan/zoom)
dot -Tsvg graph.dot | svg2html > architecture.html
```

### Layout Algorithms

```bash
# Hierarchical (default, good for DAGs)
dot -Tpng graph.dot -o hier.png

# Force-directed (circular layout)
neato -Tpng graph.dot -o circular.png

# Radial (tree-like)
twopi -Tpng graph.dot -o radial.png
```

---

## Related Tools

- **[query_lineage](query_lineage.md)** - Query specific object lineage (faster)
- **[build_catalog](build_catalog.md)** - Generate metadata catalog (prerequisite for lineage)
- **[get_catalog_summary](get_catalog_summary.md)** - Check catalog status

---

## Troubleshooting

### Problem: Build Taking Too Long

**Symptoms:** Graph build running for >15 minutes

**Solutions:**
1. Narrow scope: `build_dependency_graph(database="SPECIFIC_DB")`
2. Use INFORMATION_SCHEMA: `account_scope=False`
3. Run during off-hours to avoid contention

### Problem: Missing Dependencies

**Symptoms:** Expected relationships not showing in graph

**Causes:**
- Cross-database references require `account_scope=True`
- Dynamic SQL dependencies not detected
- External references (stages, etc.) not included

**Solutions:**
1. Enable account scope: `account_scope=True`
2. Verify objects exist in metadata: `SHOW OBJECTS`
3. Check SQL definitions manually for complex cases

### Problem: Access Denied

**Symptoms:** `RuntimeError: Access denied to ACCOUNT_USAGE`

**Solutions:**
1. Request `USAGE` on `SNOWFLAKE.ACCOUNT_USAGE` schema
2. Use `account_scope=False` to limit to INFORMATION_SCHEMA
3. Verify role has sufficient privileges

---

## See Also

- [Architecture Guide](../../architecture.md) - System design patterns
- [Workflows Guide](../../workflows.md) - Dependency analysis workflows
- [Graphviz Documentation](https://graphviz.org/documentation/) - Graph visualization

---

**Last Updated:** 2025-10-06
**Version:** 1.9.0
