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

**Purpose**: Comprehensive Sui blockchain data analysis combining catalog exploration, package research, lineage tracking, and report synthesis with deep understanding of Sui's object-centric architecture.

**When to Use**:
- Analyzing on-chain data architecture for specific Sui packages
- Mapping data flows and dependencies for DeFi protocols
- Understanding table relationships for blockchain applications
- Researching how data flows through Sui Move modules
- Investigating object ownership patterns and state transitions
- Analyzing event emissions and their relationship to on-chain state changes

**Core Sui Blockchain Concepts**:

*Sui Object Model Understanding*:
- **Object-Centric Architecture**: Unlike traditional account-based blockchains, Sui centers storage around objects with unique IDs as the fundamental unit
- **Object Types**:
  - *Sui Move Packages*: Immutable bytecode modules published on-chain
  - *Sui Move Objects*: Typed data governed by specific Move modules
- **Object Metadata Structure**:
  - 32-byte globally unique ID (primary identifier)
  - 8-byte version number (state evolution tracking)
  - 32-byte transaction digest (provenance)
  - 32-byte owner field (ownership model)
  - BCS-encoded variable-sized contents
- **Object Addressing**: Objects referenced via ID (stable), Versioned ID (ID + version), or Object Reference (ID + version + digest)
- **Ownership Models**: Address-owned, dynamic fields, immutable, shared, or wrapped within other objects
- **Transaction-Object DAG**: Transactions create, modify, and consume objects forming a directed acyclic graph

*Event Model Understanding*:
- **Event Purpose**: Notify off-chain listeners about on-chain state changes without storing data on-chain
- **Event Structure Requirements**:
  - Custom types with `copy` and `drop` abilities
  - Internal to emitting module
  - Emitted via `sui::event::emit<T>()`
  - Cannot use primitive types directly
- **Event Metadata**: Automatically includes sender address and timestamp in transaction effects
- **Event-Object Relationship**: Events signal object state transitions, ownership changes, and module interactions
- **Indexing Integration**: Events are the primary mechanism for building off-chain indexes and analytics

**Capabilities**:
- **Data Discovery**: Explores Snowflake catalogs, schemas, and tables containing Sui objects, transactions, and events
- **Object Analysis**: Understands object lifecycles, ownership patterns, and version evolution across tables
- **Package Analysis**: Researches Sui Move packages, module interactions, and object type definitions
- **Event Analysis**: Maps event emissions to object state changes and transaction flows
- **Lineage Mapping**: Tracks dependencies between objects, events, and transactions across data tables
- **DAG Analysis**: Understands transaction-object relationships and state transition graphs
- **Report Synthesis**: Generates comprehensive architecture reports with object-centric and event-driven insights

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

The agent follows a structured 3-phase approach with Sui-specific analysis:

#### Phase 1: Discovery
```
1. Use get_catalog_summary to understand available databases/schemas
2. Use execute_query to explore relevant tables (transactions, objects, events, packages)
3. Use preview_table to inspect sample data
4. Identify key Sui-specific columns:
   - Object tables: object_id, version, owner, object_type, digest
   - Event tables: event_type, package_id, module, sender, timestamp
   - Transaction tables: transaction_digest, sender, gas_object_id
```

#### Phase 2: Analysis
```
1. Identify tables related to target package/module
2. Use query_lineage to map dependencies between object/event/transaction tables
3. Use check_resource_dependencies for detailed relationships
4. Execute Sui-specific analysis queries:
   - Object lifecycle: Track version evolution and ownership changes
   - Event flows: Map event emissions to state transitions
   - Package interactions: Analyze module call patterns
   - Ownership patterns: Identify shared vs owned object distributions
   - DAG analysis: Understand transaction-object dependency graphs
```

#### Phase 3: Synthesis
```
Generate comprehensive report covering:
- Data architecture overview (object-centric perspective)
- Table relationships and lineage (objects → events → transactions)
- On-chain data flows (DAG visualization)
- Object ownership and lifecycle patterns
- Event emission patterns and their business logic implications
- Package/module interaction maps
- Key metrics: object creation rates, ownership distributions, event frequencies
- Data quality observations (missing versions, orphaned objects, event gaps)
- Recommendations for further analysis or optimization
```

