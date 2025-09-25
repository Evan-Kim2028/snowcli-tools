from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .builder import LineageBuilder
from .graph import EdgeType, LineageEdge, LineageGraph, LineageNode, NodeType


@dataclass
class LineageSnapshot:
    snapshot_id: str
    timestamp: datetime
    tag: Optional[str]
    description: Optional[str]
    graph_hash: str
    node_count: int
    edge_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "tag": self.tag,
            "description": self.description,
            "graph_hash": self.graph_hash,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "metadata": self.metadata,
        }


@dataclass
class LineageChange:
    change_type: str
    object_key: str
    object_type: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type,
            "object_key": self.object_key,
            "object_type": self.object_type,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LineageDiff:
    from_snapshot: LineageSnapshot
    to_snapshot: LineageSnapshot
    added_nodes: List[str]
    removed_nodes: List[str]
    added_edges: List[Tuple[str, str]]
    removed_edges: List[Tuple[str, str]]
    modified_nodes: List[Dict[str, Any]]
    changes: List[LineageChange]
    summary: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "from_snapshot": self.from_snapshot.to_dict(),
            "to_snapshot": self.to_snapshot.to_dict(),
            "added_nodes": self.added_nodes,
            "removed_nodes": self.removed_nodes,
            "added_edges": [(s, t) for s, t in self.added_edges],
            "removed_edges": [(s, t) for s, t in self.removed_edges],
            "modified_nodes": self.modified_nodes,
            "changes": [c.to_dict() for c in self.changes],
            "summary": self.summary,
        }


@dataclass
class LineageEvolution:
    object_key: str
    snapshots: List[LineageSnapshot]
    changes_over_time: List[LineageChange]
    dependency_history: Dict[str, List[str]]
    schema_evolution: List[Dict[str, Any]]

    def to_dict(self) -> dict:
        return {
            "object_key": self.object_key,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "changes_over_time": [c.to_dict() for c in self.changes_over_time],
            "dependency_history": self.dependency_history,
            "schema_evolution": self.schema_evolution,
        }


