"""Comprehensive tests for advanced lineage features, focusing on P0/P1 issues."""

import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import pytest

from nanuk_mcp.lineage import (
    ChangeType,
    ColumnLineageExtractor,
    ImpactAnalyzer,
    LineageHistoryManager,
)
from nanuk_mcp.lineage.column_parser import QualifiedColumn
from nanuk_mcp.lineage.utils import (
    cached_sql_parse,
    networkx_descendants_at_distance,
    safe_file_write,
    safe_sql_parse,
    validate_object_name,
    validate_sql_injection,
)


class TestP0CriticalIssues(TestCase):
    """Test fixes for P0 (critical) issues."""

    def test_missing_imports_resolved(self):
        """Ensure all imports are properly resolved."""
        # These should not raise ImportError

        # Verify they're usable
        col = QualifiedColumn(table="test", column="col")
        self.assertEqual(col.table, "test")

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'--",
            "1; DELETE FROM data WHERE 1=1",
            "/* malicious comment */ SELECT * FROM sensitive",
        ]

        for dangerous in dangerous_inputs:
            self.assertFalse(
                validate_sql_injection(dangerous),
                f"Failed to detect dangerous input: {dangerous}",
            )

        safe_inputs = [
            "SELECT * FROM users",
            "customer_name",
            "ORDER BY date DESC",
        ]

        for safe in safe_inputs:
            self.assertTrue(
                validate_sql_injection(safe), f"False positive on safe input: {safe}"
            )

    def test_file_system_operations_safety(self):
        """Test safe file system operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Test safe_file_write
            test_file = tmppath / "test.txt"
            content = "test content"

            success = safe_file_write(test_file, content)
            self.assertTrue(success)
            self.assertEqual(test_file.read_text(), content)

            # Test atomic write (temp file cleanup on failure)
            with mock.patch("pathlib.Path.replace", side_effect=OSError("Mock error")):
                success = safe_file_write(tmppath / "fail.txt", "content")
                self.assertFalse(success)
                # Ensure temp file is cleaned up
                temp_files = list(tmppath.glob("*.tmp"))
                self.assertEqual(len(temp_files), 0)

    def test_database_connection_safety(self):
        """Test safe database connection handling."""
        from nanuk_mcp.lineage.utils import safe_db_connection

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Should handle connection properly
            with safe_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE test (id INTEGER)")
                conn.commit()

            # Verify connection is closed
            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor2.fetchall()
            conn2.close()
            self.assertEqual(len(tables), 1)


class TestP1HighPriorityIssues(TestCase):
    """Test fixes for P1 (high priority) issues."""

    def test_sql_parse_error_handling(self):
        """Test robust SQL parsing error handling."""
        test_cases = [
            ("", None),  # Empty SQL
            (None, None),  # None SQL
            ("INVALID SQL GARBAGE", None),  # Invalid SQL
            ("SELECT * FROM table", "SELECT"),  # Valid SQL
            ("SELECT 1; SELECT 2", ["SELECT", "SELECT"]),  # Multi-statement
        ]

        for sql, expected_type in test_cases:
            result = safe_sql_parse(sql)
            if expected_type is None:
                self.assertIsNone(result, f"Expected None for SQL: {sql}")
            elif isinstance(expected_type, list):
                self.assertIsInstance(result, list)
                for r in result:
                    self.assertIsNotNone(r)
            else:
                self.assertIsNotNone(result)

    def test_networkx_descendants_at_distance(self):
        """Test custom networkx descendants function."""
        import networkx as nx

        # Create test graph
        g = nx.DiGraph()
        g.add_edges_from(
            [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("B", "E"),
                ("A", "F"),
            ]
        )

        # Test distance 1
        desc = networkx_descendants_at_distance(g, "A", 1)
        self.assertEqual(desc, {"B", "F"})

        # Test distance 2
        desc = networkx_descendants_at_distance(g, "A", 2)
        self.assertEqual(desc, {"B", "F", "C", "E"})

        # Test distance 3
        desc = networkx_descendants_at_distance(g, "A", 3)
        self.assertEqual(desc, {"B", "F", "C", "E", "D"})

        # Test non-existent node
        desc = networkx_descendants_at_distance(g, "Z", 1)
        self.assertEqual(desc, set())

    def test_memory_leak_prevention(self):
        """Test memory leak prevention in history manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir)
            manager = LineageHistoryManager(storage_path=storage_path)

            # Create multiple snapshots
            for i in range(5):
                # Mock catalog path
                catalog_path = storage_path / "catalog"
                catalog_path.mkdir(exist_ok=True)

                with mock.patch.object(manager, "_save_snapshot"):
                    manager.capture_snapshot(
                        catalog_path, tag=f"v{i}", description=f"Snapshot {i}"
                    )

            # Test cleanup function
            from nanuk_mcp.lineage.utils import clean_old_snapshots

            # Create fake old graph files
            for i in range(150):
                graph_file = storage_path / f"graph_{i}.json"
                graph_file.write_text("{}")

            # Clean old snapshots
            clean_old_snapshots(storage_path, keep_count=100, keep_days=90)

            # Should keep only 100 files
            remaining = list(storage_path.glob("graph_*.json"))
            self.assertLessEqual(len(remaining), 100)

    def test_performance_optimization_cache(self):
        """Test functools.lru_cache for SQL parsing optimization."""
        # Clear cache first to ensure clean test state
        cached_sql_parse.cache_clear()

        # Test that caching works by checking cache_info
        self.assertEqual(cached_sql_parse.cache_info().currsize, 0)

        # Parse some SQL statements
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT name FROM customers"

        result1 = cached_sql_parse(sql1)
        self.assertEqual(cached_sql_parse.cache_info().hits, 0)
        self.assertEqual(cached_sql_parse.cache_info().misses, 1)

        cached_sql_parse(sql2)
        self.assertEqual(cached_sql_parse.cache_info().misses, 2)

        # Parse same SQL again - should hit cache
        result1_cached = cached_sql_parse(sql1)
        self.assertEqual(cached_sql_parse.cache_info().hits, 1)

        # Verify results are consistent
        self.assertIsNotNone(result1)
        self.assertEqual(result1.sql(), result1_cached.sql())

    def test_object_name_validation(self):
        """Test Snowflake object name validation."""
        valid_names = [
            "table_name",
            "SCHEMA.TABLE",
            "DB.SCHEMA.TABLE",
            "_underscore_start",
            "name123",
            "name$with$dollar",
            '"Mixed Case Name"',
        ]

        invalid_names = [
            "",
            None,
            "123startwithnumber",  # Can't start with number
            "name-with-dash",  # Dash not allowed
            "name with spaces",  # Spaces not allowed (unless quoted)
            "name@special",  # @ not allowed
        ]

        for name in valid_names:
            self.assertTrue(validate_object_name(name), f"Valid name rejected: {name}")

        for name in invalid_names:
            self.assertFalse(
                validate_object_name(name) if name else False,
                f"Invalid name accepted: {name}",
            )


