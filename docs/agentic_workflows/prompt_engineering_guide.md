# Agentic Prompt Engineering Guide

> **Master the art of orchestrating AI agents for Sui blockchain data analysis**

This guide provides detailed examples, templates, and best practices for crafting effective prompts that leverage the specialized agents built on snowcli-tools MCP.

## Table of Contents

1. [Prompt Fundamentals](#prompt-fundamentals)
2. [Sui Blockchain Data Analyst Prompts](#sui-blockchain-data-analyst-prompts)
3. [Snowflake Query Optimizer Prompts](#snowflake-query-optimizer-prompts)
4. [Multi-Agent Workflows](#multi-agent-workflows)
5. [Advanced Techniques](#advanced-techniques)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

---

## Prompt Fundamentals

### Basic Structure

Effective agent prompts follow this structure:

```
[CONTEXT] + [GOAL] + [CONSTRAINTS] + [OUTPUT FORMAT]
```

**Example**:
```
I have Sui blockchain data in Snowflake. I need to understand how data
flows through package 0x2::sui::SUI. Focus on transaction patterns and
limit analysis to the last 30 days. Provide a report with visualizable
lineage map.
```

### Key Principles

1. **Be Specific**: Mention exact package addresses, table names, or time ranges
2. **State Intent**: Clarify if you want exploration, optimization, or validation
3. **Set Scope**: Define boundaries (time range, depth, tables, etc.)
4. **Specify Format**: Indicate desired output (report, query, recommendations)

---

## Sui Blockchain Data Analyst Prompts

### Basic Analysis Prompts

#### Simple Package Analysis
```
Analyze the data architecture for Sui package 0x2::sui::SUI
```

**What the agent will do**:
- Explore catalog for relevant tables
- Query transaction and object tables
- Map dependencies
- Generate standard report

---

#### Focused Component Analysis
```
Using the snowcli-tools MCP, analyze how package 0x3::staking::StakingPool
interacts with validator data. Focus on the STAKING_EVENTS and
VALIDATOR_CHANGES tables specifically.
```

**What the agent will do**:
- Start with specified tables
- Check lineage between them
- Analyze event patterns
- Provide focused report on staking interactions

---

#### Time-Bounded Analysis
```
Generate a comprehensive report on package 0x5::dex::Pool data flows
for the last 7 days. Include transaction volume metrics and peak activity
patterns.
```

**What the agent will do**:
- Add time filters to queries
- Calculate volume metrics
- Identify peak periods
- Include temporal analysis in report

---

### Advanced Analysis Prompts

#### Multi-Package Comparison
```
Compare the data architecture and flow patterns between:
1. Package 0x2::coin::Coin
2. Package 0x3::token::Token

Highlight differences in event generation, object creation patterns, and
dependency complexity. Provide side-by-side comparison table.
```

**What the agent will do**:
- Analyze each package separately
- Compare architectures
- Generate comparison metrics
- Create structured comparison output

---

#### Dependency Deep Dive
```
For package 0x4::lending::Market, trace all upstream and downstream
dependencies to depth 3. For each dependency, show:
- Table name
- Relationship type (direct/indirect)
- Data volume
- Last update timestamp

Present as a hierarchical tree structure.
```

**What the agent will do**:
- Use query_lineage with depth=3
- Gather metadata for each dependency
- Query row counts and timestamps
- Format as tree structure

---

#### Data Quality Assessment
```
Analyze package 0x6::nft::Collection and identify:
- Missing or null critical fields
- Duplicate records
- Referential integrity issues
- Timestamp anomalies

Prioritize issues by severity and provide remediation SQL.
```

**What the agent will do**:
- Query tables for quality metrics
- Run validation checks
- Categorize issues by severity
- Generate fix queries

---

### Exploratory Analysis Prompts

#### Open-Ended Discovery
```
I have a new Sui DeFi protocol at package 0x7::protocol. I don't know
the data structure yet. Please:

1. Discover all related tables in the catalog
2. Map the data architecture
3. Identify key entities and relationships
4. Suggest analysis opportunities

Start from scratch - assume I know nothing about how this data is organized.
```

**What the agent will do**:
- Search catalog for package references
- Inspect table schemas
- Build dependency map
- Suggest next steps

---

#### Pattern Recognition
```
Analyze transaction patterns for package 0x8::game::Arena over the last
30 days. Identify:
- Recurring behaviors
- Anomalous activity
- Growth trends
- User segmentation patterns

Use clustering or classification if appropriate.
```

**What the agent will do**:
- Extract transaction data
- Perform pattern analysis
- Identify clusters and outliers
- Provide insights with SQL examples

---

## Snowflake Query Optimizer Prompts

### Basic Optimization Prompts

#### Simple Query Optimization
```sql
Optimize this query - it's taking over 60 seconds:

SELECT
  sender,
  COUNT(*) as tx_count,
  SUM(amount) as total_amount
FROM sui_transactions
WHERE package_id = '0x2::sui::SUI'
  AND timestamp > DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY sender
ORDER BY total_amount DESC
LIMIT 100;
```

**What the agent will do**:
- Analyze query structure
- Check table clustering/partitioning
- Recommend index or clustering keys
- Provide optimized query variant
- Estimate performance improvement

---

#### Join Optimization
```sql
This join is slow - please optimize:

SELECT
  t.transaction_id,
  t.sender,
  o.object_id,
  o.object_type
FROM sui_transactions t
JOIN sui_objects o ON t.transaction_id = o.created_by_tx
WHERE t.timestamp > '2025-01-01'
  AND o.package_id = '0x3::nft::Collection';
```

**What the agent will do**:
- Analyze join strategy
- Check cardinality of joined columns
- Recommend clustering/partitioning
- Suggest join order changes
- Provide before/after plans

---

### Advanced Optimization Prompts

#### Aggregation Performance
```
I have a query that aggregates 500M rows from SUI_TRANSACTIONS table
for daily metrics. It times out after 10 minutes. The query groups by:
- date (truncated timestamp)
- package_id
- function_name

Suggest schema optimizations and query rewrites to get this under 30 seconds.
```

**What the agent will do**:
- Recommend clustering by date + package_id
- Suggest materialized view approach
- Provide incremental aggregation pattern
- Calculate expected performance gain
- Include DDL for recommended changes

---

#### Window Function Optimization
```sql
Optimize this window function query:

SELECT
  sender,
  timestamp,
  amount,
  ROW_NUMBER() OVER (PARTITION BY sender ORDER BY timestamp DESC) as rn,
  SUM(amount) OVER (PARTITION BY sender ORDER BY timestamp
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
FROM sui_transactions
WHERE package_id = '0x4::lending::Market'
QUALIFY rn <= 10;
```

**What the agent will do**:
- Analyze window function cost
- Check partitioning alignment
- Recommend QUALIFY optimization
- Suggest intermediate table approach if needed
- Provide optimized version

---

#### Schema Design Review
```
Review the schema design for these Sui blockchain tables:

Tables:
- SUI_TRANSACTIONS (2B rows, 500GB)
- SUI_OBJECTS (5B rows, 1.2TB)
- SUI_EVENTS (10B rows, 3TB)

Common query patterns:
- Filter by package_id + timestamp
- Join transactions → objects → events
- Aggregate by date + package
- Search by sender/recipient address

Recommend clustering keys, partitioning strategy, and any schema changes.
```

**What the agent will do**:
- Analyze table sizes and query patterns
- Recommend clustering keys per table
- Suggest partitioning strategies
- Calculate storage/performance tradeoffs
- Provide DDL for changes

---

## Multi-Agent Workflows

### Sequential Agent Orchestration

#### Analysis → Optimization Pipeline
```
Step 1: Use the Sui Blockchain Data Analyst to analyze package
0x5::amm::Pool and identify the 5 slowest queries in the analysis.

Step 2: Use the Snowflake Query Optimizer to optimize each of those
5 queries.

Step 3: Re-run the analysis with optimized queries and compare the
total time improvement.

Provide a final report with time savings and optimization recommendations.
```

**Workflow**:
1. Data Analyst identifies slow queries
2. Query Optimizer improves each one
3. Data Analyst validates improvements
4. Combined report generated

---

#### Iterative Refinement
```
Iteratively analyze and optimize package 0x6::dex::Router:

Round 1: Initial analysis with current schema
Round 2: Apply top 3 optimization recommendations
Round 3: Re-analyze to measure improvement
Round 4: Apply next tier optimizations
Round 5: Final analysis and report

Stop early if we achieve <100ms average query time.
```

**Workflow**:
- Cycles between analysis and optimization
- Measures improvement each round
- Stops when target met
- Provides iteration history

---

### Parallel Agent Patterns

#### Comparative Analysis
```
In parallel:

Agent A: Analyze package 0x7::bridge::EthBridge
Agent B: Analyze package 0x8::bridge::BscBridge

Then compare their:
- Data architecture complexity
- Query performance characteristics
- Schema optimization opportunities
- Integration patterns

Identify which bridge has better data modeling and why.
```

**Workflow**:
- Two analysts work simultaneously
- Results compared after completion
- Synthesis report generated
- Best practices identified

---

## Advanced Techniques

### Context Injection

#### Using Previous Analysis
```
Based on the previous analysis of package 0x2::sui::SUI
(from our last conversation), now analyze package 0x9::wrapped::WSUI
and specifically compare:

1. How WSUI dependencies differ from SUI
2. Whether WSUI queries can reuse SUI optimizations
3. If WSUI introduces new performance challenges

Reference specific tables and queries from the previous analysis.
```

**Technique**: Builds on prior context to deepen analysis

---

### Constraint-Driven Prompts

#### Budget Constraints
```
Optimize queries for package 0xa::oracle::PriceFeed with these constraints:

- Total analysis time < 5 minutes
- Warehouse budget: X-Small only
- Must complete within free tier query limits
- Prioritize high-impact optimizations

Focus on "quick wins" that deliver 80% of benefit with 20% of effort.
```

**Technique**: Forces prioritization and efficient execution

---

#### Data Freshness Requirements
```
Analyze package 0xb::realtime::Events with real-time requirements:

- Data must be <5 minutes old
- Queries must complete <1 second
- Schema must support continuous ingestion
- Recommend streaming table strategy

Provide architecture for real-time analytics pipeline.
```

**Technique**: Guides toward specific architectural patterns

---

## Common Patterns

### Pattern 1: Catalog → Query → Analyze
```
1. First, check what tables exist for Sui package 0xc::defi::Protocol
2. Then, query the top 3 most relevant tables
3. Finally, analyze the data patterns and generate insights

Provide SQL for each query and explain reasoning.
```

### Pattern 2: Hypothesis → Test → Conclude
```
Hypothesis: Package 0xd::nft::Marketplace has inefficient duplicate
event storage.

Test this by:
1. Querying for duplicate events
2. Calculating storage waste
3. Analyzing query impact

Conclude with recommendation: keep duplicates, deduplicate, or optimize queries.
```

### Pattern 3: Baseline → Optimize → Validate
```
1. Baseline: Run current query and measure performance
2. Optimize: Apply recommended improvements
3. Validate: Re-run and compare results

Document exact performance gains (time, data scanned, cost).
```

---

## Troubleshooting

### When Agent Gets Stuck

**Symptom**: Agent keeps exploring but not synthesizing

**Better Prompt**:
```
Stop exploration. Based on the data you've gathered so far for package
0xe::protocol, generate the report now even if incomplete. Mark any
gaps as "[NEEDS MORE DATA]".
```

---

### When Results Are Too Broad

**Symptom**: Agent returns overwhelming amount of information

**Better Prompt**:
```
Narrow the previous analysis to only:
- Top 5 most-used tables
- Queries that touch >1M rows
- Dependencies of depth 1 only

Exclude everything else from the report.
```

---

### When Performance Is Slow

**Symptom**: Agent queries are timing out

**Better Prompt**:
```
Re-do the analysis with these guardrails:
- Use LIMIT 1000 on all sample queries
- Set timeout to 10 seconds per query
- Skip lineage analysis if too slow
- Use catalog metadata instead of full scans where possible

Provide "lite" version of analysis.
```

---

## Prompt Templates

### Template: New Package Analysis
```
Analyze Sui package [PACKAGE_ADDRESS] in Snowflake.

Scope: [full/focused/light]
Time Range: [last N days / all time / specific dates]
Depth: [surface/medium/deep]

Focus on:
- [ ] Data architecture
- [ ] Table relationships
- [ ] Query patterns
- [ ] Performance issues
- [ ] Data quality

Output format: [report/queries/recommendations/all]
```

### Template: Query Optimization
```
Optimize this [type: select/join/aggregate/window] query:

```sql
[YOUR QUERY HERE]
```

Context:
- Table size: [rows/GB]
- Current runtime: [seconds]
- Target runtime: [seconds]
- Warehouse: [size]

Constraints:
- [ ] Cannot modify schema
- [ ] Cannot add materialized views
- [ ] Must maintain exact results
- [ ] Budget: [limit]

Provide:
1. Optimized query
2. Expected improvement
3. Explanation of changes
```

### Template: Comparative Analysis
```
Compare these Sui packages:
1. [PACKAGE_1]
2. [PACKAGE_2]
3. [PACKAGE_3]

Comparison dimensions:
- [ ] Data volume
- [ ] Schema complexity
- [ ] Query performance
- [ ] Dependency depth
- [ ] Data freshness

Output: Comparison table + winner + reasoning
```

---

## Best Practices Summary

### Do's ✅

- Provide specific package addresses and table names
- Set explicit time boundaries for queries
- Specify desired output format upfront
- Use constraints to guide agent priorities
- Build on previous analysis for continuity
- Break complex requests into phases

### Don'ts ❌

- Don't use vague terms like "recent" or "big"
- Don't ask for everything at once
- Don't skip context about data scale
- Don't omit performance requirements
- Don't forget to specify depth limits
- Don't assume agent knows your schema

---

## Examples in Action

### Example 1: Full Workflow
```
Task: Analyze new Sui DEX package 0x123abc

Prompt 1 (Discovery):
"Catalog all tables related to package 0x123abc"

Prompt 2 (Analysis):
"For the tables found, analyze the swap transaction flow from user
action to liquidity pool update"

Prompt 3 (Optimization):
"The swap query took 45 seconds. Optimize it to <5 seconds."

Prompt 4 (Validation):
"Re-run the analysis with optimized queries and generate final report
comparing before/after performance"
```

### Example 2: Troubleshooting
```
Task: Figure out why package 0x456def queries are slow

Prompt 1:
"Analyze query performance for package 0x456def - focus only on
queries that take >10 seconds"

Prompt 2:
"For the slow queries identified, check:
1. Are tables clustered properly?
2. Are there missing joins?
3. Is data distribution skewed?"

Prompt 3:
"Provide specific DDL to fix the top 3 issues found"

Prompt 4:
"Estimate time/cost savings if we apply these fixes"
```

---

## See Also

- [Agent Configurations](./agent_configurations.md) - Agent architecture details
- [MCP Server User Guide](../mcp_server_user_guide.md) - MCP setup
- [Features Overview](../features_overview.md) - Available MCP tools
