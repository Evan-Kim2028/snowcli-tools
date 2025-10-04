# Cortex Search Guide

**Semantic Search Over Your Snowflake Data**

## Overview

Cortex Search enables semantic search over text data in Snowflake. Unlike traditional keyword search, it understands meaning and context.

## Setup

### 1. Create Search Service

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE PRODUCT_FEEDBACK_SEARCH
ON feedback_text
ATTRIBUTES customer_name, product_name
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        feedback_text,
        customer_name,
        product_name,
        feedback_id
    FROM ANALYTICS.PUBLIC.PRODUCT_FEEDBACK
);
```

### 2. Query the Service

```python
from mcp_server_snowflake.cortex_services.tools import query_cortex_search

results = query_cortex_search(
    search_service="ANALYTICS.PUBLIC.PRODUCT_FEEDBACK_SEARCH",
    query="shipping delays",
    columns=["customer_name", "product_name", "feedback_text"],
    limit=10,
    snowflake_service=snowflake_service
)

for result in results:
    print(f"{result['product_name']}: {result['feedback_text']}")
```

## Common Use Cases

### Customer Support

```python
# Find similar support tickets
query_cortex_search(
    search_service="SUPPORT_TICKETS_SEARCH",
    query="cannot login to account",
    columns=["ticket_id", "issue_description", "resolution"],
    limit=5
)
```

### Product Research

```python
# Find product mentions
query_cortex_search(
    search_service="REVIEWS_SEARCH",
    query="battery life complaints",
    columns=["product_id", "review_text", "rating"],
    limit=20
)
```

## Best Practices

1. **Index relevant columns** - Only index searchable text
2. **Set appropriate lag** - Balance freshness vs cost
3. **Use filters** - Combine with WHERE clauses when possible
4. **Monitor costs** - Search operations consume credits

## See Also

- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
