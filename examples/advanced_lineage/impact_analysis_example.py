#!/usr/bin/env python
"""
Impact Analysis Example

This example shows how to analyze the impact of changes in your DeFi pipeline.
Use case: You want to modify the core DEX trades table and need to understand
what downstream analytics and reports might be affected.
"""

from pathlib import Path

from snowcli_tools.lineage import ChangeType, ImpactAnalyzer, LineageGraph
from snowcli_tools.lineage.graph import EdgeType, LineageEdge, LineageNode, NodeType


def main():
    print("Impact Analysis")
    print("=" * 50)
    print()

    # Create a mock DeFi lineage graph (in practice, loaded from your catalog)
    print("Building DeFi pipeline graph...")

    graph = LineageGraph()

    # Add key DeFi pipeline tables
    defi_tables = [
        ("DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS", "Raw blockchain events"),
        ("DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE", "Core processed trades"),
        ("DEFI_SAMPLE_DB.PROCESSED.COIN_INFO", "Cryptocurrency metadata"),
        (
            "DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT",
            "BTC trades with USD pricing",
        ),
        ("DEFI_SAMPLE_DB.ANALYTICS.FILTERED_DEX_TRADES_VIEW", "Analytics view"),
        ("DEFI_SAMPLE_DB.REPORTS.DAILY_VOLUME_REPORT", "Daily trading reports"),
    ]

    for table_name, description in defi_tables:
        node = LineageNode(
            key=table_name,
            node_type=NodeType.DATASET,
            attributes={"name": table_name.split(".")[-1], "description": description},
        )
        graph.add_node(node)

    # Add dependencies (who depends on whom)
    dependencies = [
        (
            "DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS",
            "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE",
        ),
        (
            "DEFI_SAMPLE_DB.PROCESSED.COIN_INFO",
            "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE",
        ),
        (
            "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE",
            "DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT",
        ),
        (
            "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE",
            "DEFI_SAMPLE_DB.ANALYTICS.FILTERED_DEX_TRADES_VIEW",
        ),
        (
            "DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT",
            "DEFI_SAMPLE_DB.REPORTS.DAILY_VOLUME_REPORT",
        ),
    ]

    for src, dst in dependencies:
        edge = LineageEdge(src=src, dst=dst, edge_type=EdgeType.DERIVES_FROM)
        graph.add_edge(edge)

    analyzer = ImpactAnalyzer(graph)
    print(f"Created pipeline with {len(graph.nodes)} tables")

    # Scenario: What happens if we modify the core DEX trades table?
    target_table = "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE"

    print(f"\nAnalyzing impact of changing: {target_table.split('.')[-1]}")

    # Analyze impact of schema change
    report = analyzer.analyze_impact(
        object_name=target_table,
        change_type=ChangeType.ALTER_SCHEMA,
        max_depth=5,
        include_upstream=False,
    )

    print("\nImpact Summary:")
    print(f"  Risk Score: {report.risk_score:.1f}/10")
    print(f"  Tables Affected: {report.total_impacted_objects}")

    if report.impacted_objects:
        print("\nObjects That Will Break:")
        for obj in report.impacted_objects[:4]:  # Show top 4
            print(f"  {obj.fqn().split('.')[-1]}")
            print(f"    Severity: {obj.severity.value}")
            print(f"    Distance: {obj.distance_from_source} hops away")

    # Calculate blast radius
    blast_radius = analyzer.calculate_blast_radius(
        object_name=target_table, max_depth=5
    )

    print("\nBlast Radius:")
    print(
        f"  Immediate impact: {blast_radius['downstream_by_distance'].get(1, []).__len__()} tables"
    )
    print(f"  Total downstream: {blast_radius['total_downstream']} objects")

    # Find critical dependencies
    spofs = analyzer.find_single_points_of_failure(min_dependent_count=1)

    if spofs:
        print("\nCritical Tables (Single Points of Failure):")
        for spof in spofs[:3]:  # Show top 3
            table_name = spof["object"].split(".")[-1]
            print(f"  {table_name}")
            print(f"    Affects {spof['downstream_count']} downstream objects")
            print(f"    Criticality: {spof['criticality_score']:.1f}/10")

    # Timing analysis with realistic DeFi refresh schedules
    refresh_schedules = {
        "DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS": 0.25,  # 15 min (real-time blockchain)
        "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE": 1.0,  # 1 hour
        "DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT": 6.0,  # 6 hours
        "DEFI_SAMPLE_DB.ANALYTICS.FILTERED_DEX_TRADES_VIEW": 0.0,  # Real-time view
        "DEFI_SAMPLE_DB.REPORTS.DAILY_VOLUME_REPORT": 24.0,  # Daily
    }

    propagation = analyzer.analyze_change_propagation_time(
        object_name=target_table, refresh_schedules=refresh_schedules
    )

    print("\nChange Propagation Timeline:")
    print(f"  Total affected: {propagation['total_affected']} objects")
    print(
        f"  Full propagation time: {propagation['max_propagation_time_hours']:.1f} hours"
    )

    # Show a few key timing details
    key_objects = [
        obj
        for obj in propagation["propagation_details"].keys()
        if "ANALYTICS" in obj or "REPORTS" in obj
    ]
    for obj in key_objects[:2]:
        details = propagation["propagation_details"][obj]
        obj_name = obj.split(".")[-1]
        print(f"  {obj_name}: {details['estimated_time_hours']:.1f} hours")

    # Show recommendations
    if report.recommendations:
        print("\nRecommendations:")
        for rec in report.recommendations[:3]:  # Show top 3
            print(f"  {rec}")

    print("\nAdvanced Usage:")
    sample_data_path = Path(__file__).parent.parent / "sample_data"
    print("  Load your actual lineage from catalog files")
    print("  Test multiple change scenarios (DROP, ALTER, etc.)")
    print(f"  Sample data pipeline: {sample_data_path}")
    print("  Set up monitoring for critical dependency changes")


if __name__ == "__main__":
    main()
