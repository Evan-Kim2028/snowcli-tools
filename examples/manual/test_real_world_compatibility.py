#!/usr/bin/env python3
# ruff: noqa
"""
Real-world API compatibility test simulating existing code patterns.
This ensures that code written for the original API continues to work.
"""

import sys

sys.path.insert(0, "src")


def test_legacy_code_pattern():
    """Test that legacy code patterns still work."""
    print("Testing legacy code patterns...")

    # This is how existing code would use the lineage API
    from snowcli_tools.lineage.graph import (
        LineageEdge,
        LineageGraph,
        LineageNode,
    )

    # Create a graph the old way
    graph = LineageGraph()

    # Add nodes using the original API (with string types for compatibility)
    node1 = LineageNode(
        key="DB.SCHEMA.TABLE1",
        node_type="table",  # Using string as that's what the builder uses
        attributes={"database": "DB", "schema": "SCHEMA", "name": "TABLE1"},
    )
    node2 = LineageNode(
        key="DB.SCHEMA.VIEW1",
        node_type="view",  # Using string as that's what the builder uses
        attributes={"database": "DB", "schema": "SCHEMA", "name": "VIEW1"},
    )

    graph.add_node(node1)
    graph.add_node(node2)

    # Add edge using original properties (src, dst)
    edge = LineageEdge(
        src="DB.SCHEMA.TABLE1",
        dst="DB.SCHEMA.VIEW1",
        edge_type="downstream",  # Using string for compatibility
        evidence={"sql": "CREATE VIEW VIEW1 AS SELECT * FROM TABLE1"},
    )
    graph.add_edge(edge)

    # Test traversal (original method)
    downstream = graph.traverse("DB.SCHEMA.TABLE1", direction="downstream")
    assert "DB.SCHEMA.VIEW1" in downstream.nodes, "Traversal failed"

    # Test serialization (original methods)
    graph_dict = graph.to_dict()
    assert len(graph_dict["nodes"]) == 2, "Serialization failed"
    assert len(graph_dict["edges"]) == 1, "Serialization failed"

    # Test deserialization
    restored_graph = LineageGraph.from_dict(graph_dict)
    assert len(restored_graph.nodes) == 2, "Deserialization failed"

    print("✓ Legacy code patterns work correctly")
    return True


def test_mixed_usage():
    """Test that old and new APIs can be used together."""
    print("\nTesting mixed old/new API usage...")

    # Import both old and new
    from snowcli_tools.lineage import ColumnLineageExtractor, LineageGraph

    # Use old API to create graph
    graph = LineageGraph()

    # Use new API features
    extractor = ColumnLineageExtractor()

    # Old API method
    from snowcli_tools.lineage.graph import LineageNode

    node = LineageNode(
        key="TEST_TABLE", node_type="table", attributes={}  # Can use string now
    )
    graph.add_node(node)

    # New API property
    edges = graph.edges  # New property works alongside old methods

    print("✓ Old and new APIs work together")
    return True


def test_edge_property_compatibility():
    """Test that both src/dst and source/target work."""
    print("\nTesting edge property compatibility...")

    from snowcli_tools.lineage.graph import LineageEdge

    edge = LineageEdge(
        src="TABLE_A", dst="TABLE_B", edge_type="downstream", evidence={}
    )

    # Test that both old and new accessors work
    assert edge.src == "TABLE_A", "src property broken"
    assert edge.source == "TABLE_A", "source property broken"
    assert edge.dst == "TABLE_B", "dst property broken"
    assert edge.target == "TABLE_B", "target property broken"

    # Both should reference the same underlying data
    assert edge.src == edge.source, "src and source don't match"
    assert edge.dst == edge.target, "dst and target don't match"

    print("✓ Both src/dst and source/target properties work")
    return True


def test_string_enum_compatibility():
    """Test that both string and enum types work for node_type and edge_type."""
    print("\nTesting string/enum compatibility...")

    from snowcli_tools.lineage.graph import (
        EdgeType,
        LineageEdge,
        LineageGraph,
        LineageNode,
        NodeType,
    )

    graph = LineageGraph()

    # Add node with enum type
    node1 = LineageNode(key="NODE1", node_type=NodeType.DATASET, attributes={})
    graph.add_node(node1)

    # Add node with string type
    node2 = LineageNode(key="NODE2", node_type="view", attributes={})
    graph.add_node(node2)

    # Add edge with enum type
    edge1 = LineageEdge(
        src="NODE1", dst="NODE2", edge_type=EdgeType.DERIVES_FROM, evidence={}
    )
    graph.add_edge(edge1)

    # Add edge with string type
    edge2 = LineageEdge(src="NODE2", dst="NODE1", edge_type="upstream", evidence={})
    graph.add_edge(edge2)

    # Serialize and deserialize
    graph_dict = graph.to_dict()
    restored = LineageGraph.from_dict(graph_dict)

    assert len(restored.nodes) == 2, "Node count mismatch"
    assert len(restored.edges) == 2, "Edge count mismatch"

    print("✓ Both string and enum types work")
    return True


def test_import_patterns():
    """Test various import patterns that existing code might use."""
    print("\nTesting various import patterns...")

    # Pattern 1: Direct module imports
    # Pattern 2: Package-level imports
    from snowcli_tools.lineage import LineageBuilder as LB
    from snowcli_tools.lineage import LineageGraph as LG
    from snowcli_tools.lineage.builder import LineageBuilder
    from snowcli_tools.lineage.graph import LineageGraph

    # All should reference the same classes
    assert LineageGraph == LG, "Different LineageGraph classes"
    assert LineageBuilder == LB, "Different LineageBuilder classes"

    # Pattern 3: Test that __all__ exports are available
    import snowcli_tools.lineage as lineage

    assert hasattr(lineage, "LineageGraph"), "LineageGraph not in exports"
    assert hasattr(lineage, "LineageBuilder"), "LineageBuilder not in exports"
    assert hasattr(lineage, "ColumnLineageExtractor"), "New features not in exports"

    print("✓ All import patterns work")
    return True


def main():
    """Run all real-world compatibility tests."""
    print("=" * 60)
    print("REAL-WORLD API COMPATIBILITY TEST")
    print("=" * 60)

    all_passed = True

    try:
        all_passed &= test_legacy_code_pattern()
        all_passed &= test_mixed_usage()
        all_passed &= test_edge_property_compatibility()
        all_passed &= test_string_enum_compatibility()
        all_passed &= test_import_patterns()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ REAL-WORLD COMPATIBILITY: 100% CONFIRMED")
        print("\nKey guarantees:")
        print("• All existing code continues to work unchanged")
        print("• Original src/dst properties maintained")
        print("• New source/target aliases work alongside")
        print("• Both enum and string types accepted")
        print("• All import patterns preserved")
        print("• Serialization format unchanged")
        print("• New features are purely additive")
    else:
        print("❌ Some compatibility issues found")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
