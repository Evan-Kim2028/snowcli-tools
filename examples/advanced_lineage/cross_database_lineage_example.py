#!/usr/bin/env python
"""
Cross-Database Lineage Example

This example shows how to trace data dependencies across multiple databases.
Use case: You have DeFi data spread across RAW, PROCESSED, and ANALYTICS databases
and want to understand cross-database relationships and critical connection points.
"""

from pathlib import Path

from snowcli_tools.lineage import CrossDatabaseLineageBuilder


def main():
    print("Cross-Database Lineage Analysis")
    print("=" * 50)
    print()

    # Example: DeFi data spread across multiple databases
    sample_data_path = Path(__file__).parent.parent / "sample_data"
    catalog_paths = [
        sample_data_path / "catalog" / "raw_db",
        sample_data_path / "catalog" / "processed_db",
        sample_data_path / "catalog" / "analytics_db",
    ]

    print("Building cross-database lineage graph...")
    builder = CrossDatabaseLineageBuilder(catalog_paths)

    try:
        # Build unified lineage across DeFi databases
        unified_graph = builder.build_cross_db_lineage(
            include_shares=True, resolve_external_refs=True
        )

        print("Built unified graph:")
        print(f"  Databases: {len(unified_graph.databases)}")
        print(f"  Total tables/views: {len(unified_graph.nodes)}")
        print(f"  Cross-database links: {len(unified_graph.cross_db_references)}")

        # Analyze database boundaries
        boundary_analysis = builder.analyze_database_boundaries()

        print("\nDatabase Connections:")
        for db_name, analysis in list(boundary_analysis.items())[:3]:  # Show top 3
            print(f"\n  {db_name}:")
            print(f"    Internal objects: {analysis['internal_objects']}")
            print(
                f"    External dependencies: {len(analysis['external_dependencies'])}"
            )

            if analysis["external_dependencies"]:
                ext_dbs = set(
                    dep["database"] for dep in analysis["external_dependencies"]
                )
                print(f"    Connected to: {', '.join(ext_dbs)}")

        # Find critical cross-database paths
        if unified_graph.cross_db_references:
            print("\nCross-Database Data Flows:")
            for ref in unified_graph.cross_db_references[:3]:  # Show top 3
                source_db = ref.source_db.split("_")[0].upper()  # RAW, PROCESSED, etc.
                target_db = ref.target_db.split("_")[0].upper()
                print(f"  {source_db} -> {target_db}")
                print(f"    From: {ref.source_object.split('.')[-1]}")
                print(f"    To: {ref.target_object.split('.')[-1]}")

        # Identify database hubs (critical connection points)
        hubs = builder.identify_database_hubs(min_connections=2)

        if hubs:
            print("\nCritical Connection Points:")
            for hub in hubs[:3]:  # Show top 3
                print(f"  {hub['object'].split('.')[-1]}")
                print(f"    Database: {hub['database']}")
                print(f"    Connections: {hub['total_connections']}")
                print(f"    Links databases: {', '.join(hub['connected_databases'])}")

        # Database isolation analysis
        print("\nDatabase Isolation Scores:")
        for db in unified_graph.databases[:3]:  # Show top 3
            dependencies = unified_graph.get_cross_db_dependencies(db)
            isolation_score = 1.0 - (
                len(dependencies) / max(1, len(unified_graph.nodes))
            )

            status = "Well isolated" if isolation_score > 0.7 else "Highly connected"
            print(f"  {db}: {isolation_score:.1f}/10 - {status}")

    except Exception as e:
        print(f"Using mock data (catalog loading issue): {e}")
        print("\nMock DeFi Cross-Database Flow:")
        print("  RAW_DB -> PROCESSED_DB: DEX events -> Clean trades")
        print("  PROCESSED_DB -> ANALYTICS_DB: Clean trades -> USD pricing")
        print("  ANALYTICS_DB -> REPORTING_DB: USD pricing -> Daily reports")

    print("\nKey Insights:")
    print("  Cross-database lineage reveals data architecture dependencies")
    print("  Hub tables are critical points that connect multiple databases")
    print("  High isolation = good database boundaries, low coupling")
    print("  Data shares can create hidden cross-database dependencies")

    print("\nAdvanced Usage:")
    print("  Load actual catalogs from your Snowflake environments")
    print("  Analyze data share dependencies across accounts")
    print(f"  Sample setup available at: {sample_data_path}")
    print("  Export lineage graphs for architecture documentation")


if __name__ == "__main__":
    main()
