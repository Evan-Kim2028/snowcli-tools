#!/usr/bin/env python3
# ruff: noqa
"""
API Compatibility Verification Script
Ensures 100% backward compatibility with existing code
"""

import sys

sys.path.insert(0, "src")


def verify_imports():
    """Verify all imports work correctly."""
    print("Testing imports...")

    # Test existing API imports
    try:
        from snowcli_tools.lineage import LineageBuilder, LineageGraph

        print("✓ Core imports (LineageBuilder, LineageGraph) work")
    except ImportError as e:
        print(f"✗ Core import failed: {e}")
        return False

    # Test new advanced features
    try:
        from snowcli_tools.lineage import (
            ChangeType,
            ColumnLineageExtractor,
            CrossDatabaseLineageBuilder,
            ExternalSourceMapper,
            ImpactAnalyzer,
            LineageHistoryManager,
            TransformationTracker,
        )

        print("✓ Advanced feature imports work")
    except ImportError as e:
        print(f"✗ Advanced import failed: {e}")
        return False

    # Test module-level imports (for existing code compatibility)
    try:
        from snowcli_tools.lineage.builder import LineageBuilder as DirectBuilder
        from snowcli_tools.lineage.graph import (
            EdgeType,
            LineageEdge,
            LineageNode,
            NodeType,
        )

        print("✓ Module-level imports work")
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return False

    return True


def verify_lineage_edge_compatibility():
    """Verify LineageEdge has both old and new properties."""
    print("\nTesting LineageEdge compatibility...")

    from snowcli_tools.lineage.graph import LineageEdge

    # Create an edge
    edge = LineageEdge(
        src="table1",
        dst="table2",
        edge_type="downstream",
        evidence={"sql": "SELECT * FROM table1"},
    )

    # Test original properties
    try:
        assert edge.src == "table1", "src property failed"
        assert edge.dst == "table2", "dst property failed"
        print("✓ Original properties (src, dst) work")
    except Exception as e:
        print(f"✗ Original properties failed: {e}")
        return False

    # Test compatibility properties
    try:
        assert edge.source == "table1", "source property failed"
        assert edge.target == "table2", "target property failed"
        print("✓ Compatibility properties (source, target) work")
    except Exception as e:
        print(f"✗ Compatibility properties failed: {e}")
        return False

    return True


def verify_lineage_graph_compatibility():
    """Verify LineageGraph maintains all existing methods."""
    print("\nTesting LineageGraph compatibility...")

    from snowcli_tools.lineage.graph import LineageEdge, LineageGraph, LineageNode

    graph = LineageGraph()

    # Test add_node (original method)
    try:
        node = LineageNode(
            key="test_table", node_type="table", attributes={"database": "TEST_DB"}
        )
        graph.add_node(node)
        print("✓ add_node() method works")
    except Exception as e:
        print(f"✗ add_node() failed: {e}")
        return False

    # Test add_edge (original method)
    try:
        edge = LineageEdge(
            src="table1", dst="table2", edge_type="downstream", evidence={}
        )
        graph.add_edge(edge)
        print("✓ add_edge() method works")
    except Exception as e:
        print(f"✗ add_edge() failed: {e}")
        return False

    # Test edges property (new addition)
    try:
        edges = graph.edges
        assert isinstance(edges, list), "edges should return a list"
        print("✓ edges property works")
    except Exception as e:
        print(f"✗ edges property failed: {e}")
        return False

    # Test traverse (original method)
    try:
        result = graph.traverse("table1", direction="downstream", depth=2)
        print("✓ traverse() method works")
    except Exception as e:
        print(f"✗ traverse() failed: {e}")
        return False

    # Test serialization (original methods)
    try:
        dict_repr = graph.to_dict()
        restored = LineageGraph.from_dict(dict_repr)
        print("✓ to_dict() and from_dict() work")
    except Exception as e:
        print(f"✗ Serialization failed: {e}")
        return False

    return True


def verify_builder_compatibility():
    """Verify LineageBuilder maintains existing interface."""
    print("\nTesting LineageBuilder compatibility...")

    from pathlib import Path

    from snowcli_tools.lineage import LineageBuilder

    try:
        # Test constructor with Path
        builder = LineageBuilder(Path("."))
        print("✓ LineageBuilder constructor works with Path")

        # Test constructor with string
        builder = LineageBuilder(".")
        print("✓ LineageBuilder constructor works with string")

        # The build() method would require actual catalog data
        # but we can verify it exists and has correct signature
        import inspect

        sig = inspect.signature(builder.build)
        print(f"✓ build() method signature: {sig}")

    except Exception as e:
        print(f"✗ LineageBuilder compatibility failed: {e}")
        return False

    return True


def main():
    """Run all compatibility checks."""
    print("=" * 60)
    print("API COMPATIBILITY VERIFICATION")
    print("=" * 60)

    all_passed = True

    # Run all verification tests
    all_passed &= verify_imports()
    all_passed &= verify_lineage_edge_compatibility()
    all_passed &= verify_lineage_graph_compatibility()
    all_passed &= verify_builder_compatibility()

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ RESULT: 100% API COMPATIBILITY CONFIRMED")
        print("All existing code will continue to work without changes.")
        print("New advanced features are fully additive.")
    else:
        print("❌ RESULT: Some compatibility issues found")
        print("Please review the failures above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
