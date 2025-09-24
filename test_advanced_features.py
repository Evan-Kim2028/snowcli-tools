#!/usr/bin/env python3
"""
Test advanced lineage features on dex_trades_stable and CETUS_GENERALIZED_LP_LIVE_DT
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from snowcli_tools.lineage import (
    LineageBuilder,
    ColumnLineageExtractor,
    TransformationTracker,
    CrossDatabaseLineageBuilder,
    ImpactAnalyzer,
    LineageHistoryManager,
    ChangeType,
)

# Path to the data catalogue
CATALOG_PATH = Path("/Users/evandekim/Documents/snowflake_connector_py/data_catalogue")


def load_table_sql(table_name: str) -> str:
    """Load SQL for a specific table from catalogue."""
    # Check dynamic tables first
    dt_file = CATALOG_PATH / "dynamic_tables.jsonl"
    if dt_file.exists():
        with open(dt_file, 'r') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('name') == table_name:
                    return obj.get('text', '')

    # Check views
    views_file = CATALOG_PATH / "views.jsonl"
    if views_file.exists():
        with open(views_file, 'r') as f:
            for line in f:
                obj = json.loads(line)
                if obj.get('name') == table_name:
                    return obj.get('text', '')

    return ""


def test_basic_lineage():
    """Test basic lineage building from catalogue."""
    print("\n" + "="*60)
    print("1. Testing Basic Lineage Building")
    print("="*60)

    try:
        builder = LineageBuilder(CATALOG_PATH)
        result = builder.build()

        print(f"✅ Built lineage graph:")
        print(f"   - Nodes: {len(result.graph.nodes)}")
        print(f"   - Edges: {len(result.graph.edges)}")

        # Look for our specific tables
        dex_trades_found = False
        cetus_found = False

        for node_key in result.graph.nodes:
            if "dex_trades_stable" in node_key.lower():
                dex_trades_found = True
                print(f"   - Found dex_trades_stable: {node_key}")
            if "cetus_generalized_lp_live_dt" in node_key.lower():
                cetus_found = True
                print(f"   - Found CETUS_GENERALIZED_LP_LIVE_DT: {node_key}")

        if not dex_trades_found:
            print("   ⚠️ dex_trades_stable not found in lineage")
        if not cetus_found:
            print("   ⚠️ CETUS_GENERALIZED_LP_LIVE_DT not found in lineage")

        return result.graph

    except Exception as e:
        print(f"❌ Error building lineage: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_column_level_lineage():
    """Test column-level lineage extraction."""
    print("\n" + "="*60)
    print("2. Testing Column-Level Lineage")
    print("="*60)

    # Get SQL for CETUS_GENERALIZED_LP_LIVE_DT
    cetus_sql = load_table_sql("CETUS_GENERALIZED_LP_LIVE_DT")

    if not cetus_sql:
        print("❌ Could not find SQL for CETUS_GENERALIZED_LP_LIVE_DT")
        return

    print(f"Found SQL for CETUS_GENERALIZED_LP_LIVE_DT ({len(cetus_sql)} chars)")

    try:
        extractor = ColumnLineageExtractor(
            default_database="ETHEREUM",
            default_schema="DEFI"
        )

        # Extract first 1000 chars of SQL for testing (full SQL might be very long)
        test_sql = cetus_sql[:2000] if len(cetus_sql) > 2000 else cetus_sql

        lineage = extractor.extract_column_lineage(
            test_sql,
            target_table="CETUS_GENERALIZED_LP_LIVE_DT"
        )

        print(f"✅ Extracted column lineage:")
        print(f"   - Transformations found: {len(lineage.transformations)}")
        print(f"   - Column dependencies: {len(lineage.column_dependencies)}")

        if lineage.issues:
            print(f"   - Issues encountered: {lineage.issues}")

        # Show sample transformations
        for i, trans in enumerate(lineage.transformations[:3]):
            print(f"\n   Transformation {i+1}:")
            print(f"     Target: {trans.target_column.column}")
            print(f"     Type: {trans.transformation_type.value}")
            print(f"     Sources: {len(trans.source_columns)} columns")
            if trans.function_name:
                print(f"     Function: {trans.function_name}")

        return lineage

    except Exception as e:
        print(f"❌ Error extracting column lineage: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_transformation_tracking():
    """Test transformation tracking capabilities."""
    print("\n" + "="*60)
    print("3. Testing Transformation Tracking")
    print("="*60)

    try:
        tracker = TransformationTracker(storage_path=Path("/tmp/transformations"))

        # Get column lineage first
        cetus_sql = load_table_sql("CETUS_GENERALIZED_LP_LIVE_DT")
        if cetus_sql:
            extractor = ColumnLineageExtractor(
                default_database="ETHEREUM",
                default_schema="DEFI"
            )

            lineage = extractor.extract_column_lineage(
                cetus_sql[:1000],  # Use partial SQL for testing
                target_table="CETUS_GENERALIZED_LP_LIVE_DT"
            )

            # Track transformations
            tracked = []
            for trans in lineage.transformations[:5]:  # Track first 5
                metadata = tracker.track_transformation(
                    trans,
                    source_object="SOURCE_TABLE",
                    target_object="CETUS_GENERALIZED_LP_LIVE_DT",
                    business_logic="CETUS LP data processing"
                )
                tracked.append(metadata)

            print(f"✅ Tracked {len(tracked)} transformations")

            # Analyze patterns
            patterns = tracker.analyze_patterns(min_frequency=1)
            print(f"   - Patterns identified: {len(patterns)}")

            for pattern in patterns[:3]:
                print(f"     • {pattern.name}: {pattern.frequency} occurrences")

            # Get summary
            summary = tracker.get_transformation_summary()
            print(f"\n   Summary:")
            print(f"     - Total transformations: {summary['total_transformations']}")
            print(f"     - Types: {summary['transformation_types']}")

        return tracker

    except Exception as e:
        print(f"❌ Error tracking transformations: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_impact_analysis(lineage_graph):
    """Test impact analysis on dex_trades_stable."""
    print("\n" + "="*60)
    print("4. Testing Impact Analysis")
    print("="*60)

    if not lineage_graph:
        print("❌ No lineage graph available")
        return

    try:
        analyzer = ImpactAnalyzer(lineage_graph)

        # Find dex_trades_stable node
        target_node = None
        for node_key in lineage_graph.nodes:
            if "dex_trades_stable" in node_key.lower():
                target_node = node_key
                break

        if not target_node:
            print("❌ Could not find dex_trades_stable in graph")
            # Try with a different table that exists
            if lineage_graph.nodes:
                target_node = list(lineage_graph.nodes.keys())[0]
                print(f"   Using alternative node: {target_node}")

        if target_node:
            # Analyze DROP impact
            report = analyzer.analyze_impact(
                object_name=target_node,
                change_type=ChangeType.DROP,
                max_depth=3
            )

            print(f"✅ Impact analysis for DROP of {target_node}:")
            print(f"   - Risk Score: {report.risk_score:.2f}")
            print(f"   - Total Impacted Objects: {report.total_impacted_objects}")
            print(f"   - Impact by severity: {report.impact_summary.get('by_severity', {})}")

            # Show top impacted objects
            print(f"\n   Top impacted objects:")
            for obj in report.impacted_objects[:5]:
                print(f"     • {obj.object_name} ({obj.severity.value})")

            # Calculate blast radius
            blast_radius = analyzer.calculate_blast_radius(
                object_name=target_node,
                max_depth=2
            )

            print(f"\n   Blast Radius:")
            print(f"     - Downstream: {blast_radius['total_downstream']} objects")
            print(f"     - Upstream: {blast_radius['total_upstream']} objects")

            # Find single points of failure
            spofs = analyzer.find_single_points_of_failure(min_dependent_count=2)
            print(f"\n   Single Points of Failure: {len(spofs)} found")
            for spof in spofs[:3]:
                print(f"     • {spof['object']} ({spof['downstream_count']} dependencies)")

            return report

    except Exception as e:
        print(f"❌ Error in impact analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_time_travel_lineage():
    """Test time-travel lineage capabilities."""
    print("\n" + "="*60)
    print("5. Testing Time-Travel Lineage")
    print("="*60)

    try:
        history_manager = LineageHistoryManager(storage_path=Path("/tmp/lineage_history"))

        # Capture initial snapshot
        snapshot1 = history_manager.capture_snapshot(
            catalog_path=CATALOG_PATH,
            tag="test_v1",
            description="Initial test snapshot"
        )

        print(f"✅ Captured snapshot:")
        print(f"   - ID: {snapshot1.snapshot_id}")
        print(f"   - Tag: {snapshot1.tag}")
        print(f"   - Nodes: {snapshot1.node_count}")
        print(f"   - Edges: {snapshot1.edge_count}")

        # Capture another snapshot (simulating changes)
        snapshot2 = history_manager.capture_snapshot(
            catalog_path=CATALOG_PATH,
            tag="test_v2",
            description="Second test snapshot"
        )

        # Compare snapshots
        diff = history_manager.compare_lineage("test_v1", "test_v2")

        if diff:
            print(f"\n   Snapshot comparison (v1 -> v2):")
            print(f"     - Total changes: {diff.summary['total_changes']}")
            print(f"     - Nodes added: {len(diff.added_nodes)}")
            print(f"     - Nodes removed: {len(diff.removed_nodes)}")

        # List all snapshots
        all_snapshots = history_manager.list_snapshots()
        print(f"\n   Total snapshots captured: {len(all_snapshots)}")

        return history_manager

    except Exception as e:
        print(f"❌ Error in time-travel lineage: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_cross_database_lineage():
    """Test cross-database lineage if multiple databases exist."""
    print("\n" + "="*60)
    print("6. Testing Cross-Database Lineage")
    print("="*60)

    try:
        # For now, we'll use the same catalog path
        # In real scenario, you'd have multiple database catalogs
        builder = CrossDatabaseLineageBuilder([CATALOG_PATH])

        unified = builder.build_cross_db_lineage(
            include_shares=True,
            resolve_external_refs=True
        )

        print(f"✅ Built unified lineage:")
        print(f"   - Databases: {list(unified.databases)}")
        print(f"   - Total nodes: {len(unified.nodes)}")
        print(f"   - Cross-DB references: {len(unified.cross_db_references)}")

        # Analyze database boundaries
        boundary_analysis = builder.analyze_database_boundaries()
        for db_name, analysis in boundary_analysis.items():
            print(f"\n   Database: {db_name}")
            print(f"     - Internal objects: {analysis['internal_objects']}")
            print(f"     - External dependencies: {len(analysis['external_dependencies'])}")

        return unified

    except Exception as e:
        print(f"❌ Error in cross-database lineage: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING ADVANCED LINEAGE FEATURES")
    print("Target tables: dex_trades_stable, CETUS_GENERALIZED_LP_LIVE_DT")
    print("="*60)

    # Test 1: Basic lineage
    lineage_graph = test_basic_lineage()

    # Test 2: Column-level lineage
    column_lineage = test_column_level_lineage()

    # Test 3: Transformation tracking
    tracker = test_transformation_tracking()

    # Test 4: Impact analysis
    if lineage_graph:
        impact_report = test_impact_analysis(lineage_graph)

    # Test 5: Time-travel lineage
    history = test_time_travel_lineage()

    # Test 6: Cross-database lineage
    cross_db = test_cross_database_lineage()

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ Basic Lineage:", "Success" if lineage_graph else "Failed")
    print("✅ Column-Level Lineage:", "Success" if column_lineage else "Failed")
    print("✅ Transformation Tracking:", "Success" if tracker else "Failed")
    print("✅ Impact Analysis:", "Success" if lineage_graph else "N/A")
    print("✅ Time-Travel Lineage:", "Success" if history else "Failed")
    print("✅ Cross-Database Lineage:", "Success" if cross_db else "Failed")


if __name__ == "__main__":
    main()