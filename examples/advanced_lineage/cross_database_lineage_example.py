#!/usr/bin/env python
"""
Example: Cross-Database Lineage Analysis

This example demonstrates how to:
1. Build unified lineage across multiple databases
2. Identify cross-database dependencies
3. Find database hubs and critical paths
4. Export unified lineage graphs
"""

from pathlib import Path
from snowcli_tools.lineage import CrossDatabaseLineageBuilder


def main():
    # Assume we have catalogs from multiple databases
    catalog_paths = [
        Path("./data_catalogue/staging_db"),
        Path("./data_catalogue/analytics_db"),
        Path("./data_catalogue/reporting_db")
    ]

    print("=" * 60)
    print("Example 1: Building Cross-Database Lineage")
    print("=" * 60)

    builder = CrossDatabaseLineageBuilder(catalog_paths)

    # Build the unified lineage graph
    unified_graph = builder.build_cross_db_lineage(
        include_shares=True,
        resolve_external_refs=True
    )

    print(f"\nUnified Lineage Graph:")
    print(f"  Databases: {', '.join(unified_graph.databases)}")
    print(f"  Total Nodes: {len(unified_graph.nodes)}")
    print(f"  Total Edges: {len(unified_graph.edges)}")
    print(f"  Cross-DB References: {len(unified_graph.cross_db_references)}")

    # Example 2: Analyze database boundaries
    print("\n" + "=" * 60)
    print("Example 2: Database Boundary Analysis")
    print("=" * 60)

    boundary_analysis = builder.analyze_database_boundaries()

    for db_name, analysis in boundary_analysis.items():
        print(f"\nDatabase: {db_name}")
        print(f"  Internal Objects: {analysis['internal_objects']}")
        print(f"  External Dependencies: {len(analysis['external_dependencies'])}")
        print(f"  External Dependents: {len(analysis['external_dependents'])}")

        if analysis['external_dependencies']:
            print("  Sample External Dependencies:")
            for dep in analysis['external_dependencies'][:3]:
                print(f"    - {dep['target']} ({dep['database']})")

    # Example 3: Find cross-database paths
    print("\n" + "=" * 60)
    print("Example 3: Cross-Database Data Flow Paths")
    print("=" * 60)

    # Find paths between objects in different databases
    source_object = "STAGING_DB::PUBLIC.RAW_DATA.CUSTOMERS"
    target_object = "REPORTING_DB::PUBLIC.REPORTS.CUSTOMER_SUMMARY"

    paths = builder.find_cross_db_paths(
        source_object,
        target_object,
        max_depth=10
    )

    print(f"\nPaths from {source_object} to {target_object}:")
    print(f"Found {len(paths)} paths")

    for i, path in enumerate(paths[:3], 1):
        print(f"\n  Path {i} (length: {len(path)}):")
        for step in path:
            db = step.split("::")[0] if "::" in step else "UNKNOWN"
            obj = step.split("::")[-1] if "::" in step else step
            print(f"    [{db}] {obj}")

    # Example 4: Identify database hubs
    print("\n" + "=" * 60)
    print("Example 4: Database Hub Analysis")
    print("=" * 60)

    hubs = builder.identify_database_hubs(min_connections=5)

    print(f"\nTop Database Hubs (objects connecting multiple databases):")
    for hub in hubs[:5]:
        print(f"\n  Object: {hub['object']}")
        print(f"  Database: {hub['database']}")
        print(f"  Total Connections: {hub['total_connections']}")
        print(f"  In-degree: {hub['in_degree']}, Out-degree: {hub['out_degree']}")
        print(f"  Connected Databases: {', '.join(hub['connected_databases'])}")

    # Example 5: Cross-database references analysis
    print("\n" + "=" * 60)
    print("Example 5: Cross-Database References")
    print("=" * 60)

    for ref in unified_graph.cross_db_references[:5]:
        print(f"\n  Source: {ref.source_object}")
        print(f"    Database: {ref.source_db}")
        print(f"  Target: {ref.target_object}")
        print(f"    Database: {ref.target_db}")
        print(f"  Type: {ref.reference_type}")
        if ref.is_data_share:
            print(f"  Data Share: {ref.share_name}")

    # Example 6: Data share analysis
    print("\n" + "=" * 60)
    print("Example 6: Data Share Analysis")
    print("=" * 60)

    if unified_graph.shares:
        print(f"\nData Shares: {len(unified_graph.shares)}")
        for share_name, share_info in unified_graph.shares.items():
            print(f"\n  Share: {share_name}")
            print(f"  Provider: {share_info['provider_database']}")
            print(f"  Shared Objects: {len(share_info['shared_objects'])}")
            for obj in share_info['shared_objects'][:3]:
                print(f"    - {obj['object']} ({obj['type']})")

    # Example 7: Export unified lineage
    print("\n" + "=" * 60)
    print("Example 7: Exporting Unified Lineage")
    print("=" * 60)

    # Export as JSON
    json_path = builder.export_unified_lineage(
        Path("./unified_lineage.json"),
        format="json"
    )
    print(f"\nExported to JSON: {json_path}")

    # Export as DOT graph for visualization
    dot_path = builder.export_unified_lineage(
        Path("./unified_lineage.dot"),
        format="dot"
    )
    print(f"Exported to DOT: {dot_path}")

    # Export as GraphML for network analysis tools
    graphml_path = builder.export_unified_lineage(
        Path("./unified_lineage.graphml"),
        format="graphml"
    )
    print(f"Exported to GraphML: {graphml_path}")

    # Example 8: Database isolation analysis
    print("\n" + "=" * 60)
    print("Example 8: Database Isolation Analysis")
    print("=" * 60)

    for db in unified_graph.databases:
        dependencies = unified_graph.get_cross_db_dependencies(db)

        incoming = [d for d in dependencies if d.target_db == db]
        outgoing = [d for d in dependencies if d.source_db == db]

        print(f"\n{db}:")
        print(f"  Incoming dependencies: {len(incoming)}")
        print(f"  Outgoing dependencies: {len(outgoing)}")

        isolation_score = 1.0 - (len(dependencies) / max(1, len(unified_graph.nodes)))
        print(f"  Isolation score: {isolation_score:.2f}")

        if isolation_score < 0.5:
            print(f"  ⚠️ Low isolation - highly interconnected")
        elif isolation_score > 0.8:
            print(f"  ✓ High isolation - loosely coupled")
        else:
            print(f"  ℹ️ Moderate isolation")


if __name__ == "__main__":
    main()