# Cortex Complete Guide

**LLM-Powered Text Generation**

## Overview

Cortex Complete provides access to large language models for text generation, summarization, and analysis.

## Available Models

- `mistral-large` - Best for complex tasks
- `mixtral-8x7b` - Balanced performance/cost
- `llama3-8b` - Fast, cost-effective
- `llama3-70b` - High quality

## Basic Usage

```python
from mcp_server_snowflake.cortex_services.tools import complete_cortex

response = complete_cortex(
    model="mistral-large",
    prompt="Summarize: [your text here]",
    max_tokens=256,
    snowflake_service=snowflake_service
)

print(response)
```

## Common Use Cases

### Summarization

```python
complete_cortex(
    model="mistral-large",
    prompt=f"""Summarize this sales report:
    Q1: $1.2M revenue, 15% growth
    Q2: $1.5M revenue, 25% growth
    Q3: $1.8M revenue, 20% growth
    
    Provide executive summary with key insights.""",
    max_tokens=200
)
```

### Data Analysis

```python
complete_cortex(
    model="mistral-large",
    prompt=f"""Analyze this customer feedback:
    - 45% mentioned shipping delays
    - 30% praised product quality
    - 25% requested new features
    
    What should we prioritize?""",
    max_tokens=300
)
```

### Classification

```python
complete_cortex(
    model="llama3-8b",
    prompt=f"""Classify this support ticket as: bug, feature_request, or question
    
    Ticket: "The dashboard doesn't load on mobile devices"
    
    Classification:""",
    max_tokens=10
)
```

## Best Practices

1. **Choose right model** - Balance quality vs cost
2. **Limit tokens** - Set appropriate max_tokens
3. **Clear prompts** - Be specific about desired output
4. **Monitor usage** - Track token consumption

## See Also

- [Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