class LineageHistoryManager:
    def __init__(self, storage_path: Optional[Path] = None, max_snapshots: int = 100):
        self.storage_path = storage_path or Path("./lineage_history")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "lineage_history.db"
        self.max_snapshots = max_snapshots  # Maximum snapshots to retain
        self._init_database()

    def capture_snapshot(
        self,
        catalog_path: Path,
        tag: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LineageSnapshot:
        builder = LineageBuilder(catalog_path)
        result = builder.build()

        snapshot_id = self._generate_snapshot_id()
        timestamp = datetime.now()
        graph_hash = self._hash_graph(result.graph)

        snapshot = LineageSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            tag=tag,
            description=description,
            graph_hash=graph_hash,
            node_count=len(result.graph.nodes),
            edge_count=len(result.graph.edges),
            metadata={
                "catalog_path": str(catalog_path),
                "audit_entries": len(result.audit.entries) if result.audit else 0,
            },
        )

        self._save_snapshot(snapshot, result.graph)
        self._cleanup_old_snapshots()  # Clean up old snapshots to prevent memory exhaustion

        return snapshot

    def get_snapshot(
        self, identifier: str
    ) -> Optional[Tuple[LineageSnapshot, LineageGraph]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM snapshots
            WHERE snapshot_id = ? OR tag = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (identifier, identifier),
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        snapshot = self._row_to_snapshot(row)
        graph = self._load_graph(snapshot.snapshot_id)

        conn.close()
        return snapshot, graph

    def list_snapshots(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags_only: bool = False,
    ) -> List[LineageSnapshot]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM snapshots WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if tags_only:
            query += " AND tag IS NOT NULL"

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        snapshots = [self._row_to_snapshot(row) for row in rows]

        conn.close()
        return snapshots

    def compare_lineage(
        self, identifier1: str, identifier2: str
    ) -> Optional[LineageDiff]:
        snapshot1_data = self.get_snapshot(identifier1)
        snapshot2_data = self.get_snapshot(identifier2)

        if not snapshot1_data or not snapshot2_data:
            return None

        snapshot1, graph1 = snapshot1_data
        snapshot2, graph2 = snapshot2_data

        nodes1 = set(graph1.nodes.keys())
        nodes2 = set(graph2.nodes.keys())

        edges1 = {(e.source, e.target) for e in graph1.edges}
        edges2 = {(e.source, e.target) for e in graph2.edges}

        added_nodes = list(nodes2 - nodes1)
        removed_nodes = list(nodes1 - nodes2)
        added_edges = list(edges2 - edges1)
        removed_edges = list(edges1 - edges2)

        modified_nodes = self._find_modified_nodes(graph1, graph2)
        changes = self._generate_changes(
            added_nodes, removed_nodes, added_edges, removed_edges, modified_nodes
        )

        summary = self._generate_diff_summary(
            added_nodes, removed_nodes, added_edges, removed_edges, modified_nodes
        )

        return LineageDiff(
            from_snapshot=snapshot1,
            to_snapshot=snapshot2,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            modified_nodes=modified_nodes,
            changes=changes,
            summary=summary,
        )

    def track_object_evolution(
        self,
        object_key: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> LineageEvolution:
        snapshots = self.list_snapshots(start_date, end_date)

        object_snapshots = []
        changes = []
        dependency_history = {}
        schema_evolution = []

        for snapshot in snapshots:
            result = self.get_snapshot(snapshot.snapshot_id)
            if result is None:
                continue
            _, graph = result

            if object_key in graph.nodes:
                object_snapshots.append(snapshot)

                node = graph.nodes[object_key]
                timestamp_str = snapshot.timestamp.isoformat()

                dependencies = [e.target for e in graph.edges if e.source == object_key]
                dependency_history[timestamp_str] = dependencies

                schema_info = {
                    "timestamp": timestamp_str,
                    "attributes": node.attributes.copy(),
                }
                schema_evolution.append(schema_info)

        if len(object_snapshots) > 1:
            for i in range(len(object_snapshots) - 1):
                result1 = self.get_snapshot(object_snapshots[i].snapshot_id)
                result2 = self.get_snapshot(object_snapshots[i + 1].snapshot_id)
                if result1 is None or result2 is None:
                    continue
                _, graph1 = result1
                _, graph2 = result2

                if object_key in graph1.nodes and object_key in graph2.nodes:
                    node1 = graph1.nodes[object_key]
                    node2 = graph2.nodes[object_key]

                    if node1.attributes != node2.attributes:
                        change = LineageChange(
                            change_type="modified",
                            object_key=object_key,
                            object_type=node2.attributes.get("object_type"),
                            details={
                                "changes": self._diff_attributes(
                                    node1.attributes, node2.attributes
                                )
                            },
                            timestamp=object_snapshots[i + 1].timestamp,
                        )
                        changes.append(change)

        return LineageEvolution(
            object_key=object_key,
            snapshots=object_snapshots,
            changes_over_time=changes,
            dependency_history=dependency_history,
            schema_evolution=schema_evolution,
        )

    def find_lineage_patterns(self, min_snapshots: int = 5) -> Dict[str, Any]:
        snapshots = self.list_snapshots()

        if len(snapshots) < min_snapshots:
            return {"error": f"Insufficient snapshots. Need at least {min_snapshots}"}

        patterns = {
            "growth_rate": self._calculate_growth_rate(snapshots),
            "volatile_objects": self._find_volatile_objects(snapshots),
            "stable_core": self._find_stable_core(snapshots),
            "seasonal_changes": self._detect_seasonal_patterns(snapshots),
            "common_changes": self._find_common_change_patterns(snapshots),
        }

        return patterns

    def create_timeline_visualization(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        snapshots = self.list_snapshots(start_date, end_date)

        timeline: Dict[str, Any] = {
            "snapshots": [],
            "events": [],
            "statistics": {},
        }

        for i, snapshot in enumerate(snapshots):
            timeline["snapshots"].append(
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "tag": snapshot.tag,
                    "node_count": snapshot.node_count,
                    "edge_count": snapshot.edge_count,
                }
            )

            if i > 0:
                diff = self.compare_lineage(
                    snapshots[i - 1].snapshot_id, snapshot.snapshot_id
                )

                if diff:
                    event = {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "added_nodes": len(diff.added_nodes),
                        "removed_nodes": len(diff.removed_nodes),
                        "added_edges": len(diff.added_edges),
                        "removed_edges": len(diff.removed_edges),
                    }
                    timeline["events"].append(event)

        if snapshots:
            timeline["statistics"] = {
                "total_snapshots": len(snapshots),
                "date_range": {
                    "start": snapshots[-1].timestamp.isoformat(),
                    "end": snapshots[0].timestamp.isoformat(),
                },
                "average_node_count": sum(s.node_count for s in snapshots)
                / len(snapshots),
                "average_edge_count": sum(s.edge_count for s in snapshots)
                / len(snapshots),
            }

        return timeline

    def rollback_to_snapshot(self, snapshot_id: str, output_path: Path) -> bool:
        snapshot_data = self.get_snapshot(snapshot_id)
        if not snapshot_data:
            return False

        snapshot, graph = snapshot_data

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        graph_data = {
            "nodes": {
                key: {"type": node.node_type.value, "attributes": node.attributes}
                for key, node in graph.nodes.items()
            },
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type.value,
                }
                for edge in graph.edges
            ],
        }

        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)

        return True

    def export_history(self, output_path: Path, format: str = "json") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        snapshots = self.list_snapshots()

        if format == "json":
            history_data = {
                "snapshots": [s.to_dict() for s in snapshots],
                "statistics": {
                    "total_snapshots": len(snapshots),
                    "date_range": {
                        "start": (
                            snapshots[-1].timestamp.isoformat() if snapshots else None
                        ),
                        "end": (
                            snapshots[0].timestamp.isoformat() if snapshots else None
                        ),
                    },
                },
            }

            with open(output_path, "w") as f:
                json.dump(history_data, f, indent=2)

        elif format == "html":
            html_content = self._generate_html_history(snapshots)
            with open(output_path, "w") as f:
                f.write(html_content)

        return output_path

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                tag TEXT,
                description TEXT,
                graph_hash TEXT NOT NULL,
                node_count INTEGER,
                edge_count INTEGER,
                metadata TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp ON snapshots (timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tag ON snapshots (tag)
        """
        )

        conn.commit()
        conn.close()

    def _save_snapshot(self, snapshot: LineageSnapshot, graph: LineageGraph):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO snapshots
            (snapshot_id, timestamp, tag, description, graph_hash, node_count, edge_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                snapshot.snapshot_id,
                snapshot.timestamp.isoformat(),
                snapshot.tag,
                snapshot.description,
                snapshot.graph_hash,
                snapshot.node_count,
                snapshot.edge_count,
                json.dumps(snapshot.metadata),
            ),
        )

        conn.commit()
        conn.close()

        graph_file = self.storage_path / f"graph_{snapshot.snapshot_id}.json"
        graph_data = {
            "nodes": {
                key: {"type": node.node_type.value, "attributes": node.attributes}
                for key, node in graph.nodes.items()
            },
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type.value,
                }
                for edge in graph.edges
            ],
        }

        with open(graph_file, "w") as f:
            json.dump(graph_data, f)

    def _load_graph(self, snapshot_id: str) -> LineageGraph:
        graph_file = self.storage_path / f"graph_{snapshot_id}.json"

        if not graph_file.exists():
            return LineageGraph()

        with open(graph_file, "r") as f:
            data = json.load(f)

        graph = LineageGraph()

        for key, node_data in data.get("nodes", {}).items():
            node = LineageNode(
                key=key,
                node_type=NodeType(node_data["type"]),
                attributes=node_data["attributes"],
            )
            graph.add_node(node)

        for edge_data in data.get("edges", []):
            edge = LineageEdge(
                src=edge_data["source"],
                dst=edge_data["target"],
                edge_type=EdgeType(edge_data["type"]),
            )
            graph.add_edge(edge)

        return graph

    def _generate_snapshot_id(self) -> str:
        return (
            datetime.now().strftime("%Y%m%d_%H%M%S_")
            + hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        )

    def _cleanup_old_snapshots(self):
        """Remove old snapshots that exceed the retention limit."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get count of snapshots
        cursor.execute("SELECT COUNT(*) FROM snapshots")
        count = cursor.fetchone()[0]

        if count > self.max_snapshots:
            # Delete oldest snapshots and their graph files
            cursor.execute(
                """
                SELECT snapshot_id FROM snapshots
                ORDER BY timestamp ASC
                LIMIT ?
            """,
                (count - self.max_snapshots,),
            )

            for row in cursor.fetchall():
                snapshot_id = row[0]
                graph_file = self.storage_path / f"graph_{snapshot_id}.json"
                if graph_file.exists():
                    graph_file.unlink()

            # Delete from database
            cursor.execute(
                """
                DELETE FROM snapshots
                WHERE snapshot_id IN (
                    SELECT snapshot_id FROM snapshots
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
            """,
                (count - self.max_snapshots,),
            )

        conn.commit()
        conn.close()

    def _hash_graph(self, graph: LineageGraph) -> str:
        content = json.dumps(
            {
                "nodes": sorted(graph.nodes.keys()),
                "edges": sorted([(e.source, e.target) for e in graph.edges]),
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _row_to_snapshot(self, row: Tuple) -> LineageSnapshot:
        return LineageSnapshot(
            snapshot_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            tag=row[2],
            description=row[3],
            graph_hash=row[4],
            node_count=row[5],
            edge_count=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
        )

    def _find_modified_nodes(
        self, graph1: LineageGraph, graph2: LineageGraph
    ) -> List[Dict[str, Any]]:
        modified = []

        common_nodes = set(graph1.nodes.keys()) & set(graph2.nodes.keys())

        for node_key in common_nodes:
            node1 = graph1.nodes[node_key]
            node2 = graph2.nodes[node_key]

            if node1.attributes != node2.attributes:
                modified.append(
                    {
                        "key": node_key,
                        "changes": self._diff_attributes(
                            node1.attributes, node2.attributes
                        ),
                    }
                )

        return modified

    def _diff_attributes(
        self, attrs1: Dict[str, Any], attrs2: Dict[str, Any]
    ) -> Dict[str, Any]:
        changes = {}

        all_keys = set(attrs1.keys()) | set(attrs2.keys())

        for key in all_keys:
            val1 = attrs1.get(key)
            val2 = attrs2.get(key)

            if val1 != val2:
                changes[key] = {"old": val1, "new": val2}

        return changes

    def _generate_changes(
        self,
        added_nodes: List[str],
        removed_nodes: List[str],
        added_edges: List[Tuple[str, str]],
        removed_edges: List[Tuple[str, str]],
        modified_nodes: List[Dict],
    ) -> List[LineageChange]:
        changes = []

        for node in added_nodes:
            changes.append(
                LineageChange(
                    change_type="added_node",
                    object_key=node,
                    object_type=None,
                    details={},
                    timestamp=datetime.now(),
                )
            )

        for node in removed_nodes:
            changes.append(
                LineageChange(
                    change_type="removed_node",
                    object_key=node,
                    object_type=None,
                    details={},
                    timestamp=datetime.now(),
                )
            )

        for source, target in added_edges:
            changes.append(
                LineageChange(
                    change_type="added_edge",
                    object_key=f"{source} -> {target}",
                    object_type="edge",
                    details={"source": source, "target": target},
                    timestamp=datetime.now(),
                )
            )

        for source, target in removed_edges:
            changes.append(
                LineageChange(
                    change_type="removed_edge",
                    object_key=f"{source} -> {target}",
                    object_type="edge",
                    details={"source": source, "target": target},
                    timestamp=datetime.now(),
                )
            )

        for mod in modified_nodes:
            changes.append(
                LineageChange(
                    change_type="modified_node",
                    object_key=mod["key"],
                    object_type=None,
                    details=mod["changes"],
                    timestamp=datetime.now(),
                )
            )

        return changes

    def _generate_diff_summary(
        self,
        added_nodes: List[str],
        removed_nodes: List[str],
        added_edges: List[Tuple],
        removed_edges: List[Tuple],
        modified_nodes: List[Dict],
    ) -> Dict[str, Any]:
        return {
            "total_changes": len(added_nodes)
            + len(removed_nodes)
            + len(added_edges)
            + len(removed_edges)
            + len(modified_nodes),
            "nodes": {
                "added": len(added_nodes),
                "removed": len(removed_nodes),
                "modified": len(modified_nodes),
            },
            "edges": {"added": len(added_edges), "removed": len(removed_edges)},
            "change_rate": {
                "node_change_rate": (
                    len(added_nodes) + len(removed_nodes) + len(modified_nodes)
                )
                / max(1, len(added_nodes) + len(removed_nodes) + len(modified_nodes)),
                "edge_change_rate": (len(added_edges) + len(removed_edges))
                / max(1, len(added_edges) + len(removed_edges)),
            },
        }

    def _calculate_growth_rate(
        self, snapshots: List[LineageSnapshot]
    ) -> Dict[str, float]:
        if len(snapshots) < 2:
            return {"node_growth": 0.0, "edge_growth": 0.0}

        first = snapshots[-1]
        last = snapshots[0]

        days_diff = (last.timestamp - first.timestamp).days or 1

        node_growth = (last.node_count - first.node_count) / days_diff
        edge_growth = (last.edge_count - first.edge_count) / days_diff

        return {
            "node_growth_per_day": node_growth,
            "edge_growth_per_day": edge_growth,
            "total_node_growth": last.node_count - first.node_count,
            "total_edge_growth": last.edge_count - first.edge_count,
        }

    def _find_volatile_objects(self, snapshots: List[LineageSnapshot]) -> List[str]:
        object_changes = {}

        for i in range(len(snapshots) - 1):
            diff = self.compare_lineage(
                snapshots[i].snapshot_id, snapshots[i + 1].snapshot_id
            )

            if diff:
                for change in diff.changes:
                    obj = change.object_key
                    if obj not in object_changes:
                        object_changes[obj] = 0
                    object_changes[obj] += 1

        volatile = sorted(object_changes.items(), key=lambda x: x[1], reverse=True)[:10]

        return [obj for obj, count in volatile]

    def _find_stable_core(self, snapshots: List[LineageSnapshot]) -> List[str]:
        if not snapshots:
            return []

        all_nodes = []
        for snapshot in snapshots[:5]:
            result = self.get_snapshot(snapshot.snapshot_id)
            if result is None:
                continue
            _, graph = result
            all_nodes.append(set(graph.nodes.keys()))

        if not all_nodes:
            return []

        stable_core = all_nodes[0]
        for nodes in all_nodes[1:]:
            stable_core &= nodes

        return list(stable_core)[:20]

    def _detect_seasonal_patterns(
        self, snapshots: List[LineageSnapshot]
    ) -> Dict[str, Any]:
        return {"detected": False, "pattern": "Analysis requires more historical data"}

    def _find_common_change_patterns(
        self, snapshots: List[LineageSnapshot]
    ) -> List[Dict]:
        pattern_counts = {}

        for i in range(len(snapshots) - 1):
            diff = self.compare_lineage(
                snapshots[i].snapshot_id, snapshots[i + 1].snapshot_id
            )

            if diff:
                pattern = (
                    f"added:{len(diff.added_nodes)}_removed:{len(diff.removed_nodes)}"
                )
                if pattern not in pattern_counts:
                    pattern_counts[pattern] = 0
                pattern_counts[pattern] += 1

        patterns = [
            {"pattern": pattern, "frequency": count}
            for pattern, count in sorted(
                pattern_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        return patterns

    def _generate_html_history(self, snapshots: List[LineageSnapshot]) -> str:
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html><head>")
        html.append("<title>Lineage History</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("table { border-collapse: collapse; width: 100%; }")
        html.append(
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        )
        html.append("th { background-color: #f2f2f2; }")
        html.append(
            ".tag { background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 3px; }"
        )
        html.append("</style>")
        html.append("</head><body>")

        html.append("<h1>Lineage History</h1>")
        html.append(f"<p>Total Snapshots: {len(snapshots)}</p>")

        html.append("<table>")
        html.append(
            "<tr><th>Timestamp</th><th>Tag</th><th>Nodes</th><th>Edges</th><th>Description</th></tr>"
        )

        for snapshot in snapshots[:50]:
            html.append("<tr>")
            html.append(f"<td>{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>")
            html.append(
                f"<td>{f'<span class="tag">{snapshot.tag}</span>' if snapshot.tag else '-'}</td>"
            )
            html.append(f"<td>{snapshot.node_count}</td>")
            html.append(f"<td>{snapshot.edge_count}</td>")
            html.append(f"<td>{snapshot.description or '-'}</td>")
            html.append("</tr>")

        html.append("</table>")
        html.append("</body></html>")

        return "\n".join(html)
