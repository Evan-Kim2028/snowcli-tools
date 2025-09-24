#!/usr/bin/env python
"""
Example: External Data Source Mapping

This example demonstrates how to:
1. Map external data sources (S3, Azure, GCS)
2. Track external table dependencies
3. Analyze stage configurations
4. Export external lineage mappings
"""

from pathlib import Path
from snowcli_tools.lineage import ExternalSourceMapper


def main():
    # Initialize the external source mapper
    catalog_path = Path("./data_catalogue")
    mapper = ExternalSourceMapper(catalog_path)

    print("=" * 60)
    print("Example 1: Mapping External Sources")
    print("=" * 60)

    # Map all external sources
    external_lineage = mapper.map_external_sources(
        include_stages=True,
        include_external_tables=True,
        include_copy_history=True
    )

    print(f"\nExternal Source Mapping Summary:")
    print(f"  Unique External Sources: {len(external_lineage.external_sources)}")
    print(f"  External Tables: {len(external_lineage.external_tables)}")
    print(f"  Stages: {len(external_lineage.stages)}")
    print(f"  Data Flow Paths: {len(external_lineage.data_flow_paths)}")

    # Example 2: Analyze external sources by type
    print("\n" + "=" * 60)
    print("Example 2: External Source Analysis")
    print("=" * 60)

    access_patterns = mapper.analyze_external_access_patterns()

    print("\nExternal Access Patterns:")
    print(f"  Total External Tables: {access_patterns['external_table_count']}")
    print(f"  Total Stages: {access_patterns['stage_count']}")
    print(f"  Unique Sources: {access_patterns['unique_sources']}")

    print("\nBy Source Type:")
    for source_type, count in access_patterns['by_source_type'].items():
        print(f"  {source_type}: {count}")

    print("\nBy File Format:")
    for file_format, count in access_patterns['by_file_format'].items():
        print(f"  {file_format}: {count}")

    # Example 3: Bucket analysis
    print("\n" + "=" * 60)
    print("Example 3: Cloud Storage Bucket Analysis")
    print("=" * 60)

    print("\nBucket Usage Summary:")
    for bucket_name, info in external_lineage.bucket_summary.items():
        print(f"\n  Bucket: {bucket_name}")
        print(f"  Type: {info['source_type']}")
        print(f"  Total References: {info['total_references']}")
        print(f"  Tables using this bucket: {len(info['tables'])}")
        print(f"  Stages using this bucket: {len(info['stages'])}")

        if info['tables']:
            print(f"  Sample tables:")
            for table in info['tables'][:3]:
                print(f"    - {table}")

    # Example 4: External table mappings
    print("\n" + "=" * 60)
    print("Example 4: External Table Analysis")
    print("=" * 60)

    for ext_table in external_lineage.external_tables[:3]:
        print(f"\nExternal Table: {ext_table.fqn()}")
        print(f"  Source Type: {ext_table.external_source.source_type.value}")
        print(f"  Location: {ext_table.external_source.location}")

        if ext_table.external_source.file_pattern:
            print(f"  File Pattern: {ext_table.external_source.file_pattern}")
        if ext_table.external_source.file_format:
            print(f"  File Format: {ext_table.external_source.file_format}")

        print(f"  Auto Refresh: {ext_table.auto_refresh}")

        if ext_table.partition_columns:
            print(f"  Partition Columns: {', '.join(ext_table.partition_columns)}")

    # Example 5: Stage configurations
    print("\n" + "=" * 60)
    print("Example 5: Stage Configuration Analysis")
    print("=" * 60)

    for stage in external_lineage.stages[:3]:
        print(f"\nStage: {stage.fqn()}")
        print(f"  Source Type: {stage.external_source.source_type.value}")
        print(f"  Location: {stage.external_source.location}")

        if stage.external_source.credentials:
            print(f"  Has Credentials: Yes")
        if stage.external_source.encryption:
            print(f"  Has Encryption: Yes")

        if stage.copy_operations:
            print(f"  Copy Operations: {len(stage.copy_operations)}")
            for op in stage.copy_operations[:2]:
                print(f"    - {op['source_location']} -> {op['target_table']}")

        if stage.pipes:
            print(f"  Connected Pipes: {len(stage.pipes)}")

    # Example 6: Find dependencies for specific object
    print("\n" + "=" * 60)
    print("Example 6: External Dependencies for Objects")
    print("=" * 60)

    test_object = "ANALYTICS.PUBLIC.FACT_SALES"
    dependencies = mapper.find_external_dependencies(test_object)

    if dependencies:
        print(f"\nExternal dependencies for {test_object}:")
        for dep in dependencies:
            print(f"  - Type: {dep.source_type.value}")
            print(f"    Location: {dep.location}")
            if dep.stage_name:
                print(f"    Stage: {dep.stage_name}")
    else:
        print(f"\nNo external dependencies found for {test_object}")

    # Example 7: Data flow paths
    print("\n" + "=" * 60)
    print("Example 7: Data Flow Path Analysis")
    print("=" * 60)

    print("\nTop Data Flow Paths:")
    for path in external_lineage.data_flow_paths[:5]:
        print(f"\n  Source: {path['source']}")
        print(f"  Type: {path['source_type']}")
        print(f"  Flow: {path['flow_type']}")
        print(f"  Targets: {len(path['targets'])} tables")
        for target in path['targets'][:3]:
            print(f"    - {target}")

    # Example 8: Find tables using specific source
    print("\n" + "=" * 60)
    print("Example 8: Tables Using Specific Source")
    print("=" * 60)

    test_source = "s3://data-lake/raw/customers/"
    tables = mapper.get_tables_from_source(test_source)

    if tables:
        print(f"\nTables using {test_source}:")
        for table in tables:
            print(f"  - {table}")
    else:
        print(f"\nNo tables found using {test_source}")

    # Example 9: Export external mappings
    print("\n" + "=" * 60)
    print("Example 9: Exporting External Mappings")
    print("=" * 60)

    # Export as JSON
    json_path = mapper.export_external_mappings(
        Path("./external_mappings.json"),
        format="json"
    )
    print(f"\nExported to JSON: {json_path}")

    # Export as Markdown report
    md_path = mapper.export_external_mappings(
        Path("./external_mappings.md"),
        format="markdown"
    )
    print(f"Exported to Markdown: {md_path}")

    # Export as DOT graph
    dot_path = mapper.export_external_mappings(
        Path("./external_mappings.dot"),
        format="dot"
    )
    print(f"Exported to DOT: {dot_path}")

    # Example 10: Security analysis
    print("\n" + "=" * 60)
    print("Example 10: External Source Security Analysis")
    print("=" * 60)

    secured_sources = 0
    unsecured_sources = 0

    for source in external_lineage.external_sources.values():
        if source.encryption or source.credentials:
            secured_sources += 1
        else:
            unsecured_sources += 1

    print(f"\nSecurity Summary:")
    print(f"  Secured sources: {secured_sources}")
    print(f"  Unsecured sources: {unsecured_sources}")

    if unsecured_sources > 0:
        print(f"\n  ⚠️ Warning: {unsecured_sources} sources without explicit security")


if __name__ == "__main__":
    main()