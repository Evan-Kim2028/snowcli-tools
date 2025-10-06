# Workflows Guide
**Version:** 1.10.0
**Last Updated:** 2025-10-06

---

## Overview

This guide provides end-to-end workflows for common tasks using SnowCLI Tools MCP server with AI assistants. Each workflow includes step-by-step instructions, expected tool usage, and practical examples.

---

## Quick Navigation

| Workflow | Time | Complexity | Use Case |
|----------|------|------------|----------|
| [Database Discovery](#1-database-discovery) | 5-15 min | Beginner | Onboard to unfamiliar database |
| [PII Detection](#2-pii-detection) | 10-30 min | Intermediate | Compliance audit |
| [Impact Analysis](#3-impact-analysis) | 5-15 min | Intermediate | Pre-migration planning |
| [Schema Documentation](#4-schema-documentation) | 15-30 min | Intermediate | Data catalog generation |
| [Lineage Investigation](#5-lineage-investigation) | 5-10 min | Beginner | Understand data flow |
| [Quick Table Inspection](#6-quick-table-inspection) | 1-2 min | Beginner | Ad-hoc exploration |

---

## 1. Database Discovery

**Goal:** Understand structure and contents of an unfamiliar database

**Use Case:**
- New team member onboarding
- Exploring inherited database
- Auditing third-party data

### Step 1: Verify Connectivity

**AI Prompt:**
```
Test my Snowflake connection
```

**Expected Tool Usage:**
```python
test_connection()
```

**Expected Output:**
```
✅ Connected to Snowflake
Profile: prod-profile
Account: myorg-myaccount
Database: ANALYTICS
Warehouse: COMPUTE_WH
```

### Step 2: Get Database Overview

**AI Prompt:**
```
What databases and tables are available?
```

**Expected Tool Usage:**
```python
execute_query("SHOW DATABASES")
execute_query("SHOW TABLES IN DATABASE ANALYTICS")
```

### Step 3: Build Complete Catalog

**AI Prompt:**
```
Build a catalog of the ANALYTICS database
```

**Expected Tool Usage:**
```python
build_catalog(database="ANALYTICS")
```

**Time:** 1-5 minutes (depends on database size)

### Step 4: Review Catalog Summary

**AI Prompt:**
```
Show me the catalog summary
```

**Expected Tool Usage:**
```python
get_catalog_summary()
```

**Expected Output:**
```json
{
  "totals": {
    "tables": 127,
    "views": 45,
    "total_objects": 374
  }
}
```

### Step 5: Profile Key Tables

**AI Prompt:**
```
Profile these tables: CUSTOMERS, ORDERS, PRODUCTS
```

**Expected Tool Usage:**
```python
profile_table(
    table_name=["CUSTOMERS", "ORDERS", "PRODUCTS"],
    include_ai_analysis=True
)
```

**Time:** 1-2 minutes

**Result:**
- Complete schema documentation
- Column statistics
- Business context (AI-inferred)
- PII detection

---

## 2. PII Detection

**Goal:** Identify all tables containing personally identifiable information

**Use Case:**
- GDPR/CCPA compliance
- Data privacy audit
- Security assessment

### Step 1: Build Catalog

**AI Prompt:**
```
Build a catalog of the PROD_DB database
```

**Expected Tool Usage:**
```python
build_catalog(database="PROD_DB")
```

### Step 2: Get Table List

**AI Prompt:**
```
List all tables in PROD_DB
```

**Expected Tool Usage:**
```python
get_catalog_summary()
# Or
execute_query("SHOW TABLES IN DATABASE PROD_DB")
```

### Step 3: Batch Profile with AI Analysis

**AI Prompt:**
```
Profile all tables in PROD_DB and detect PII
```

**Expected Tool Usage:**
```python
profile_table(
    table_name=["CUSTOMERS", "USERS", "ORDERS", "PAYMENTS", ...],
    include_ai_analysis=True,  # Enable PII detection
    output_format="json"        # Structured output
)
```

**Time:** 5-15 minutes (depends on table count)

### Step 4: Review PII Findings

**Expected Output Format:**
```markdown
## CUSTOMERS Table

### PII Detected:
- email (CONFIRMED - Email addresses)
- phone (CONFIRMED - Phone numbers)
- name (LIKELY - Personal names)
- ssn (CONFIRMED - Social security numbers)

### Recommendations:
- Implement column-level security
- Consider data masking for non-production
- Document retention policies
```

### Step 5: Export Results

**AI Prompt:**
```
Export PII findings to JSON
```

**Result:** Structured JSON with all PII columns across database

**Use For:**
- Compliance reports
- Security reviews
- Data governance documentation

---

## 3. Impact Analysis

**Goal:** Understand what breaks if you change a table or view

**Use Case:**
- Pre-migration planning
- Schema refactoring
- Deprecation analysis

### Step 1: Identify Target Object

**AI Prompt:**
```
I want to change the ORDERS table. What will break?
```

### Step 2: Query Downstream Dependencies

**Expected Tool Usage:**
```python
query_lineage(
    object_name="ORDERS",
    direction="downstream",  # What depends on ORDERS
    depth=5                  # Look 5 levels deep
)
```

**Expected Output:**
```
ANALYTICS.PUBLIC.ORDERS
└── Downstream Consumers
    ├── CUSTOMER_ORDERS (view)
    ├── DAILY_REVENUE (view)
    │   └── WEEKLY_REVENUE (view)
    │       └── EXECUTIVE_DASHBOARD (view)
    ├── ORDER_SUMMARY (materialized view)
    └── ORDER_PROCESSING (task)
```

**Analysis:** Changing ORDERS affects 6 objects

### Step 3: Profile Affected Objects

**AI Prompt:**
```
Profile these downstream objects: CUSTOMER_ORDERS, DAILY_REVENUE, EXECUTIVE_DASHBOARD
```

**Expected Tool Usage:**
```python
profile_table(
    table_name=["CUSTOMER_ORDERS", "DAILY_REVENUE", "EXECUTIVE_DASHBOARD"]
)
```

**Result:** Understand structure of affected objects

### Step 4: Visualize Complete Impact

**AI Prompt:**
```
Build a dependency graph for the ANALYTICS database
```

**Expected Tool Usage:**
```python
build_dependency_graph(
    database="ANALYTICS",
    format="dot"  # For visualization
)
```

**Then:**
```bash
# Render with Graphviz
dot -Tpng graph.dot -o impact.png
```

### Step 5: Plan Migration

Based on impact analysis:
1. Identify all affected objects (from lineage)
2. Understand their structure (from profiling)
3. Plan update order (from dependency graph)
4. Test in dev environment first

---

## 4. Schema Documentation

**Goal:** Generate comprehensive documentation for data catalog

**Use Case:**
- Data governance requirements
- Team onboarding materials
- Knowledge base creation

### Step 1: Build Complete Catalog

**AI Prompt:**
```
Build a comprehensive catalog of the ANALYTICS database with DDL
```

**Expected Tool Usage:**
```python
build_catalog(
    database="ANALYTICS",
    include_ddl=True  # Include DDL for recreation
)
```

### Step 2: Profile All Tables

**AI Prompt:**
```
Profile all tables in ANALYTICS with AI analysis
```

**Expected Tool Usage:**
```python
# Get table list from catalog
get_catalog_summary()

# Profile all tables
profile_table(
    table_name=[list_of_tables],
    include_ai_analysis=True,
    output_format="markdown"
)
```

### Step 3: Generate Lineage Documentation

**AI Prompt:**
```
Document lineage for all reporting views
```

**Expected Tool Usage:**
```python
# For each reporting view:
query_lineage(
    object_name="REPORT_VIEW",
    direction="both",
    format="json"
)
```

### Step 4: Build Architecture Diagram

**AI Prompt:**
```
Create a dependency graph for documentation
```

**Expected Tool Usage:**
```python
build_dependency_graph(
    database="ANALYTICS",
    format="dot"
)
```

**Render:**
```bash
dot -Tsvg graph.dot -o architecture.svg
```

### Step 5: Consolidate Documentation

**Final Deliverables:**
1. **Catalog Export:** `./data_catalogue/` (JSON/JSONL)
2. **Table Documentation:** Markdown files per table
3. **Lineage Reports:** Data flow documentation
4. **Architecture Diagram:** SVG/PNG visualization

---

## 5. Lineage Investigation

**Goal:** Trace data flow to understand how data moves through your warehouse

**Use Case:**
- Debug data quality issues
- Understand report calculations
- Map data pipeline

### Scenario: "Where does this number come from?"

**AI Prompt:**
```
Where does the revenue in EXECUTIVE_DASHBOARD come from?
```

### Step 1: Trace Upstream Sources

**Expected Tool Usage:**
```python
query_lineage(
    object_name="EXECUTIVE_DASHBOARD",
    direction="upstream",
    depth=10  # Trace to raw sources
)
```

**Expected Output:**
```
EXECUTIVE_DASHBOARD
└── Upstream Sources
    └── WEEKLY_REVENUE
        └── DAILY_REVENUE
            └── CUSTOMER_ORDERS
                ├── CUSTOMERS (table - RAW SOURCE)
                └── ORDERS (table - RAW SOURCE)
                    └── ORDER_ITEMS (table - RAW SOURCE)
```

**Answer:** Revenue ultimately comes from ORDERS and ORDER_ITEMS tables

### Step 2: Understand Transformations

**AI Prompt:**
```
Show me the SQL that creates DAILY_REVENUE
```

**Expected Tool Usage:**
```python
execute_query("""
    SELECT GET_DDL('VIEW', 'DAILY_REVENUE')
""")
```

### Step 3: Profile Source Tables

**AI Prompt:**
```
Profile the ORDERS and ORDER_ITEMS tables
```

**Expected Tool Usage:**
```python
profile_table(
    table_name=["ORDERS", "ORDER_ITEMS"],
    include_ai_analysis=False  # Fast profiling
)
```

**Result:** Understand source data structure

---

## 6. Quick Table Inspection

**Goal:** Fast exploration of a single table

**Use Case:**
- Ad-hoc analysis
- Quick data checks
- Development testing

### Fast Track (30 seconds)

**AI Prompt:**
```
Show me the CUSTOMERS table
```

**Expected Tool Usage:**
```python
preview_table(table_name="CUSTOMERS", limit=10)
```

**Result:**
- 10 sample rows
- Column names and types
- Immediate feedback

### Detailed Track (2 minutes)

**AI Prompt:**
```
Give me a complete profile of the CUSTOMERS table
```

**Expected Tool Usage:**
```python
profile_table(
    table_name="CUSTOMERS",
    include_ai_analysis=True
)
```

**Result:**
- Complete schema
- Column statistics
- Business context
- PII detection

---

## Workflow Patterns

### Pattern 1: Explore → Profile → Analyze

```
1. preview_table()      # Quick look
2. profile_table()      # Detailed understanding
3. query_lineage()      # Context and relationships
```

**Use:** First-time exploration

### Pattern 2: Catalog → Batch Profile → Document

```
1. build_catalog()      # Extract metadata
2. profile_table([...]) # Batch profiling
3. Export results       # Generate documentation
```

**Use:** Data governance, documentation projects

### Pattern 3: Test → Query → Refine

```
1. test_connection()    # Verify setup
2. execute_query()      # Run query
3. Iterate              # Refine based on results
```

**Use:** Ad-hoc analysis, development

---

## Tips for Effective Workflows

### 1. Start Small, Expand as Needed

```
# Don't do this:
profile_table(table_name=[all_100_tables], include_ai_analysis=True)
# Cost: $5, Time: 30 minutes

# Do this instead:
preview_table(table_name="KEY_TABLE")  # 5 seconds
profile_table(table_name="KEY_TABLE")  # 20 seconds
# Then expand to other tables
```

### 2. Use Caching Strategically

```
# First call: Fresh analysis
profile_table(table_name="CUSTOMERS")
# Time: 20s, Cost: $0.05

# Subsequent calls: Cached
profile_table(table_name="CUSTOMERS")
# Time: <100ms, Cost: $0.00
```

Cache valid for 1 hour or until DDL changes.

### 3. Optimize for Batch Operations

```
# Instead of:
for table in tables:
    profile_table(table, include_ai_analysis=True)  # Slow

# Do:
profile_table(
    table_name=tables,
    include_ai_analysis=False  # Fast batch mode
)
```

### 4. Layer Your Analysis

```
1. High-level: get_catalog_summary()
2. Mid-level: execute_query("SELECT...")
3. Deep-dive: profile_table() with AI
```

---

## See Also

- **[MCP Quick Start](mcp_quick_start.md)** - Setup guide
- **[Tools Reference](api/TOOLS_REFERENCE.md)** - Complete tool documentation
- **[Troubleshooting](troubleshooting.md)** - Common issues
- **[Security Guide](security.md)** - Safe practices

---

**Last Updated:** 2025-10-06
**Version:** 1.10.0
**Have a workflow to share?** [Open a PR](https://github.com/Evan-Kim2028/snowcli-tools/pulls)
