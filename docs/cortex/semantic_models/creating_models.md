# Creating Semantic Models for Cortex Analyst

## Overview

Semantic models define the structure of your data for Cortex Analyst. They describe tables, columns, relationships, and business logic in YAML format.

## Basic Structure

```yaml
name: model_name
tables:
  - name: TABLE_NAME
    description: "Human-readable description"
    base_table:
      database: DATABASE_NAME
      schema: SCHEMA_NAME
      table: TABLE_NAME
    dimensions:
      - name: column_name
        description: "What this represents"
        expr: COLUMN_NAME
    measures:
      - name: metric_name
        description: "How to calculate this"
        expr: SUM(COLUMN_NAME)
```

## Complete Example

See [examples/sales_model.yaml](./examples/sales_model.yaml)

## Uploading Models

```sql
-- Create stage
CREATE STAGE IF NOT EXISTS ANALYTICS.MODELS.STAGE;

-- Upload model
PUT file:///path/to/model.yaml @ANALYTICS.MODELS.STAGE AUTO_COMPRESS=FALSE;

-- Verify
LIST @ANALYTICS.MODELS.STAGE;
```

## Best Practices

1. **Clear descriptions** - Help Analyst understand intent
2. **Logical grouping** - Group related tables
3. **Define relationships** - Explicitly link tables
4. **Common metrics** - Pre-define useful measures
5. **Useful filters** - Add frequently-used filters

## See Also

- [Example: Sales Model](./examples/sales_model.yaml)
- [Example: Analytics Model](./examples/analytics_model.yaml)
