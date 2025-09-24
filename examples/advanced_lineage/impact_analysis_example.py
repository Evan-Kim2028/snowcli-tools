#!/usr/bin/env python
"""
Example: Lineage Impact Analysis

This example demonstrates how to:
1. Analyze impact of changes to database objects
2. Calculate blast radius
3. Find single points of failure
4. Generate impact reports
"""

from pathlib import Path
from snowcli_tools.lineage import (
    LineageBuilder,
    ImpactAnalyzer,
    ChangeType
)


def main():
    # Build lineage graph from catalog
    catalog_path = Path("./data_catalogue")
    builder = LineageBuilder(catalog_path)
    result = builder.build()

    # Initialize impact analyzer
    analyzer = ImpactAnalyzer(result.graph)

    print("=" * 60)
    print("Example 1: Basic Impact Analysis")
    print("=" * 60)

    # Analyze impact of dropping a table
    source_object = "STAGING.PUBLIC.RAW_CUSTOMERS"
    change_type = ChangeType.DROP

    report = analyzer.analyze_impact(
        object_name=source_object,
        change_type=change_type,
        max_depth=5,
        include_upstream=False
    )

    print(f"\nImpact Analysis for: {source_object}")
    print(f"Change Type: {change_type.value}")
    print(f"Risk Score: {report.risk_score:.2f}")
    print(f"Total Impacted Objects: {report.total_impacted_objects}")

    print("\nImpact Summary:")
    for severity, count in report.impact_summary['by_severity'].items():
        print(f"  {severity}: {count}")

    print("\nTop Impacted Objects:")
    for obj in report.impacted_objects[:5]:
        print(f"  - {obj.fqn()}")
        print(f"    Type: {obj.object_type}")
        print(f"    Severity: {obj.severity.value}")
        print(f"    Distance: {obj.distance_from_source}")
        print(f"    Impact: {obj.impact_type}")

    # Example 2: Blast radius calculation
    print("\n" + "=" * 60)
    print("Example 2: Blast Radius Analysis")
    print("=" * 60)

    blast_radius = analyzer.calculate_blast_radius(
        object_name=source_object,
        max_depth=5
    )

    print(f"\nBlast Radius for: {source_object}")
    print(f"  Total Downstream: {blast_radius['total_downstream']}")
    print(f"  Total Upstream: {blast_radius['total_upstream']}")

    print("\nDownstream by Distance:")
    for distance, objects in blast_radius['downstream_by_distance'].items():
        print(f"  Distance {distance}: {len(objects)} objects")
        for obj in objects[:3]:
            print(f"    - {obj}")

    # Example 3: Find single points of failure
    print("\n" + "=" * 60)
    print("Example 3: Single Points of Failure")
    print("=" * 60)

    spofs = analyzer.find_single_points_of_failure(min_dependent_count=3)

    print(f"\nIdentified {len(spofs)} Single Points of Failure:")
    for spof in spofs[:5]:
        print(f"\n  Object: {spof['object']}")
        print(f"  Type: {spof['object_type']}")
        print(f"  Downstream Count: {spof['downstream_count']}")
        print(f"  Criticality Score: {spof['criticality_score']:.2f}")
        print(f"  Sample Dependencies:")
        for dep in spof['downstream_objects'][:3]:
            print(f"    - {dep}")

    # Example 4: Change propagation time analysis
    print("\n" + "=" * 60)
    print("Example 4: Change Propagation Time")
    print("=" * 60)

    # Define refresh schedules (in hours)
    refresh_schedules = {
        "STAGING.PUBLIC.RAW_CUSTOMERS": 1.0,
        "ANALYTICS.PUBLIC.DIM_CUSTOMERS": 2.0,
        "ANALYTICS.PUBLIC.FACT_SALES": 4.0,
        "REPORTING.PUBLIC.CUSTOMER_SUMMARY": 6.0
    }

    propagation = analyzer.analyze_change_propagation_time(
        object_name=source_object,
        refresh_schedules=refresh_schedules
    )

    print(f"\nChange Propagation Analysis for: {source_object}")
    print(f"  Total Affected: {propagation['total_affected']}")
    print(f"  Max Propagation Time: {propagation['max_propagation_time_hours']:.1f} hours")

    print("\nPropagation Timeline:")
    for obj, details in list(propagation['propagation_details'].items())[:5]:
        print(f"  {obj}:")
        print(f"    Time: {details['estimated_time_hours']:.1f} hours")
        print(f"    Path Length: {details['path_length']} hops")

    # Example 5: Multiple change scenarios
    print("\n" + "=" * 60)
    print("Example 5: Multiple Change Scenarios")
    print("=" * 60)

    scenarios = [
        ("STAGING.PUBLIC.RAW_CUSTOMERS", ChangeType.DROP),
        ("ANALYTICS.PUBLIC.DIM_CUSTOMERS", ChangeType.ALTER_SCHEMA),
        ("ANALYTICS.PUBLIC.FACT_SALES", ChangeType.DROP_COLUMN),
        ("REPORTING.PUBLIC.CUSTOMER_SUMMARY", ChangeType.MODIFY_LOGIC)
    ]

    heatmap = analyzer.generate_impact_heatmap(scenarios)

    print("\nImpact Heatmap:")
    for object_name, impact in heatmap.items():
        print(f"\n  {object_name}:")
        print(f"    Change: {impact['change_type']}")
        print(f"    Risk Score: {impact['risk_score']:.2f}")
        print(f"    Total Impacted: {impact['total_impacted']}")
        print(f"    Critical Count: {impact['critical_count']}")

    # Example 6: Circular dependency detection
    print("\n" + "=" * 60)
    print("Example 6: Circular Dependencies")
    print("=" * 60)

    cycles = analyzer.identify_circular_dependencies()

    if cycles:
        print(f"\n⚠️ Found {len(cycles)} circular dependencies:")
        for i, cycle in enumerate(cycles[:3], 1):
            print(f"\n  Cycle {i}:")
            for obj in cycle:
                print(f"    -> {obj}")
            print(f"    -> {cycle[0]} (circular)")
    else:
        print("\n✓ No circular dependencies detected")

    # Example 7: Critical path analysis
    print("\n" + "=" * 60)
    print("Example 7: Critical Path Analysis")
    print("=" * 60)

    if report.critical_paths:
        print(f"\nCritical Paths from {source_object}:")
        for path in report.critical_paths[:3]:
            print(f"\n  To: {path.target_object}")
            print(f"  Path Length: {path.path_length}")
            print(f"  Path: {' -> '.join(path.path[:5])}")
            if path.critical_nodes:
                print(f"  Critical Nodes: {', '.join(path.critical_nodes)}")
            if path.bottlenecks:
                print(f"  Bottlenecks: {', '.join(path.bottlenecks)}")

    # Example 8: Recommendations
    print("\n" + "=" * 60)
    print("Example 8: Impact Mitigation Recommendations")
    print("=" * 60)

    print("\nRecommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")

    # Example 9: Notification list
    print("\n" + "=" * 60)
    print("Example 9: Notification List")
    print("=" * 60)

    if report.notification_list:
        print("\nUsers to Notify:")
        for notification in report.notification_list[:5]:
            print(f"  User: {notification['user']}")
            print(f"  Severity: {notification['severity']}")
            print(f"  Object: {notification['object']}")
            print(f"  Impact: {notification['impact_type']}")
    else:
        print("\nNo notifications required")

    # Example 10: Export impact report
    print("\n" + "=" * 60)
    print("Example 10: Exporting Impact Report")
    print("=" * 60)

    # Export as HTML
    html_path = analyzer.export_impact_report(
        report,
        Path("./impact_report.html"),
        format="html"
    )
    print(f"\nExported to HTML: {html_path}")

    # Export as JSON
    json_path = analyzer.export_impact_report(
        report,
        Path("./impact_report.json"),
        format="json"
    )
    print(f"Exported to JSON: {json_path}")

    # Export as Markdown
    md_path = analyzer.export_impact_report(
        report,
        Path("./impact_report.md"),
        format="markdown"
    )
    print(f"Exported to Markdown: {md_path}")


if __name__ == "__main__":
    main()