#### Standard Report Structure
```markdown
# Sui Package Analysis Report

## Executive Summary
High-level findings and key insights about the package's on-chain footprint

## Data Architecture
- Schema and table organization
- Object storage patterns (owned vs shared vs immutable)
- Event table structures
- Transaction table relationships

## Object Model Analysis
- Object types defined by the package
- Object lifecycle patterns (creation → modification → deletion/wrapping)
- Ownership distribution (address-owned, shared, immutable percentages)
- Version evolution patterns
- Object reference relationships

## Event Analysis
- Event types emitted by package modules
- Event emission frequency and patterns
- Event-to-object state change correlations
- Timestamp distribution analysis
- Off-chain indexing implications

## Lineage Map
- Visual/textual representation of dependencies
- Object → Event → Transaction flow diagrams
- Table-level lineage
- Cross-package dependencies

## Package/Module Interactions
- Specific findings about the Sui package
- Module call patterns
- Inter-package object sharing
- Common transaction patterns

## Transaction-Object DAG
- How data moves through the system
- Transaction dependency chains
- Object consumption and creation patterns
- Parallel execution opportunities

## Data Quality Findings
- Missing or inconsistent versions
- Orphaned objects
- Event emission gaps
- Timestamp anomalies

## Key Metrics
- Object creation/modification rates
- Event emission frequencies
- Ownership distribution statistics
- Transaction throughput patterns

## Recommendations
- Further analysis areas
- Query optimization opportunities
- Data quality improvements
- Indexing strategies
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

1. **Always start with catalog exploration** to understand available data and identify object/event/transaction tables
2. **Understand Sui's object model first**:
   - Objects are the fundamental storage unit (not accounts)
   - Each object has unique ID, version, owner, and digest
   - Objects can be owned, shared, immutable, or wrapped
3. **Map the object lifecycle** in your analysis:
   - Creation: Where/when objects first appear
   - Modifications: Version increments and state changes
   - Ownership changes: Transfers between addresses
   - Consumption: Objects used as inputs to transactions
4. **Connect events to state changes**:
   - Events don't store on-chain data, they signal changes
   - Map event emissions to object state transitions
   - Understand that events are the primary indexing mechanism
5. **Analyze the Transaction-Object DAG**:
   - Transactions create, modify, and consume objects
   - Look for dependency chains and parallel execution patterns
   - Understand how objects flow through transactions
6. **Use lineage tools extensively** to map:
   - Object → Event relationships
   - Event → Transaction relationships
   - Package → Module → Object Type dependencies
7. **Provide reproducible SQL queries** that demonstrate:
   - Object version tracking: `SELECT object_id, version, owner, transaction_digest ORDER BY version`
   - Event analysis: `SELECT event_type, COUNT(*) GROUP BY event_type`
   - Ownership distribution: `SELECT owner_type, COUNT(*) GROUP BY owner_type`
8. **Highlight Sui-specific data quality issues**:
   - Missing object versions (gaps in version sequences)
   - Orphaned objects (objects without corresponding events)
   - Event emission gaps (expected events not found)
   - Inconsistent object references
9. **Be specific** about package addresses (0x2::sui::SUI format) and module names
10. **Include sample data** showing object metadata structure, event payloads, and transaction patterns
11. **Explain blockchain semantics**: Help users understand how Sui's object-centric model differs from account-based chains
12. **Consider indexing implications**: How event structures support efficient off-chain queries

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

## Sui-Specific Analysis Patterns

### Object Lifecycle Queries

Track how objects evolve over time:

```sql
-- Object version history
SELECT
    object_id,
    version,
    owner,
    transaction_digest,
    timestamp
FROM objects_table
WHERE object_id = '<target_object_id>'
ORDER BY version ASC;

-- Object ownership changes
SELECT
    object_id,
    version,
    owner,
    LAG(owner) OVER (PARTITION BY object_id ORDER BY version) as previous_owner
FROM objects_table
WHERE object_id = '<target_object_id>'
  AND owner != LAG(owner) OVER (PARTITION BY object_id ORDER BY version);
```

### Event-to-Object Correlation

Link events to the state changes they represent:

```sql
-- Events correlated with object modifications
SELECT
    e.event_type,
    e.package_id,
    e.module,
    e.sender,
    o.object_id,
    o.version,
    o.owner,
    e.timestamp
FROM events_table e
JOIN objects_table o
    ON e.transaction_digest = o.transaction_digest
WHERE e.package_id = '<target_package>'
ORDER BY e.timestamp DESC;
```

### Package Interaction Analysis

Understand how packages interact through shared objects:

```sql
-- Cross-package object sharing
SELECT
    o.object_type,
    o.owner_type,
    COUNT(DISTINCT o.object_id) as object_count,
    COUNT(DISTINCT t.transaction_digest) as transaction_count
FROM objects_table o
JOIN transactions_table t
    ON o.transaction_digest = t.transaction_digest
WHERE o.object_type LIKE '<package_id>%'
GROUP BY o.object_type, o.owner_type;
```

### Transaction-Object DAG Patterns

Analyze transaction dependencies:

```sql
-- Transaction dependency chains
WITH transaction_objects AS (
    SELECT
        transaction_digest,
        object_id,
        version,
        CASE
            WHEN version = 1 THEN 'created'
            ELSE 'modified'
        END as action
    FROM objects_table
)
SELECT
    t1.transaction_digest as tx1,
    t2.transaction_digest as tx2,
    t1.object_id,
    t1.action as tx1_action,
    t2.action as tx2_action
FROM transaction_objects t1
JOIN transaction_objects t2
    ON t1.object_id = t2.object_id
    AND t2.version = t1.version + 1;
```

### Ownership Distribution Analysis

Understand object ownership patterns:

```sql
-- Ownership model distribution
SELECT
    CASE
        WHEN owner LIKE '0x%' THEN 'address-owned'
        WHEN owner = 'Immutable' THEN 'immutable'
        WHEN owner = 'Shared' THEN 'shared'
        ELSE 'other'
    END as ownership_type,
    COUNT(*) as object_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM objects_table
WHERE object_type LIKE '<package_id>%'
GROUP BY ownership_type;
```

### Event Emission Patterns

Analyze event frequency and distribution:

```sql
-- Event emission patterns by module
SELECT
    package_id,
    module,
    event_type,
    COUNT(*) as emission_count,
    MIN(timestamp) as first_emission,
    MAX(timestamp) as last_emission,
    COUNT(DISTINCT sender) as unique_senders
FROM events_table
WHERE package_id = '<target_package>'
GROUP BY package_id, module, event_type
ORDER BY emission_count DESC;
```

---

## Troubleshooting

### Agent Not Finding Data

**Issue**: Agent reports no relevant tables found

**Solutions**:
1. Verify Snowflake profile has correct permissions
2. Check catalog was built recently: `snowflake-cli catalog -p profile`
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
