# Agentic Workflows for Snowcli-Tools

> **Transform Snowflake + Sui blockchain analysis with intelligent AI agents**

## Overview

This directory contains documentation for orchestrating specialized AI agents that work with the snowcli-tools MCP server to perform complex, multi-step Sui blockchain data analysis workflows.

## What Are Agentic Workflows?

**Agentic workflows** combine:
- **Agents**: AI systems that make decisions, reason between steps, and synthesize findings
- **Tools**: Atomic operations from snowcli-tools MCP (queries, catalog, lineage)
- **Orchestration**: Multi-step workflows that adapt based on intermediate results

Unlike simple tool calls, agentic workflows:
- ✅ Handle open-ended exploration
- ✅ Make context-dependent decisions
- ✅ Synthesize comprehensive reports
- ✅ Adapt workflow based on findings
- ✅ Combine multiple tool calls intelligently

## Available Documentation

### 📘 [Agent Configurations](./agent_configurations.md)
Complete reference for specialized agents:
- **Sui Blockchain Data Analyst**: Comprehensive package and data flow analysis
- **Snowflake Query Optimizer**: Performance tuning and schema optimization
- Agent architectures, workflows, and best practices

### 📗 [Prompt Engineering Guide](./prompt_engineering_guide.md)
Master prompt crafting with:
- 50+ example prompts for various scenarios
- Multi-agent orchestration patterns
- Templates and troubleshooting tips
- Real-world workflow examples

## Quick Start

### 1. Ensure MCP Server is Running

```bash
# Configure your Snowflake profile
export SNOWFLAKE_PROFILE=your-profile-name

# Start MCP server (if not already running via Claude Code config)
snowflake-cli mcp
```

### 2. Simple Agent Invocation

In Claude Code, use natural language that matches agent capabilities:

```
Analyze the on-chain data architecture for Sui package 0x2::sui::SUI
```

The appropriate agent will be automatically invoked to:
1. Explore the catalog for relevant tables
2. Query transaction and object data
3. Map dependencies and lineage
4. Generate a comprehensive report

### 3. Multi-Step Workflow

```
First, analyze package 0x3::staking and identify the 3 slowest queries.
Then optimize those queries for sub-second performance.
Finally, re-run the analysis and show the improvement.
```

Multiple agents work together:
1. **Data Analyst** finds slow queries
2. **Query Optimizer** improves them
3. **Data Analyst** validates improvements

## Architecture

```
┌──────────────────────────────────────────────────┐
│              User (Natural Language)              │
│  "Analyze Sui package 0x123 data architecture"  │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│           Specialized Agent (Orchestrator)        │
│  • Breaks down request into steps                │
│  • Makes context-dependent decisions              │
│  • Synthesizes findings                           │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│         Snowcli-Tools MCP (Atomic Tools)          │
│  • execute_query     • build_catalog              │
│  • preview_table     • query_lineage              │
│  • check_dependencies                             │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│      Snowflake Data Warehouse (Sui Data)         │
└──────────────────────────────────────────────────┘
```

## Use Cases

### 1. Package Architecture Analysis
```
"Analyze package 0x2::coin::Coin data flow and dependencies"
```
**Agent**: Sui Blockchain Data Analyst
**Output**: Comprehensive architecture report with lineage map

### 2. Query Performance Optimization
```
"This query times out - optimize it for sub-second execution"
```
**Agent**: Snowflake Query Optimizer
**Output**: Optimized query + schema recommendations + performance estimates

### 3. Comparative Analysis
```
"Compare data architectures between package A and package B"
```
**Agents**: Multiple Data Analysts working in parallel
**Output**: Side-by-side comparison with recommendations

### 4. Data Quality Assessment
```
"Analyze package 0x5::nft for data quality issues"
```
**Agent**: Sui Blockchain Data Analyst
**Output**: Quality report with remediation SQL

### 5. Real-Time Analytics Design
```
"Design a real-time analytics pipeline for package 0x7::events"
```
**Agents**: Data Analyst + Query Optimizer
**Output**: Architecture design with performance specs

## Agent Comparison

| Feature | Sui Data Analyst | Query Optimizer |
|---------|------------------|-----------------|
| **Primary Focus** | Data discovery & architecture | Performance & optimization |
| **Input** | Package address, tables | Slow queries, schemas |
| **Output** | Comprehensive reports | Optimized queries + DDL |
| **Workflow** | Discovery → Analysis → Synthesis | Context → Diagnose → Optimize → Validate |
| **Use When** | Understanding new data | Improving performance |
| **Tools Used** | All MCP tools | Primarily query-focused tools |
| **Report Format** | Narrative + visualizations | Before/after + metrics |

## Integration with Claude Code

### Configuration

Agents work automatically with Claude Code when:
1. ✅ Snowcli-tools MCP server is configured in `.claude.json`
2. ✅ Snowflake profile is valid and accessible
3. ✅ Prompts match agent capability patterns

### Example `.claude.json` MCP Configuration

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

### Agent Invocation

**Automatic** - Just use natural language:
```
"Analyze Sui package 0x123abc data flows"
```

**Explicit** - Reference agent by capability:
```
"Use the Sui blockchain data analyst agent to map package 0x456def architecture"
```

## Best Practices

### 1. Start Specific
❌ Bad: "Tell me about my data"
✅ Good: "Analyze package 0x2::sui::SUI transaction patterns for last 30 days"

