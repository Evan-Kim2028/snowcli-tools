# Snowflake Cortex AI Integration

**Version**: v1.9.0+  
**Status**: Available via upstream `snowflake-labs-mcp`

## Overview

nanuk-mcp provides full access to Snowflake Cortex AI services through its integration with the upstream `snowflake-labs-mcp` package (v1.3.3+). These services enable natural language querying, semantic search, and LLM-powered completions directly against your Snowflake data.

### Available Cortex Services

1. **[Cortex Analyst](./analyst_guide.md)** - Natural language to SQL generation
2. **[Cortex Search](./search_guide.md)** - Semantic search over data
3. **[Cortex Complete](./completion_guide.md)** - LLM-powered text generation

All services are provided by the upstream `snowflake-labs-mcp` package and are available automatically when using nanuk-mcp.

## Quick Start

### Prerequisites

- Snowflake account with Cortex AI enabled
- nanuk-mcp v1.9.0+
- Appropriate Snowflake privileges for Cortex services

### Installation

Cortex services are included by default:

```bash
# nanuk-mcp automatically includes snowflake-labs-mcp
pip install nanuk-mcp

# Or with uv
uv pip install nanuk-mcp
```

### Basic Usage

#### Cortex Analyst - Natural Language Queries

```python
# Natural language to SQL
result = query_cortex_analyst(
    semantic_model="@DB.SCHEMA.STAGE/model.yaml",
    query="Show me top 10 customers by revenue this quarter"
)

print(result)
```

#### Cortex Search - Semantic Search

```python
# Semantic search over data
results = query_cortex_search(
    search_service="DB.SCHEMA.PRODUCT_SEARCH",
    query="customer complaints about shipping",
    columns=["product_name", "feedback_text"],
    limit=20
)

for result in results:
    print(f"{result['product_name']}: {result['feedback_text']}")
```

#### Cortex Complete - LLM Completions

```python
# LLM-powered completions
response = complete_cortex(
    model="mistral-large",
    prompt="Summarize this sales data: [data]",
    max_tokens=512
)

print(response)
```

## Documentation Structure

- **[analyst_guide.md](./analyst_guide.md)** - Natural language query guide with semantic models
- **[search_guide.md](./search_guide.md)** - Semantic search setup and usage
- **[completion_guide.md](./completion_guide.md)** - LLM completion examples
- **[semantic_models/](./semantic_models/)** - Creating and using semantic models

## Upstream Integration

nanuk-mcp leverages Cortex services from the official `snowflake-labs-mcp` package:

