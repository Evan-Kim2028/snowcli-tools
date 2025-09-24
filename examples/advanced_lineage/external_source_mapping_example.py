#!/usr/bin/env python
"""
External Source Mapping Example

This example shows how to map external data sources like S3 buckets and stages.
Use case: You have DeFi data coming from external APIs, blockchain indexers,
and price feeds stored in S3, and want to understand these data dependencies.
"""

from pathlib import Path

from snowcli_tools.lineage import ExternalSourceMapper


def main():
    print("External Source Mapping")
    print("=" * 50)
    print()

    # Example: DeFi data sources from external systems
    sample_data_path = Path(__file__).parent.parent / "sample_data"
    catalog_path = sample_data_path / "catalog"

    # Check if catalog path exists
    if not catalog_path.exists():
        print(f"Note: Sample catalog path not found at {catalog_path}")
        print("Using mock data for demonstration")
        catalog_path = Path("/tmp/mock_catalog")  # Will trigger mock data in try/except

    print("Mapping external data sources...")
    mapper = ExternalSourceMapper(catalog_path)

    try:
        # Map external sources in DeFi pipeline
        external_lineage = mapper.map_external_sources(
            include_stages=True, include_external_tables=True, include_copy_history=True
        )

        print("Found external data sources:")
        print(f"  External tables: {len(external_lineage.external_tables)}")
        print(f"  Stages: {len(external_lineage.stages)}")
        print(f"  Unique sources: {len(external_lineage.external_sources)}")

        # Analyze data source patterns
        access_patterns = mapper.analyze_external_access_patterns()

        print("\nExternal Data Patterns:")
        if access_patterns["by_source_type"]:
            for source_type, count in list(access_patterns["by_source_type"].items())[
                :3
            ]:
                print(f"  {source_type}: {count} connections")

        if access_patterns["by_file_format"]:
            print("\nFile Formats Used:")
            for file_format, count in list(access_patterns["by_file_format"].items())[
                :3
            ]:
                print(f"  {file_format}: {count} tables")

        # Show bucket usage
        if external_lineage.bucket_summary:
            print("\nCloud Storage Buckets:")
            for bucket_name, info in list(external_lineage.bucket_summary.items())[:3]:
                print(f"  {bucket_name}")
                if "source_type" in info:
                    print(f"    Type: {info['source_type']}")
                if "tables" in info:
                    print(f"    Tables: {len(info['tables'])}")
                if "stages" in info:
                    print(f"    Stages: {len(info['stages'])}")

        # Show external table details
        if external_lineage.external_tables:
            print("\nExternal Tables Found:")
            for ext_table in external_lineage.external_tables[:2]:  # Show top 2
                table_name = ext_table.fqn().split(".")[-1]
                print(f"  {table_name}")
                print(f"    Source: {ext_table.external_source.source_type.value}")
                print(f"    Auto-refresh: {ext_table.auto_refresh}")
                if ext_table.external_source.file_format:
                    print(f"    Format: {ext_table.external_source.file_format}")

    except Exception as e:
        print(f"Using mock data (catalog loading issue): {e}")
        print("\nMock DeFi External Sources:")
        print("  S3 bucket: defi-raw-data/blockchain-events/")
        print("  External table: RAW_BLOCKCHAIN_EVENTS (Parquet)")
        print("  Stage: DEFI_STAGE -> processes JSON price feeds")
        print("  External table: COINGECKO_PRICES (CSV, auto-refresh)")

    print("\nKey Insights:")
    print("  External tables create dependencies outside your Snowflake account")
    print("  Auto-refresh tables can introduce unexpected data changes")
    print("  Stage configurations affect data loading patterns")
    print("  Multiple tables using same S3 bucket = shared dependency risk")

    print("\nAdvanced Usage:")
    print("  Monitor external source availability and performance")
    print("  Track which tables depend on each external source")
    print(f"  Sample data setup: {sample_data_path}")
    print("  Set up alerts for external source failures")


if __name__ == "__main__":
    main()