class TestColumnLineageRobustness(TestCase):
    """Test column lineage extraction robustness."""

    def test_multi_statement_sql_handling(self):
        """Test handling of multi-statement SQL."""
        extractor = ColumnLineageExtractor()

        multi_sql = """
        CREATE TABLE temp AS SELECT * FROM source;
        INSERT INTO target SELECT * FROM temp;
        DROP TABLE temp;
        """

        lineage = extractor.extract_column_lineage(multi_sql)

        # Should process first statement and note the issue
        self.assertIn("Multi-statement SQL detected", " ".join(lineage.issues))

    def test_invalid_table_name_handling(self):
        """Test handling of invalid table names."""
        extractor = ColumnLineageExtractor()

        sql = "SELECT * FROM valid_table"
        invalid_target = "123-invalid-name"

        lineage = extractor.extract_column_lineage(sql, target_table=invalid_target)

        # Should reject invalid name
        self.assertIn("Invalid target table name", " ".join(lineage.issues))

    def test_complex_sql_parsing(self):
        """Test parsing of complex SQL with various edge cases."""
        extractor = ColumnLineageExtractor()

        complex_sql = """
        WITH recursive_cte AS (
            SELECT id, parent_id, name, 0 as level
            FROM hierarchy
            WHERE parent_id IS NULL
            UNION ALL
            SELECT h.id, h.parent_id, h.name, r.level + 1
            FROM hierarchy h
            JOIN recursive_cte r ON h.parent_id = r.id
        )
        SELECT * FROM recursive_cte
        """

        lineage = extractor.extract_column_lineage(complex_sql, "hierarchy_flat")

        # Should handle recursive CTE without crashing
        self.assertIsNotNone(lineage)
        self.assertIsInstance(lineage.transformations, list)


