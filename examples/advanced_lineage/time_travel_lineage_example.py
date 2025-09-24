#!/usr/bin/env python
"""
Time-Travel Lineage Example

This example shows how to track lineage changes across deployments.
Use case: You want to understand how your DeFi pipeline evolved from the
initial MVP to the current production version, and identify when specific
tables or dependencies were added.
"""

from pathlib import Path

from snowcli_tools.lineage import LineageHistoryManager


def main():
    print("Time-Travel Lineage Analysis")
    print("=" * 50)
    print()

    # Example: Track DeFi pipeline evolution over deployments
    history_manager = LineageHistoryManager(storage_path=Path("./lineage_history"))
    sample_data_path = Path(__file__).parent.parent / "sample_data"
    catalog_path = sample_data_path / "catalog"

    print("Capturing lineage snapshots...")

    try:
        # Capture current state
        current_snapshot = history_manager.capture_snapshot(
            catalog_path=catalog_path,
            tag="v2.1.0",
            description="Current production DeFi pipeline",
        )

        print("Current snapshot captured:")
        print(f"  Version: {current_snapshot.tag}")
        print(f"  Tables/views: {current_snapshot.node_count}")
        print(f"  Dependencies: {current_snapshot.edge_count}")
        print(f"  Timestamp: {current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M')}")

        # Show previous snapshots if any exist
        all_snapshots = history_manager.list_snapshots()
        print("\nHistorical Snapshots:")

        if len(all_snapshots) > 1:
            print(f"  Total versions tracked: {len(all_snapshots)}")
            for snap in all_snapshots[-3:]:  # Show last 3
                version = snap.tag or f"snapshot_{snap.snapshot_id[:8]}"
                print(f"  {version}: {snap.node_count} tables, {snap.edge_count} links")
                if snap.description:
                    print(f"    {snap.description}")

            # Compare with previous version if available
            if len(all_snapshots) >= 2:
                previous_snap = all_snapshots[-2]
                diff = history_manager.compare_lineage(
                    previous_snap.tag or previous_snap.snapshot_id, current_snapshot.tag
                )

                print(f"\nChanges Since {previous_snap.tag or 'Previous Version'}:")
                if diff.added_nodes:
                    print(f"  Added tables: {len(diff.added_nodes)}")
                    for node in diff.added_nodes[:3]:  # Show first 3
                        print(f"    + {node.split('.')[-1]}")

                if diff.removed_nodes:
                    print(f"  Removed tables: {len(diff.removed_nodes)}")
                    for node in diff.removed_nodes[:3]:  # Show first 3
                        print(f"    - {node.split('.')[-1]}")

                if diff.added_edges:
                    print(f"  New dependencies: {len(diff.added_edges)}")

                if diff.removed_edges:
                    print(f"  Removed dependencies: {len(diff.removed_edges)}")

        else:
            print("  This is the first snapshot - no history to compare")

        # Show trending analysis
        if len(all_snapshots) >= 3:
            print("\nPipeline Growth Trend:")
            snapshots_sorted = sorted(all_snapshots, key=lambda x: x.timestamp)

            oldest = snapshots_sorted[0]
            newest = snapshots_sorted[-1]
            table_growth = newest.node_count - oldest.node_count
            dependency_growth = newest.edge_count - oldest.edge_count

            print(f"  Table growth: +{table_growth} since {oldest.tag or 'start'}")
            print(f"  Dependency growth: +{dependency_growth} relationships")

            # Simple complexity trend
            complexity_trend = "Growing" if table_growth > 0 else "Shrinking"
            print(f"  Complexity trend: {complexity_trend}")

    except Exception as e:
        print(f"Using mock data (history manager issue): {e}")
        print("\nMock DeFi Pipeline Evolution:")
        print("  v1.0.0: Basic RAW -> PROCESSED pipeline (5 tables)")
        print("  v1.5.0: Added ANALYTICS layer (12 tables)")
        print("  v2.0.0: Added external data sources (18 tables)")
        print("  v2.1.0: Added machine learning features (25 tables)")

    print("\nKey Insights:")
    print("  Time-travel lineage helps track architecture evolution")
    print("  Snapshot comparisons reveal impact of schema changes")
    print("  Tagging snapshots enables version-based analysis")
    print("  Growth trends indicate increasing pipeline complexity")

    print("\nAdvanced Usage:")
    print("  Schedule automated daily lineage snapshots")
    print("  Compare lineage before/after major deployments")
    print(f"  Sample setup: {sample_data_path}")
    print("  Track lineage quality metrics over time")


if __name__ == "__main__":
    main()
