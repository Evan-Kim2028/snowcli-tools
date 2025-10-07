# Agentic Framework for Snowflake-CLI Tools

> **Advanced multi-agent orchestration for Sui blockchain data analysis**

This document describes specialized agents designed to work with snowcli-tools MCP server for comprehensive Sui blockchain data analysis workflows.

## Overview

These agents are designed to orchestrate complex, multi-step workflows that combine:
- Snowflake catalog exploration
- Sui blockchain package analysis
- Data lineage tracking
- Performance optimization
- Comprehensive report generation

## Available Agents

### 1. Sui Blockchain Data Analyst

**Agent ID**: `sui-blockchain-data-analyst`

**Purpose**: Comprehensive Sui blockchain data analysis combining catalog exploration, package research, lineage tracking, and report synthesis.

**When to Use**:
- Analyzing on-chain data architecture for specific Sui packages
- Mapping data flows and dependencies for DeFi protocols
- Understanding table relationships for blockchain applications
- Researching how data flows through Sui Move modules

**Capabilities**:
- **Data Discovery**: Explores Snowflake catalogs, schemas, and tables containing Sui data
- **Package Analysis**: Researches Sui Move packages and on-chain interactions
- **Lineage Mapping**: Tracks dependencies and data flows between tables
- **Report Synthesis**: Generates comprehensive architecture and flow reports

**Tools Available**: All snowcli-tools MCP tools

---

### 2. Snowflake Query Optimizer

**Agent ID**: `snowflake-query-optimizer`

**Purpose**: Expert query optimization, performance analysis, and schema improvement recommendations for Sui blockchain data warehousing.

**When to Use**:
- Optimizing slow queries on large blockchain tables
- Analyzing join performance issues
- Recommending clustering keys and partitioning strategies
- Reviewing aggregation query performance

**Capabilities**:
- **Query Analysis**: Reviews execution plans and identifies bottlenecks
- **Schema Optimization**: Suggests clustering keys, partitioning, materialized views
- **Performance Testing**: Validates improvements with controlled timeouts
- **Blockchain-Specific**: Understands high cardinality blockchain data patterns

**Tools Available**: All snowcli-tools MCP tools

---

## Agent Workflows

### Sui Blockchain Data Analyst Workflow

The agent follows a structured 3-phase approach:

#### Phase 1: Discovery
```
1. Use get_catalog_summary to understand available databases/schemas
2. Use execute_query to explore relevant tables (transactions, objects, events)
3. Use preview_table to inspect sample data
```

#### Phase 2: Analysis
```
1. Identify tables related to target package/module
2. Use query_lineage to map dependencies
3. Use check_resource_dependencies for detailed relationships
4. Execute targeted SQL queries to understand patterns
```

#### Phase 3: Synthesis
```
Generate comprehensive report covering:
- Data architecture overview
- Table relationships and lineage
- On-chain data flows
- Key metrics and patterns
- Recommendations for further analysis
```

#### Standard Report Structure
```markdown
# Package Analysis Report

## Executive Summary
High-level findings and key insights

## Data Architecture
Schema and table organization

## Lineage Map
Visual/textual representation of dependencies

## Package Analysis
Specific findings about the Sui package

## Data Flows
How data moves through the system

## Recommendations
Next steps or areas of interest
```

---

### Snowflake Query Optimizer Workflow

The agent follows a systematic 4-step optimization process:

#### Step 1: Understand Context
```
1. Get table schemas via catalog
2. Check table sizes and row counts
3. Review existing indexes/clustering
```

#### Step 2: Diagnose Issues
```
1. Analyze query patterns
2. Identify expensive operations (scans, joins, aggregations)
3. Check for missing filters or poor join conditions
```

#### Step 3: Recommend Solutions
```
1. Provide optimized query rewrites
2. Suggest schema changes (clustering, partitioning)
3. Recommend warehouse sizing
```

#### Step 4: Validate Improvements
```
1. Test optimized queries
2. Compare execution times
3. Document performance gains
```

---

## Implementation Architecture

### How Agents Work with MCP

