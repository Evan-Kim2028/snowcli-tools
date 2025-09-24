from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from .builder import LineageBuilder
from .constants import Limits, Timeouts
from .graph import LineageGraph
from .identifiers import normalize
from .loader import CatalogLoader
from .utils import TimeoutError, timeout


@dataclass
class CrossDatabaseReference:
    source_db: str
    source_object: str
    target_db: str
    target_object: str
    reference_type: str
    is_data_share: bool = False
    share_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_db": self.source_db,
            "source_object": self.source_object,
            "target_db": self.target_db,
            "target_object": self.target_object,
            "reference_type": self.reference_type,
            "is_data_share": self.is_data_share,
            "share_name": self.share_name,
        }


@dataclass
class UnifiedLineageNode:
    key: str
    database: str
    schema: str
    name: str
    object_type: str
    is_external: bool = False
    share_info: Optional[Dict] = None

    def fqn(self) -> str:
        return f"{self.database}.{self.schema}.{self.name}"


@dataclass
class UnifiedLineageGraph:
    nodes: Dict[str, UnifiedLineageNode] = field(default_factory=dict)
    edges: List[Tuple[str, str, Dict]] = field(default_factory=list)
    cross_db_references: List[CrossDatabaseReference] = field(default_factory=list)
    databases: Set[str] = field(default_factory=set)
    shares: Dict[str, Dict] = field(default_factory=dict)
    nx_graph: Optional[nx.DiGraph] = None

    def add_node(self, node: UnifiedLineageNode):
        self.nodes[node.key] = node
        self.databases.add(node.database)

    def add_edge(self, source: str, target: str, attributes: Optional[Dict] = None):
        self.edges.append((source, target, attributes or {}))

    def add_cross_db_reference(self, reference: CrossDatabaseReference):
        self.cross_db_references.append(reference)

    def get_cross_db_dependencies(self, database: str) -> List[CrossDatabaseReference]:
        return [
            ref
            for ref in self.cross_db_references
            if ref.source_db == database or ref.target_db == database
        ]

    def build_networkx_graph(self) -> nx.DiGraph:
        if self.nx_graph is None:
            self.nx_graph = nx.DiGraph()

            for node_key, node in self.nodes.items():
                self.nx_graph.add_node(
                    node_key,
                    database=node.database,
                    schema=node.schema,
                    name=node.name,
                    object_type=node.object_type,
                    is_external=node.is_external,
                    fqn=node.fqn(),
                )

            for source, target, attrs in self.edges:
                self.nx_graph.add_edge(source, target, **attrs)

        return self.nx_graph


