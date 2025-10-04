# Cortex Analyst Guide

**Natural Language to SQL with Semantic Models**

## Overview

Cortex Analyst enables you to query your Snowflake data using natural language. It translates business questions into SQL queries using semantic models that define your data structure and relationships.

## Quick Example

```python
from mcp_server_snowflake.cortex_services.tools import query_cortex_analyst

result = query_cortex_analyst(
    semantic_model="@ANALYTICS.MODELS.STAGE/sales_model.yaml",
    query="What were our top 5 products by revenue last quarter?",
    snowflake_service=snowflake_service
)

print(result)
# Returns: SQL query + results
```

## How It Works

1. **Define a semantic model** - YAML file describing your data
2. **Upload to Snowflake stage** - Store model in stage
3. **Query with natural language** - Analyst generates SQL
4. **Get structured results** - Returns SQL + data

## Creating Semantic Models

See [Creating Semantic Models](./semantic_models/creating_models.md) for detailed guide.

### Example Semantic Model

```yaml
name: sales_analytics
tables:
  - name: SALES
    description: "Sales transactions"
    base_table:
      database: ANALYTICS
      schema: PUBLIC
      table: SALES
    dimensions:
      - name: product_name
        description: "Product name"
        expr: PRODUCT_NAME
      - name: region
        description: "Sales region"
        expr: REGION
    measures:
      - name: revenue
        description: "Total revenue"
        expr: SUM(AMOUNT)
      - name: quantity
        description: "Units sold"
        expr: SUM(QUANTITY)
    filters:
      - name: last_quarter
        description: "Last quarter only"
        expr: SALE_DATE >= DATEADD(quarter, -1, CURRENT_DATE())
```

## Common Queries

### Business Metrics

```python
queries = [
    "Show me revenue by product category",
    "What's our month-over-month growth?",
    "Which regions had the highest sales?",
    "List customers with orders over $10,000",
]

for q in queries:
    result = query_cortex_analyst(semantic_model=model, query=q)
    print(f"Q: {q}\nSQL: {result['sql']}\n")
```

### Time-Based Analysis

```python
query_cortex_analyst(
    semantic_model=model,
    query="Compare revenue this quarter vs last quarter by region"
)
```

### Aggregations

```python
query_cortex_analyst(
    semantic_model=model,
    query="Show average order value by customer segment"
)
```

## Best Practices

1. **Keep models focused** - 5-10 tables maximum
2. **Use clear descriptions** - Helps Analyst understand intent
3. **Define relationships** - Link tables properly
4. **Add common filters** - Pre-define useful filters
5. **Test iteratively** - Refine model based on query results

## See Also

- [Creating Semantic Models](./semantic_models/creating_models.md)
- [Example Models](./semantic_models/examples/)