```
┌─────────────────────────────────────────┐
│   User Request (Natural Language)       │
│   "Analyze Sui package 0x2::sui::SUI"  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Specialized Agent (Task Orchestrator) │
│   - Breaks down request into steps      │
│   - Makes decisions between actions      │
│   - Synthesizes findings                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Snowcli-Tools MCP (Atomic Tools)      │
│   - execute_query                        │
│   - preview_table                        │
│   - query_lineage                        │
│   - build_catalog                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Snowflake Data Warehouse              │
│   (Sui Blockchain Data)                 │
└─────────────────────────────────────────┘
```

### Agent vs Tool Distinction

**Agents** (reasoning layer):
- Make decisions between steps
- Handle open-ended exploration
- Synthesize findings into reports
- Adapt workflow based on findings

**Tools** (execution layer):
- Perform atomic operations
- Return structured data
- Execute specific queries
- No decision-making logic

### Why Not Build Another MCP?

These agents should **NOT** be implemented as MCP tools because:

1. **Multi-step reasoning required**: Can't predetermine exact query sequence
2. **Context-dependent decisions**: What to query next depends on previous results
3. **Synthesis required**: Need to generate narrative reports, not just return data
4. **Open-ended exploration**: Different packages need different analysis approaches

---

## Agent Best Practices

### For Sui Blockchain Data Analyst

1. **Always start with catalog exploration** to understand available data
2. **Use lineage tools extensively** to avoid missing relationships
3. **Provide reproducible SQL queries** in reports
4. **Highlight data quality issues** discovered during analysis
5. **Be specific** about package addresses and module names
6. **Include sample data** when illustrating patterns

### For Snowflake Query Optimizer

1. **Always explain WHY** an optimization works
2. **Provide before/after examples** for clarity
3. **Consider blockchain data patterns** (high cardinality addresses/hashes)
4. **Account for data distribution** in optimization recommendations
5. **Recommend appropriate warehouse sizes** for workloads
6. **Use query timeouts** to prevent runaway queries during testing

---

## Integration Points

### Claude Code Integration

These agents are designed to work seamlessly with Claude Code's Task agent functionality:

```bash
# The agent framework is already available
# Just use natural language prompts that match agent capabilities
```

### MCP Server Requirements

Ensure snowcli-tools MCP server is configured:

```json
{
  "mcpServers": {
    "snowcli-tools": {
      "command": "uv",
      "args": ["run", "snowflake-cli", "mcp"],
      "env": {
        "SNOWFLAKE_PROFILE": "your-profile-name"
      }
    }
  }
}
```

---

## Advanced Usage Patterns

### Multi-Agent Workflows

Agents can be chained for complex analysis:

1. **Data Analyst** → identifies slow queries
2. **Query Optimizer** → optimizes those queries
3. **Data Analyst** → re-analyzes with improved performance

### Iterative Refinement

Agents support iterative workflows:

```
User: "Analyze package 0x2::sui::SUI"
Agent: [Generates initial report]

User: "Now focus on the transaction flow patterns"
Agent: [Deepens analysis on specific area]

User: "Compare this with package 0x3::staking"
Agent: [Comparative analysis]
```

### Custom Workflows

While agents have standard workflows, they adapt to:
- Specific user requirements
- Data availability constraints
- Performance considerations
- Analysis depth preferences

---

## Troubleshooting

### Agent Not Finding Data

**Issue**: Agent reports no relevant tables found

**Solutions**:
1. Verify Snowflake profile has correct permissions
2. Check catalog was built recently: `snowflake-cli -p profile catalog`
3. Ensure database/schema contain expected Sui data
4. Manually verify tables exist: `execute_query "SHOW TABLES"`

### Slow Query Optimization Not Effective

**Issue**: Optimizer recommendations don't improve performance

**Solutions**:
1. Check if recommended clustering/partitioning was applied
2. Verify warehouse size is appropriate for data volume
3. Review query plan to confirm optimization was used
4. Consider data distribution may require different approach

### Agent Workflow Interrupted

**Issue**: Agent stops mid-analysis or times out

**Solutions**:
1. Increase MCP timeout: `export MCP_TIMEOUT=60000`
2. Break down request into smaller chunks
3. Use explicit phase requests: "Just do discovery phase first"
4. Check Snowflake warehouse is running and has credits

---

## See Also

- [Prompt Engineering Guide](./prompt_engineering_guide.md) - Detailed examples and templates
- [MCP Integration Guide](../mcp_server_user_guide.md) - MCP server setup
- [Architecture Overview](../architecture.md) - System design details
- [Features Overview](../features_overview.md) - Available MCP tools