class CrossDatabaseLineageBuilder:
    def __init__(self, catalog_paths: List[Path]):
        self.catalog_paths = [Path(p) for p in catalog_paths]
        self.database_graphs: Dict[str, LineageGraph] = {}
        self.database_catalogs: Dict[str, List] = {}
        self.unified_graph = UnifiedLineageGraph()

    def build_cross_db_lineage(
        self,
        include_shares: bool = True,
        resolve_external_refs: bool = True,
        timeout_seconds: int = Timeouts.DEFAULT_CROSS_DB_BUILD,
    ) -> UnifiedLineageGraph:
        try:
            with timeout(
                timeout_seconds,
                f"Cross-database lineage build timed out after {timeout_seconds}s",
            ):
                for catalog_path in self.catalog_paths:
                    self._load_database_lineage(catalog_path)

                self._merge_graphs()

                if resolve_external_refs:
                    self._resolve_external_references()

                if include_shares:
                    self._process_data_shares()

                self._identify_cross_db_references()

        except TimeoutError:
            # Return partial results if timeout occurs
            import logging

            logging.warning(
                f"Cross-database lineage build timed out after {timeout_seconds} seconds"
            )
            # Return what we have built so far

        return self.unified_graph

    def analyze_database_boundaries(self) -> Dict[str, Dict]:
        analysis = {}

        for db_name in self.unified_graph.databases:
            db_analysis: Dict[str, Any] = {
                "database": db_name,
                "internal_objects": 0,
                "external_dependencies": [],
                "external_dependents": [],
                "shared_objects": [],
                "cross_db_references": [],
            }

            for node_key, node in self.unified_graph.nodes.items():
                if node.database == db_name:
                    db_analysis["internal_objects"] += 1

            for ref in self.unified_graph.cross_db_references:
                if ref.source_db == db_name:
                    db_analysis["external_dependencies"].append(
                        {
                            "target": ref.target_object,
                            "database": ref.target_db,
                            "type": ref.reference_type,
                        }
                    )
                if ref.target_db == db_name:
                    db_analysis["external_dependents"].append(
                        {
                            "source": ref.source_object,
                            "database": ref.source_db,
                            "type": ref.reference_type,
                        }
                    )

            analysis[db_name] = db_analysis

        return analysis

    def find_cross_db_paths(
        self,
        source: str,
        target: str,
        max_depth: int = Limits.MAX_PATH_DEPTH,
        max_paths: int = Limits.MAX_PATHS,
        timeout_seconds: int = Timeouts.DEFAULT_PATH_FINDING,
    ) -> List[List[str]]:
        graph = self.unified_graph.build_networkx_graph()

        try:
            with timeout(
                timeout_seconds, f"Path finding timed out after {timeout_seconds}s"
            ):
                # Limit paths to prevent exponential resource exhaustion
                paths = []
                path_generator = nx.all_simple_paths(
                    graph, source, target, cutoff=max_depth
                )

                for i, path in enumerate(path_generator):
                    if i >= max_paths:
                        break  # Stop after max_paths to prevent resource exhaustion
                    paths.append(path)

                return paths
        except TimeoutError:
            import logging

            logging.warning(f"Path finding between {source} and {target} timed out")
            return []  # Return empty list on timeout
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def identify_database_hubs(
        self, min_connections: int = Limits.MAX_HUB_CONNECTIONS
    ) -> List[Dict]:
        graph = self.unified_graph.build_networkx_graph()
        hubs = []

        for node in graph.nodes():
            node_data = self.unified_graph.nodes.get(node)
            if not node_data:
                continue

            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)
            total_connections = in_degree + out_degree

            if total_connections >= min_connections:
                connected_dbs = set()
                for neighbor in graph.predecessors(node):
                    neighbor_data = self.unified_graph.nodes.get(neighbor)
                    if neighbor_data:
                        connected_dbs.add(neighbor_data.database)
                for neighbor in graph.successors(node):
                    neighbor_data = self.unified_graph.nodes.get(neighbor)
                    if neighbor_data:
                        connected_dbs.add(neighbor_data.database)

                if len(connected_dbs) > 1:
                    hubs.append(
                        {
                            "node": node,
                            "database": node_data.database,
                            "object": node_data.fqn(),
                            "in_degree": in_degree,
                            "out_degree": out_degree,
                            "total_connections": total_connections,
                            "connected_databases": list(connected_dbs),
                        }
                    )

        return sorted(hubs, key=lambda x: x["total_connections"], reverse=True)

    def export_unified_lineage(self, output_path: Path, format: str = "json") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = {
                "databases": list(self.unified_graph.databases),
                "nodes": {
                    key: {
                        "database": node.database,
                        "schema": node.schema,
                        "name": node.name,
                        "object_type": node.object_type,
                        "is_external": node.is_external,
                        "fqn": node.fqn(),
                    }
                    for key, node in self.unified_graph.nodes.items()
                },
                "edges": [
                    {"source": s, "target": t, "attributes": a}
                    for s, t, a in self.unified_graph.edges
                ],
                "cross_db_references": [
                    ref.to_dict() for ref in self.unified_graph.cross_db_references
                ],
                "shares": self.unified_graph.shares,
            }

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "dot":
            dot_content = self._generate_dot_graph()
            with open(output_path, "w") as f:
                f.write(dot_content)

        elif format == "graphml":
            graph = self.unified_graph.build_networkx_graph()
            nx.write_graphml(graph, output_path)

        return output_path

    def _load_database_lineage(self, catalog_path: Path):
        loader = CatalogLoader(catalog_path)
        objects = loader.load()

        if objects:
            first_obj = objects[0]
            database_name = (
                normalize(first_obj.database) if first_obj.database else "UNKNOWN"
            )
            if database_name:  # Only add if database_name is not None
                self.database_catalogs[database_name] = objects

            builder = LineageBuilder(catalog_path)
            result = builder.build()
            if database_name:  # Only add if database_name is not None
                self.database_graphs[database_name] = result.graph

    def _merge_graphs(self):
        for db_name, graph in self.database_graphs.items():
            for node_key, node in graph.nodes.items():
                unified_node = UnifiedLineageNode(
                    key=f"{db_name}::{node_key}",
                    database=db_name,
                    schema=node.attributes.get("schema", ""),
                    name=node.attributes.get("name", ""),
                    object_type=node.attributes.get("object_type", ""),
                )
                self.unified_graph.add_node(unified_node)

            for edge in graph.edges:
                source_key = f"{db_name}::{edge.source}"
                target_key = f"{db_name}::{edge.target}"

                if (
                    source_key in self.unified_graph.nodes
                    and target_key in self.unified_graph.nodes
                ):
                    self.unified_graph.add_edge(
                        source_key, target_key, {"type": edge.edge_type.value}
                    )

    def _resolve_external_references(self):
        unresolved_refs = []

        for db_name, graph in self.database_graphs.items():
            for edge in graph.edges:
                source_node = graph.nodes.get(edge.source)
                target_node = graph.nodes.get(edge.target)

                if not source_node or not target_node:
                    continue

                source_fqn = source_node.attributes.get("fqn", "")
                target_fqn = target_node.attributes.get("fqn", "")

                source_parts = source_fqn.split(".")
                target_parts = target_fqn.split(".")

                if len(source_parts) >= 3 and source_parts[0] != db_name:
                    external_db = source_parts[0]
                    external_key = ".".join(source_parts[1:])
                    resolved_key = self._find_object_in_database(
                        external_db, external_key
                    )

                    if resolved_key:
                        self.unified_graph.add_edge(
                            resolved_key,
                            f"{db_name}::{edge.target}",
                            {"type": "cross_database", "original_ref": source_fqn},
                        )
                    else:
                        unresolved_refs.append(source_fqn)

                if len(target_parts) >= 3 and target_parts[0] != db_name:
                    external_db = target_parts[0]
                    external_key = ".".join(target_parts[1:])
                    resolved_key = self._find_object_in_database(
                        external_db, external_key
                    )

                    if resolved_key:
                        self.unified_graph.add_edge(
                            f"{db_name}::{edge.source}",
                            resolved_key,
                            {"type": "cross_database", "original_ref": target_fqn},
                        )
                    else:
                        unresolved_refs.append(target_fqn)

        if unresolved_refs:
            for ref in set(unresolved_refs):
                external_node = UnifiedLineageNode(
                    key=f"external::{ref}",
                    database="EXTERNAL",
                    schema="UNKNOWN",
                    name=ref,
                    object_type="external_reference",
                    is_external=True,
                )
                self.unified_graph.add_node(external_node)

    def _find_object_in_database(self, database: str, object_key: str) -> Optional[str]:
        if database in self.database_graphs:
            graph = self.database_graphs[database]
            for node_key in graph.nodes:
                if object_key in node_key:
                    return f"{database}::{node_key}"
        return None

    def _process_data_shares(self):
        for db_name, catalog_objects in self.database_catalogs.items():
            for obj in catalog_objects:
                if hasattr(obj, "share_name") and obj.share_name:
                    share_name = obj.share_name
                    if share_name not in self.unified_graph.shares:
                        self.unified_graph.shares[share_name] = {
                            "name": share_name,
                            "provider_database": db_name,
                            "shared_objects": [],
                        }

                    self.unified_graph.shares[share_name]["shared_objects"].append(
                        {
                            "database": db_name,
                            "object": obj.fqn(),
                            "type": (
                                obj.object_type.value
                                if hasattr(obj.object_type, "value")
                                else str(obj.object_type)
                            ),
                        }
                    )

                    node_key = f"{db_name}::{obj.fqn()}"
                    if node_key in self.unified_graph.nodes:
                        self.unified_graph.nodes[node_key].share_info = {
                            "share_name": share_name,
                            "is_shared": True,
                        }

    def _identify_cross_db_references(self):
        for source, target, attrs in self.unified_graph.edges:
            source_node = self.unified_graph.nodes.get(source)
            target_node = self.unified_graph.nodes.get(target)

            if source_node and target_node:
                if source_node.database != target_node.database:
                    ref = CrossDatabaseReference(
                        source_db=source_node.database,
                        source_object=source_node.fqn(),
                        target_db=target_node.database,
                        target_object=target_node.fqn(),
                        reference_type=attrs.get("type", "dependency"),
                        is_data_share=bool(
                            source_node.share_info or target_node.share_info
                        ),
                        share_name=(
                            source_node.share_info or target_node.share_info or {}
                        ).get("share_name"),
                    )
                    self.unified_graph.add_cross_db_reference(ref)

    def _generate_dot_graph(self) -> str:
        lines = ["digraph UnifiedLineage {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        db_colors = {}
        color_palette = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#96CEB4",
            "#FECA57",
            "#48C9B0",
            "#9B59B6",
            "#3498DB",
            "#E74C3C",
            "#F39C12",
        ]

        for i, db in enumerate(self.unified_graph.databases):
            db_colors[db] = color_palette[i % len(color_palette)]

        for db in self.unified_graph.databases:
            lines.append(f'  subgraph "cluster_{db}" {{')
            lines.append(f'    label="{db}";')
            lines.append("    style=filled;")
            lines.append(f'    fillcolor="{db_colors[db]}20";')

            for node_key, node in self.unified_graph.nodes.items():
                if node.database == db:
                    label = f"{node.schema}.{node.name}\\n({node.object_type})"
                    color = db_colors[db] if not node.is_external else "#95A5A6"
                    lines.append(
                        f'    "{node_key}" [label="{label}", fillcolor="{color}40"];'
                    )

            lines.append("  }")

        for source, target, attrs in self.unified_graph.edges:
            edge_style = "solid" if attrs.get("type") != "cross_database" else "dashed"
            edge_color = "black" if attrs.get("type") != "cross_database" else "red"
            lines.append(
                f'  "{source}" -> "{target}" [style={edge_style}, color={edge_color}];'
            )

        lines.append("}")
        return "\n".join(lines)