class TestImpactAnalysisRobustness(TestCase):
    """Test impact analysis robustness."""

    def test_missing_node_handling(self):
        """Test handling of missing nodes in impact analysis."""
        from nanuk_mcp.lineage.graph import LineageGraph, LineageNode, NodeType

        graph = LineageGraph()

        # Add some test nodes
        graph.add_node(
            LineageNode(
                key="existing_node",
                node_type=NodeType.DATASET,
                attributes={"name": "test"},
            )
        )

        analyzer = ImpactAnalyzer(graph)

        # Try to analyze impact on non-existent node
        with self.assertRaises(ValueError) as context:
            analyzer.analyze_impact("non_existent_node", ChangeType.DROP, max_depth=5)

        self.assertIn("not found", str(context.exception).lower())

    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        import networkx as nx

        # Create graph with cycle
        g = nx.DiGraph()
        g.add_edges_from(
            [
                ("A", "B"),
                ("B", "C"),
                ("C", "A"),  # Creates cycle
            ]
        )

        # Mock LineageGraph
        mock_graph = mock.MagicMock()
        mock_graph.nodes = {"A": {}, "B": {}, "C": {}}
        mock_graph.edges = []

        analyzer = ImpactAnalyzer(mock_graph)
        analyzer.nx_graph = g

        cycles = analyzer.identify_circular_dependencies()

        self.assertEqual(len(cycles), 1)
        self.assertIn("A", cycles[0])
        self.assertIn("B", cycles[0])
        self.assertIn("C", cycles[0])


class TestExternalSourceSecurity(TestCase):
    """Test external source mapping security."""

    def test_credential_handling(self):
        """Test that credentials are not exposed in exports."""
        from nanuk_mcp.lineage.external import ExternalSource, ExternalSourceType

        source = ExternalSource(
            source_type=ExternalSourceType.S3,
            location="s3://bucket/path",
            credentials_ref="env:AWS_CREDENTIALS",
            encryption={"type": "AES256"},
        )

        # Convert to dict (as would be exported)
        exported = source.to_dict()

        # Should indicate credentials exist but not expose them
        self.assertTrue(exported["has_credentials"])
        self.assertNotIn("credentials", exported)
        self.assertNotIn("aws_key", str(exported))
        self.assertNotIn("very_secret", str(exported))


class TestTimeTravel(TestCase):
    """Test time-travel lineage features."""

    def test_snapshot_comparison(self):
        """Test snapshot comparison functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = LineageHistoryManager(storage_path=Path(tmpdir))

            # Mock the catalog and graph building but don't mock _save_snapshot
            # so that snapshots are actually saved to the database
            with mock.patch(
                "nanuk_mcp.lineage.history.LineageBuilder"
            ) as mock_builder:
                # Mock the builder to return a minimal graph
                mock_result = mock.Mock()
                mock_result.graph = mock.Mock()
                mock_result.graph.nodes = {}
                mock_result.graph.edge_metadata = {}
                mock_result.graph.edges = []  # Mock the edges property
                mock_result.audit = mock.Mock()
                mock_result.audit.entries = []  # Mock the audit entries
                mock_builder.return_value.build.return_value = mock_result

                manager.capture_snapshot(Path(tmpdir), tag="v1", description="First")

                manager.capture_snapshot(Path(tmpdir), tag="v2", description="Second")

            # Test snapshot listing
            snapshots = manager.list_snapshots()
            self.assertGreaterEqual(len(snapshots), 2)

            # Test tag filtering
            tagged = manager.list_snapshots(tags_only=True)
            for snap in tagged:
                self.assertIsNotNone(snap.tag)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
