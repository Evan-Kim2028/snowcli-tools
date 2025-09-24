#!/usr/bin/env python
"""
Example: Time-Travel Lineage Analysis

This example demonstrates how to:
1. Capture lineage snapshots over time
2. Compare lineage between different points in time
3. Track object evolution
4. Analyze lineage patterns and trends
"""

from pathlib import Path
from datetime import datetime, timedelta
from snowcli_tools.lineage import LineageHistoryManager


def main():
    # Initialize the lineage history manager
    history_manager = LineageHistoryManager(storage_path=Path("./lineage_history"))

    print("=" * 60)
    print("Example 1: Capturing Lineage Snapshots")
    print("=" * 60)

    # Capture initial snapshot
    catalog_path = Path("./data_catalogue")

    snapshot1 = history_manager.capture_snapshot(
        catalog_path=catalog_path,
        tag="v1.0.0",
        description="Initial production release"
    )

    print(f"\nCaptured Snapshot:")
    print(f"  ID: {snapshot1.snapshot_id}")
    print(f"  Tag: {snapshot1.tag}")
    print(f"  Timestamp: {snapshot1.timestamp}")
    print(f"  Nodes: {snapshot1.node_count}")
    print(f"  Edges: {snapshot1.edge_count}")
    print(f"  Graph Hash: {snapshot1.graph_hash[:16]}...")

    # Simulate changes and capture another snapshot
    snapshot2 = history_manager.capture_snapshot(
        catalog_path=catalog_path,
        tag="v1.1.0",
        description="Added new analytics tables"
    )

    print(f"\nCaptured Second Snapshot:")
    print(f"  ID: {snapshot2.snapshot_id}")
    print(f"  Tag: {snapshot2.tag}")

    # Example 2: List snapshots
    print("\n" + "=" * 60)
    print("Example 2: Listing Snapshots")
    print("=" * 60)

    all_snapshots = history_manager.list_snapshots()

    print(f"\nTotal Snapshots: {len(all_snapshots)}")
    for snap in all_snapshots[:5]:
        print(f"\n  Timestamp: {snap.timestamp}")
        print(f"  Tag: {snap.tag or 'untagged'}")
        print(f"  Nodes: {snap.node_count}, Edges: {snap.edge_count}")
        if snap.description:
            print(f"  Description: {snap.description}")

    # List only tagged snapshots
    tagged_snapshots = history_manager.list_snapshots(tags_only=True)
    print(f"\nTagged Snapshots: {len(tagged_snapshots)}")
    for snap in tagged_snapshots:
        print(f"  - {snap.tag}: {snap.description}")

    # Example 3: Compare lineage between snapshots
    print("\n" + "=" * 60)
    print("Example 3: Comparing Lineage Snapshots")
    print("=" * 60)

    diff = history_manager.compare_lineage("v1.0.0", "v1.1.0")

    if diff:
        print(f"\nLineage Diff (v1.0.0 -> v1.1.0):")
        print(f"  Total Changes: {diff.summary['total_changes']}")

        print("\n  Node Changes:")
        print(f"    Added: {diff.summary['nodes']['added']}")
        print(f"    Removed: {diff.summary['nodes']['removed']}")
        print(f"    Modified: {diff.summary['nodes']['modified']}")

        print("\n  Edge Changes:")
        print(f"    Added: {diff.summary['edges']['added']}")
        print(f"    Removed: {diff.summary['edges']['removed']}")

        if diff.added_nodes:
            print("\n  New Objects:")
            for node in diff.added_nodes[:5]:
                print(f"    + {node}")

        if diff.removed_nodes:
            print("\n  Removed Objects:")
            for node in diff.removed_nodes[:5]:
                print(f"    - {node}")

        if diff.modified_nodes:
            print("\n  Modified Objects:")
            for mod in diff.modified_nodes[:3]:
                print(f"    ~ {mod['key']}")
                for attr, changes in mod['changes'].items():
                    print(f"      {attr}: {changes['old']} -> {changes['new']}")

    # Example 4: Track object evolution
    print("\n" + "=" * 60)
    print("Example 4: Object Evolution Tracking")
    print("=" * 60)

    test_object = "ANALYTICS.PUBLIC.DIM_CUSTOMERS"
    evolution = history_manager.track_object_evolution(
        object_key=test_object,
        start_date=datetime.now() - timedelta(days=30)
    )

    print(f"\nEvolution of {test_object}:")
    print(f"  Snapshots tracking this object: {len(evolution.snapshots)}")
    print(f"  Total changes: {len(evolution.changes_over_time)}")

    if evolution.dependency_history:
        print("\n  Dependency History:")
        for timestamp, deps in list(evolution.dependency_history.items())[:3]:
            print(f"    {timestamp}: {len(deps)} dependencies")
            for dep in deps[:3]:
                print(f"      - {dep}")

    if evolution.schema_evolution:
        print("\n  Schema Evolution:")
        for schema_info in evolution.schema_evolution[:3]:
            print(f"    {schema_info['timestamp']}:")
            for key, value in list(schema_info['attributes'].items())[:3]:
                print(f"      {key}: {value}")

    # Example 5: Find lineage patterns
    print("\n" + "=" * 60)
    print("Example 5: Lineage Pattern Analysis")
    print("=" * 60)

    patterns = history_manager.find_lineage_patterns(min_snapshots=2)

    if "error" not in patterns:
        print("\nLineage Patterns:")

        growth = patterns['growth_rate']
        print(f"\n  Growth Rate:")
        print(f"    Nodes per day: {growth['node_growth_per_day']:.2f}")
        print(f"    Edges per day: {growth['edge_growth_per_day']:.2f}")
        print(f"    Total node growth: {growth['total_node_growth']}")
        print(f"    Total edge growth: {growth['total_edge_growth']}")

        print(f"\n  Volatile Objects (frequently changing):")
        for obj in patterns['volatile_objects'][:5]:
            print(f"    - {obj}")

        print(f"\n  Stable Core Objects (rarely changing):")
        for obj in patterns['stable_core'][:5]:
            print(f"    - {obj}")

        print(f"\n  Common Change Patterns:")
        for pattern in patterns['common_changes']:
            print(f"    - {pattern['pattern']}: {pattern['frequency']} occurrences")

    # Example 6: Create timeline visualization
    print("\n" + "=" * 60)
    print("Example 6: Timeline Visualization")
    print("=" * 60)

    timeline = history_manager.create_timeline_visualization(
        start_date=datetime.now() - timedelta(days=30)
    )

    print("\nLineage Timeline:")
    print(f"  Total Snapshots: {timeline['statistics']['total_snapshots']}")
    print(f"  Date Range: {timeline['statistics']['date_range']['start']} to {timeline['statistics']['date_range']['end']}")
    print(f"  Avg Node Count: {timeline['statistics']['average_node_count']:.1f}")
    print(f"  Avg Edge Count: {timeline['statistics']['average_edge_count']:.1f}")

    print("\n  Timeline Events:")
    for event in timeline['events'][:5]:
        print(f"    {event['timestamp']}:")
        print(f"      Added: {event['added_nodes']} nodes, {event['added_edges']} edges")
        print(f"      Removed: {event['removed_nodes']} nodes, {event['removed_edges']} edges")

    # Example 7: Rollback to snapshot
    print("\n" + "=" * 60)
    print("Example 7: Rollback to Previous Snapshot")
    print("=" * 60)

    rollback_path = Path("./rollback_lineage.json")
    success = history_manager.rollback_to_snapshot("v1.0.0", rollback_path)

    if success:
        print(f"\n✓ Successfully rolled back to v1.0.0")
        print(f"  Exported to: {rollback_path}")
    else:
        print(f"\n✗ Failed to rollback to v1.0.0")

    # Example 8: Export history
    print("\n" + "=" * 60)
    print("Example 8: Exporting Lineage History")
    print("=" * 60)

    # Export as JSON
    json_path = history_manager.export_history(
        Path("./lineage_history.json"),
        format="json"
    )
    print(f"\nExported to JSON: {json_path}")

    # Export as HTML
    html_path = history_manager.export_history(
        Path("./lineage_history.html"),
        format="html"
    )
    print(f"Exported to HTML: {html_path}")

    # Example 9: Retrieve specific snapshot
    print("\n" + "=" * 60)
    print("Example 9: Retrieving Specific Snapshot")
    print("=" * 60)

    snapshot_data = history_manager.get_snapshot("v1.1.0")
    if snapshot_data:
        snapshot, graph = snapshot_data
        print(f"\nRetrieved Snapshot: {snapshot.tag}")
        print(f"  Timestamp: {snapshot.timestamp}")
        print(f"  Graph Nodes: {len(graph.nodes)}")
        print(f"  Graph Edges: {len(graph.edges)}")

        print("\n  Sample Nodes:")
        for key in list(graph.nodes.keys())[:5]:
            node = graph.nodes[key]
            print(f"    - {key}: {node.node_type.value}")

    # Example 10: Analyze specific time period
    print("\n" + "=" * 60)
    print("Example 10: Time Period Analysis")
    print("=" * 60)

    start = datetime.now() - timedelta(days=7)
    end = datetime.now()

    period_snapshots = history_manager.list_snapshots(
        start_date=start,
        end_date=end
    )

    print(f"\nSnapshots in last 7 days: {len(period_snapshots)}")

    if len(period_snapshots) >= 2:
        first = period_snapshots[-1]
        last = period_snapshots[0]

        diff = history_manager.compare_lineage(
            first.snapshot_id,
            last.snapshot_id
        )

        if diff:
            print(f"\nChanges in last 7 days:")
            print(f"  Net node change: {len(diff.added_nodes) - len(diff.removed_nodes):+d}")
            print(f"  Net edge change: {len(diff.added_edges) - len(diff.removed_edges):+d}")


if __name__ == "__main__":
    main()