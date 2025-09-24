# Advanced Lineage Features Documentation

## Overview

The Advanced Lineage features in snowcli-tools extend the existing lineage functionality with powerful capabilities for understanding, tracking, and analyzing data flow in your Snowflake environment. These features are fully backward compatible additions to the core lineage functionality.

## Table of Contents

1. [Column-Level Lineage](#column-level-lineage)
2. [Transformation Tracking](#transformation-tracking)
3. [Cross-Database Lineage](#cross-database-lineage)
4. [External Data Source Integration](#external-data-source-integration)
5. [Impact Analysis](#impact-analysis)
6. [Time-Travel Lineage](#time-travel-lineage)

---

## Column-Level Lineage

Track data flow at the column granularity to understand exactly how individual fields are transformed and propagated through your data pipeline.

### Key Features

- Parse SQL to extract column-level dependencies
- Track transformations (functions, aggregations, joins)
- Map source columns to target columns
- Calculate transformation confidence scores

### Usage

```python
from snowcli_tools.lineage import ColumnLineageExtractor

# Initialize the extractor
extractor = ColumnLineageExtractor(
    default_database="ANALYTICS",
    default_schema="PUBLIC"
)

# Extract column lineage from SQL
sql = """
CREATE VIEW customer_summary AS
SELECT
    c.customer_id,
    UPPER(c.customer_name) as name,
    SUM(o.order_total) as total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
"""

lineage = extractor.extract_column_lineage(sql, target_table="customer_summary")

# Analyze transformations
for trans in lineage.transformations:
    print(f"Target: {trans.target_column.fqn()}")
    print(f"Sources: {[col.fqn() for col in trans.source_columns]}")
    print(f"Type: {trans.transformation_type.value}")
```

### Transformation Types

- **DIRECT**: Direct column mapping
- **ALIAS**: Column aliasing
- **FUNCTION**: Function application
- **AGGREGATE**: Aggregation functions
- **CASE**: Conditional logic
- **WINDOW**: Window functions
- **JOIN**: Join operations
- **SUBQUERY**: Subquery results

### CLI Commands

```bash
# Extract column lineage
snowflake-cli lineage column PIPELINE.RAW.USERS.EMAIL \
    --show-transformations --depth 3

# Show column dependencies
snowflake-cli lineage columns --table ANALYTICS.FACT_SALES \
    --output column_lineage.json
```

---

## Transformation Tracking

Capture and analyze data transformations to understand how data is processed throughout your pipeline.

### Key Features

- Track transformation history
- Categorize transformations (cleansing, enrichment, aggregation)
- Identify transformation patterns
- Build transformation chains
- Estimate performance impact

### Usage

```python
from snowcli_tools.lineage import TransformationTracker

# Initialize tracker
tracker = TransformationTracker(storage_path=Path("./transformations"))

# Track a transformation
metadata = tracker.track_transformation(
    transformation=column_transformation,
    source_object="RAW.CUSTOMERS",
    target_object="CLEAN.CUSTOMERS",
    business_logic="Customer data standardization"
)

# Analyze patterns
patterns = tracker.analyze_patterns(min_frequency=2)

# Find transformation chains
chains = tracker.find_transformation_chains(
    start_column="RAW.source_field",
    end_column="FINAL.target_field"
)

# Export transformation history
tracker.export_transformations(
    Path("./transformation_report.json"),
    format="json"
)
```

### Transformation Categories

- **DATA_TYPE**: Type conversions
- **CLEANSING**: Data cleaning operations
- **ENRICHMENT**: Data enrichment
- **AGGREGATION**: Aggregation operations
- **FILTERING**: Filtering logic
- **JOINING**: Join operations
- **CALCULATION**: Calculations
- **VALIDATION**: Validation rules

### Performance Impact Scoring

Each transformation is scored based on:
- Transformation type complexity
- Number of source columns
- Function complexity
- Estimated computational cost

---

## Cross-Database Lineage

Build unified lineage graphs across multiple Snowflake databases to understand data flow across database boundaries.

### Key Features

- Merge lineage from multiple databases
- Identify cross-database references
- Detect data sharing patterns
- Find database hubs
- Analyze database isolation

### Usage

```python
from snowcli_tools.lineage import CrossDatabaseLineageBuilder

# Initialize with multiple catalogs
builder = CrossDatabaseLineageBuilder([
    Path("./catalog/staging_db"),
    Path("./catalog/analytics_db"),
    Path("./catalog/reporting_db")
])

# Build unified lineage
unified = builder.build_cross_db_lineage(
    include_shares=True,
    resolve_external_refs=True
)

# Analyze database boundaries
analysis = builder.analyze_database_boundaries()

# Find cross-database paths
paths = builder.find_cross_db_paths(
    "STAGING::RAW.CUSTOMERS",
    "REPORTING::SUMMARY.CUSTOMERS"
)

# Identify hub objects
hubs = builder.identify_database_hubs(min_connections=5)

# Export unified lineage
builder.export_unified_lineage(
    Path("./unified_lineage.json"),
    format="json"
)
```

### Cross-Database Analysis

- **Boundary Analysis**: Understand dependencies between databases
- **Hub Detection**: Find objects connecting multiple databases
- **Path Finding**: Trace data flow across databases
- **Isolation Scoring**: Measure database coupling

### CLI Commands

```bash
# Build cross-database lineage
snowflake-cli lineage build --databases DB1,DB2,DB3 \
    --output ./unified_lineage

# Analyze cross-database dependencies
snowflake-cli lineage cross-db --analyze-boundaries \
    --output ./db_analysis.json
```

---

## External Data Source Integration

Map and track external data sources including cloud storage (S3, Azure, GCS) and stages.

### Key Features

- Map external tables to sources
- Track stage configurations
- Analyze bucket usage
- Trace data flow from external sources
- Security analysis

### Usage

```python
from snowcli_tools.lineage import ExternalSourceMapper

# Initialize mapper
mapper = ExternalSourceMapper(catalog_path=Path("./catalog"))

# Map external sources
external_lineage = mapper.map_external_sources(
    include_stages=True,
    include_external_tables=True,
    include_copy_history=True
)

# Find external dependencies
dependencies = mapper.find_external_dependencies("ANALYTICS.FACT_SALES")

# Get tables using specific source
tables = mapper.get_tables_from_source("s3://data-lake/raw/")

# Analyze access patterns
patterns = mapper.analyze_external_access_patterns()

# Export mappings
mapper.export_external_mappings(
    Path("./external_mappings.json"),
    format="json"
)
```

### External Source Types

- **S3**: Amazon S3 buckets
- **AZURE_BLOB**: Azure Blob Storage
- **GCS**: Google Cloud Storage
- **SNOWFLAKE_STAGE**: Internal stages
- **HTTP**: HTTP/HTTPS endpoints

### Security Analysis

- Identify secured vs unsecured sources
- Track encryption settings
- Monitor credential usage
- Audit external access patterns

### CLI Commands

```bash
# Map external sources
snowflake-cli lineage external --include-stages \
    --map-s3-buckets --output ./external_map.json

# Find external dependencies
snowflake-cli lineage external-deps TABLE_NAME \
    --show-stages --show-buckets
```

---

## Impact Analysis

Analyze the potential impact of changes to database objects before making them.

### Key Features

- Calculate blast radius
- Identify affected objects
- Determine impact severity
- Find single points of failure
- Generate recommendations
- Build notification lists

### Usage

```python
from snowcli_tools.lineage import ImpactAnalyzer, ChangeType

# Initialize analyzer
analyzer = ImpactAnalyzer(lineage_graph)

# Analyze impact
report = analyzer.analyze_impact(
    object_name="STAGING.RAW_CUSTOMERS",
    change_type=ChangeType.DROP,
    max_depth=5
)

# Calculate blast radius
blast_radius = analyzer.calculate_blast_radius(
    object_name="ANALYTICS.DIM_CUSTOMERS",
    max_depth=5
)

# Find single points of failure
spofs = analyzer.find_single_points_of_failure(min_dependent_count=3)

# Analyze propagation time
propagation = analyzer.analyze_change_propagation_time(
    object_name="RAW.SOURCE_TABLE",
    refresh_schedules={"TABLE1": 1.0, "TABLE2": 2.0}
)

# Export report
analyzer.export_impact_report(
    report,
    Path("./impact_report.html"),
    format="html"
)
```

### Change Types

- **DROP**: Object deletion
- **ALTER_SCHEMA**: Schema changes
- **ALTER_DATA_TYPE**: Data type changes
- **DROP_COLUMN**: Column removal
- **RENAME**: Object renaming
- **MODIFY_LOGIC**: Logic changes
- **PERMISSION_CHANGE**: Access changes

### Impact Severity Levels

- **CRITICAL**: Direct failure, data loss
- **HIGH**: Schema mismatches, missing columns
- **MEDIUM**: Logic changes, broken references
- **LOW**: Indirect impacts
- **INFO**: Informational only

### CLI Commands

```bash
# Analyze impact
snowflake-cli lineage impact PIPELINE.RAW.CRITICAL_TABLE \
    --change-type DROP --output ./impact_report.html

# Find single points of failure
snowflake-cli lineage spof --min-dependents 5 \
    --output ./critical_objects.json

# Calculate blast radius
snowflake-cli lineage blast-radius TABLE_NAME \
    --max-depth 5 --show-paths
```

---

## Time-Travel Lineage

Track lineage evolution over time with snapshot and comparison capabilities.

### Key Features

- Capture lineage snapshots
- Compare lineage between points in time
- Track object evolution
- Detect patterns and trends
- Rollback to previous states

### Usage

```python
from snowcli_tools.lineage import LineageHistoryManager

# Initialize manager
manager = LineageHistoryManager(storage_path=Path("./history"))

# Capture snapshot
snapshot = manager.capture_snapshot(
    catalog_path=Path("./catalog"),
    tag="v1.0.0",
    description="Initial release"
)

# List snapshots
snapshots = manager.list_snapshots(tags_only=True)

# Compare snapshots
diff = manager.compare_lineage("v1.0.0", "v1.1.0")

# Track object evolution
evolution = manager.track_object_evolution(
    object_key="ANALYTICS.DIM_CUSTOMERS",
    start_date=datetime(2024, 1, 1)
)

# Find patterns
patterns = manager.find_lineage_patterns(min_snapshots=5)

# Create timeline
timeline = manager.create_timeline_visualization()

# Rollback to snapshot
manager.rollback_to_snapshot("v1.0.0", Path("./rollback.json"))

# Export history
manager.export_history(Path("./history.json"), format="json")
```

### Snapshot Management

- Tag important versions
- Add descriptions
- Filter by date range
- Compare any two snapshots

### Evolution Tracking

- Object change history
- Dependency evolution
- Schema changes over time
- Change frequency analysis

### Pattern Detection

- Growth rates
- Volatile objects
- Stable core identification
- Seasonal patterns

### CLI Commands

```bash
# Capture snapshot
snowflake-cli lineage snapshot --tag "v2.0-release" \
    --description "Major release"

# Compare versions
snowflake-cli lineage diff --from "v1.0" --to "v2.0" \
    --output ./lineage_diff.json

# Track object history
snowflake-cli lineage history OBJECT_NAME \
    --days 30 --show-evolution

# Export timeline
snowflake-cli lineage timeline --days 90 \
    --output ./timeline.html
```

---

## Integration Examples

### Complete Pipeline Analysis

```python
# 1. Build cross-database lineage
cross_db = CrossDatabaseLineageBuilder(catalog_paths)
unified = cross_db.build_cross_db_lineage()

# 2. Extract column-level details
col_extractor = ColumnLineageExtractor()
for sql in view_definitions:
    col_lineage = col_extractor.extract_column_lineage(sql)

# 3. Track transformations
tracker = TransformationTracker()
for trans in col_lineage.transformations:
    tracker.track_transformation(trans, source, target)

# 4. Map external sources
external_mapper = ExternalSourceMapper(catalog_path)
external = external_mapper.map_external_sources()

# 5. Analyze impact
analyzer = ImpactAnalyzer(unified.build_networkx_graph())
impact = analyzer.analyze_impact("CRITICAL_TABLE", ChangeType.DROP)

# 6. Capture snapshot
history = LineageHistoryManager()
snapshot = history.capture_snapshot(catalog_path, tag="analysis_complete")
```

### Automated Monitoring

```python
import schedule
import time

def daily_lineage_check():
    # Capture daily snapshot
    manager = LineageHistoryManager()
    snapshot = manager.capture_snapshot(
        catalog_path,
        tag=f"daily_{datetime.now().strftime('%Y%m%d')}"
    )

    # Compare with yesterday
    yesterday = f"daily_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}"
    diff = manager.compare_lineage(yesterday, snapshot.tag)

    # Alert on significant changes
    if diff and diff.summary['total_changes'] > 10:
        send_alert(f"Significant lineage changes: {diff.summary}")

    # Check for new SPOFs
    analyzer = ImpactAnalyzer(get_current_graph())
    spofs = analyzer.find_single_points_of_failure()
    if len(spofs) > previous_spof_count:
        send_alert(f"New single points of failure detected: {spofs}")

# Schedule daily check
schedule.every().day.at("06:00").do(daily_lineage_check)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Best Practices

### 1. Regular Snapshots
- Capture snapshots before major changes
- Tag important versions
- Maintain snapshot descriptions

### 2. Impact Analysis Before Changes
- Always run impact analysis for schema changes
- Review critical paths
- Check blast radius

### 3. Monitor External Dependencies
- Regularly audit external sources
- Check for unsecured access
- Monitor bucket usage

### 4. Cross-Database Optimization
- Minimize cross-database dependencies
- Identify and optimize hub objects
- Monitor database isolation scores

### 5. Transformation Documentation
- Track business logic in transformations
- Document complex transformation chains
- Monitor performance impacts

---

## Performance Considerations

### Large Catalog Processing
- Use incremental updates when possible
- Cache parsed SQL results
- Process in parallel where applicable

### Memory Management
- Stream large result sets
- Use pagination for large graphs
- Clean up old snapshots periodically

### Storage Optimization
- Compress historical snapshots
- Archive old transformation logs
- Use appropriate storage formats

---

## Troubleshooting

### Common Issues

**Issue**: Column lineage extraction fails
- **Solution**: Check SQL syntax, ensure sqlglot supports the dialect

**Issue**: Cross-database references not resolved
- **Solution**: Ensure all database catalogs are included

**Issue**: Impact analysis takes too long
- **Solution**: Reduce max_depth parameter, use sampling

**Issue**: Snapshot storage growing large
- **Solution**: Archive old snapshots, use compression

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your lineage operations
```

---

## Backward Compatibility

All existing lineage functionality remains unchanged. The new advanced features are additive and can be adopted incrementally:

- Existing `LineageBuilder` and `LineageGraph` APIs work as before
- New features are imported separately when needed
- No changes required to existing code
- New features integrate seamlessly with existing lineage graphs

---

## API Reference

For detailed API documentation, see:
- [Column Lineage API](./api/column_lineage.md)
- [Transformation Tracking API](./api/transformations.md)
- [Cross-Database API](./api/cross_database.md)
- [External Sources API](./api/external_sources.md)
- [Impact Analysis API](./api/impact_analysis.md)
- [Time-Travel API](./api/time_travel.md)

---

## Support

For issues and questions:
- GitHub Issues: [snowcli-tools/issues](https://github.com/your-repo/issues)
- Documentation: [Advanced Lineage Docs](https://docs.snowcli-tools.io/lineage)
- Examples: See `/examples/advanced_lineage/` directory