### 2. Set Boundaries
❌ Bad: "Analyze everything"
✅ Good: "Analyze top 5 tables by query frequency, depth 2 lineage only"

### 3. Specify Output
❌ Bad: "Look at this query"
✅ Good: "Optimize this query and provide before/after execution times"

### 4. Build Iteratively
❌ Bad: Complex multi-part request all at once
✅ Good: Break into phases, review, then continue

### 5. Provide Context
❌ Bad: "Why is this slow?"
✅ Good: "Query scans 500GB, times out at 10min - optimize for <30sec"

## Advanced Patterns

### Sequential Chaining
```
Phase 1: "Catalog all tables for package X"
Phase 2: "Analyze the top 3 tables by size"
Phase 3: "Optimize queries on those tables"
Phase 4: "Generate final report with improvements"
```

### Parallel Execution
```
"In parallel:
Agent A: Analyze package 0xAAA
Agent B: Analyze package 0xBBB

Then compare architectures and identify best practices"
```

### Iterative Refinement
```
"Iteratively optimize package 0xCCC queries:
Round 1: Baseline
Round 2: Apply quick wins
Round 3: Deep optimization
Stop when <100ms avg query time achieved"
```

## Troubleshooting

### Agent Not Finding Data

**Issue**: "No relevant tables found"

**Solution**:
```
1. Verify profile: snowflake-cli -p profile-name verify
2. Check catalog: snowflake-cli -p profile-name catalog
3. List tables manually: execute_query "SHOW TABLES"
4. Verify permissions on INFORMATION_SCHEMA
```

### Queries Timing Out

**Issue**: Agent queries exceed timeout

**Solution**:
```
1. Increase MCP timeout: export MCP_TIMEOUT=60000
2. Add LIMIT to exploration queries
3. Request "lite" analysis version
4. Narrow scope (specific tables, date ranges)
```

### Agent Gets Stuck

**Issue**: Agent explores but doesn't conclude

**Solution**:
```
Prompt: "Generate report now based on current findings.
Mark incomplete sections as [NEEDS MORE DATA]."
```

### Results Too Broad

**Issue**: Overwhelming amount of information

**Solution**:
```
Prompt: "Narrow to: top 5 tables, depth 1 only, queries >1M rows.
Exclude all else."
```

## Examples

### Example 1: First-Time Package Analysis
```
User: "I just deployed Sui package 0x999::defi::LendingPool and ingested
data to Snowflake. I don't know the structure yet. Please analyze it."

Agent (Sui Data Analyst):
1. Searches catalog for package 0x999 references
2. Discovers LENDING_TRANSACTIONS, LENDING_POOLS, COLLATERAL tables
3. Inspects schemas and relationships
4. Maps lineage between tables
5. Generates comprehensive report with:
   - Data architecture diagram
   - Table relationships
   - Sample queries
   - Analysis recommendations

User: "Great! Now optimize the 3 slowest queries you found."

Agent (Query Optimizer):
1. Takes slow queries from previous analysis
2. Analyzes execution plans
3. Recommends clustering and partitioning
4. Provides optimized rewrites
5. Estimates 10x performance improvement
```

### Example 2: Performance Investigation
```
User: "Package 0x888::oracle queries are slow. Figure out why."

Agent (Sui Data Analyst):
1. Profiles query performance
2. Identifies PRICE_UPDATES table as bottleneck
3. Checks cardinality and data distribution
4. Detects missing clustering on timestamp + asset_id
5. Reports findings

User: "Apply the recommended optimizations."

Agent (Query Optimizer):
1. Generates DDL for clustering
2. Tests query performance before/after
3. Validates 30sec → 2sec improvement
4. Provides migration script
```

## Metrics and Performance

### Expected Performance

| Operation | Without Agent | With Agent |
|-----------|---------------|------------|
| Initial package analysis | 30+ min manual | 2-5 min automated |
| Query optimization | Trial & error hours | 5-10 min systematic |
| Lineage mapping | Manual inspection | Automated in seconds |
| Report generation | Hours of writing | Instant comprehensive output |

### Success Criteria

**Data Analyst Agent**:
- ✅ Finds all relevant tables (>95% recall)
- ✅ Correctly maps dependencies
- ✅ Generates actionable insights
- ✅ Completes in <10 minutes

**Query Optimizer Agent**:
- ✅ Achieves target performance improvement
- ✅ Maintains query correctness
- ✅ Provides reproducible optimization steps
- ✅ Estimates costs accurately

## Contributing

Want to improve the agents or add new capabilities?

1. **New Agent Ideas**: Submit feature requests with use cases
2. **Prompt Templates**: Share effective prompt patterns
3. **Workflow Examples**: Document successful multi-agent workflows
4. **Performance Tips**: Contribute optimization techniques

## Resources

### Documentation
- 📘 [Agent Configurations](./agent_configurations.md)
- 📗 [Prompt Engineering Guide](./prompt_engineering_guide.md)
- 📙 [MCP Server User Guide](../mcp_server_user_guide.md)
- 📕 [Architecture Overview](../architecture.md)

### Tools
- [Snowcli-Tools MCP](https://github.com/your-repo/snowcli-tools)
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli)
- [Claude Code](https://claude.ai/code)

### Community
- Report Issues: [GitHub Issues](https://github.com/your-repo/snowcli-tools/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/snowcli-tools/discussions)
- Examples: [Examples Directory](../../examples/)

---

**Ready to get started?** Open the [Prompt Engineering Guide](./prompt_engineering_guide.md) for detailed examples!