- **Package**: `snowflake-labs-mcp>=1.3.3`
- **Repository**: [Snowflake Labs MCP](https://github.com/Snowflake-Labs/snowflake-mcp)
- **Documentation**: [Snowflake Cortex Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex)

### What nanuk-mcp Adds

While Cortex services come from upstream, nanuk-mcp provides:

1. **Integrated Configuration** - Unified config with Snowflake connection
2. **Health Monitoring** - Cortex availability checking in `health_check` tool
3. **Comprehensive Documentation** - Guides and examples specific to nanuk-mcp usage
4. **Error Handling** - Consistent error responses across all MCP tools
5. **Optional Enhancements** - Agent-optimized wrappers (future v1.9.0 feature)

## Configuration

### MCP Server Config

Configure Cortex services in your `mcp_service_config.json`:

```json
{
  "snowflake": {
    "profile": "default",
    "warehouse": "CORTEX_WH",
    "database": "ANALYTICS",
    "schema": "SEMANTIC_MODELS"
  },
  "cortex": {
    "analyst": {
      "default_model": "@ANALYTICS.SEMANTIC_MODELS.STAGE/model.yaml",
      "timeout_seconds": 30
    },
    "search": {
      "default_service": "ANALYTICS.PUBLIC.CONTENT_SEARCH",
      "max_results": 50
    },
    "complete": {
      "default_model": "mistral-large",
      "max_tokens": 512
    }
  }
}
```

### Snowflake Profile

Ensure your Snowflake profile has Cortex access:

```toml
# ~/.snowflake/config.toml
[connections.cortex_profile]
account = "your_account"
user = "your_user"
warehouse = "CORTEX_WH"
database = "ANALYTICS"
schema = "SEMANTIC_MODELS"
role = "CORTEX_ROLE"  # Role with CORTEX usage privileges
```

## Checking Cortex Availability

Use the `health_check` tool to verify Cortex availability:

```python
from nanuk_mcp.mcp.tools import HealthCheckTool

health_tool = HealthCheckTool(config, snowflake_service)

result = await health_tool.execute(include_cortex=True)

if result["cortex"]["available"]:
    print("✅ Cortex AI services available")
    print(f"Model: {result['cortex']['model']}")
else:
    print("❌ Cortex unavailable")
    print(f"Status: {result['cortex']['status']}")
    print(f"Error: {result['cortex'].get('error', 'Unknown')}")
```

## Common Use Cases

### 1. Business Analytics

**Use Cortex Analyst** for natural language business questions:

```python
# Ask business questions in natural language
questions = [
    "What were our top 5 products by revenue last quarter?",
    "Show me customer retention rate by region",
    "Which sales reps exceeded their quota this month?"
]

for question in questions:
    result = query_cortex_analyst(
        semantic_model="@DB.SCHEMA.STAGE/sales_model.yaml",
        query=question
    )
    print(f"Q: {question}")
    print(f"A: {result}")
```

### 2. Customer Support

**Use Cortex Search** for finding relevant support tickets:

```python
# Search customer feedback
results = query_cortex_search(
    search_service="DB.SCHEMA.SUPPORT_TICKETS_SEARCH",
    query="billing issues",
    columns=["ticket_id", "customer_name", "issue_description"],
    limit=10
)
```

### 3. Data Summarization

**Use Cortex Complete** for summarizing data:

```python
# Summarize sales trends
summary = complete_cortex(
    model="mistral-large",
    prompt=f"""Summarize the following sales data:
    - Q1 Revenue: $1.2M
    - Q2 Revenue: $1.5M
    - Q3 Revenue: $1.8M
    - Q4 Revenue: $2.1M
    
    Provide a brief executive summary with key insights.""",
    max_tokens=256
)

print(summary)
```

## Limitations

### Cortex Analyst

- Semantic model size limit: 128 KB
- Table limit: ~10 tables recommended for best performance
- No dynamic queries (must pre-define tables in model)
- No VARIANT support in semantic models

### Cortex Search

- Requires search service setup
- Column-based search only
- Text data type limitations

### Cortex Complete

- Token limits based on model
- Rate limiting applies
- Cost per token

## Cost Considerations

Cortex services incur costs:

- **Cortex Analyst**: ~$0.02-0.10 per query (varies by complexity)
- **Cortex Search**: ~$0.01 per search
- **Cortex Complete**: ~$0.001-0.01 per 1K tokens (model dependent)

Monitor costs via Snowflake's usage views:
```sql
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_USAGE
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC;
```

## Best Practices

### 1. Use Appropriate Service

- **Analyst**: Structured data queries, business analytics
- **Search**: Unstructured text search, finding relevant content
- **Complete**: Text generation, summarization, creative tasks

### 2. Optimize Semantic Models

For Cortex Analyst:
- Keep models focused (5-10 tables max)
- Define clear relationships
- Use descriptive names
- Include relevant filters

### 3. Cache Results

Cache Cortex results when possible:

```python
import functools
from datetime import timedelta

@functools.lru_cache(maxsize=100)
def cached_cortex_query(query: str) -> dict:
    return query_cortex_analyst(
        semantic_model="@DB.SCHEMA.STAGE/model.yaml",
        query=query
    )
```

### 4. Monitor Usage

Track Cortex usage to control costs:

```python
# Query usage
usage_query = """
SELECT 
    SERVICE_TYPE,
    COUNT(*) as query_count,
    SUM(CREDITS_USED) as total_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_USAGE
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY SERVICE_TYPE
ORDER BY total_credits DESC
"""
```

## Troubleshooting

### Cortex Not Available

**Error**: `Cortex unavailable: not_installed`

**Solutions**:
1. Ensure Snowflake account has Cortex enabled
2. Check role has `USAGE` privilege on Cortex
3. Verify warehouse is running

### Semantic Model Not Found

**Error**: `Semantic model @DB.SCHEMA.STAGE/model.yaml not found`

**Solutions**:
1. Verify file exists in stage: `LIST @DB.SCHEMA.STAGE`
2. Check file path spelling
3. Ensure role has access to stage

### Search Service Not Found

**Error**: `Search service DB.SCHEMA.SERVICE not found`

**Solutions**:
1. Create search service first
2. Verify service name
3. Check privileges

## Next Steps

- 📘 [Cortex Analyst Guide](./analyst_guide.md) - Natural language queries
- 🔍 [Cortex Search Guide](./search_guide.md) - Semantic search setup
- 💬 [Cortex Complete Guide](./completion_guide.md) - LLM completions
- 📐 [Creating Semantic Models](./semantic_models/creating_models.md) - Model design

## Resources

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Cortex Analyst Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Cortex Search Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [snowflake-labs-mcp GitHub](https://github.com/Snowflake-Labs/snowflake-mcp)

## Support

For issues with:
- **Cortex services**: See [Snowflake Cortex Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- **nanuk-mcp integration**: Open an issue on GitHub
- **Account configuration**: Contact Snowflake support
