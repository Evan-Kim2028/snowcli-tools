from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, cast


class NodeType(str, Enum):
    DATASET = "dataset"
    TASK = "task"


class EdgeType(str, Enum):
    DERIVES_FROM = "derives_from"
    PRODUCES = "produces"
    CONSUMES = "consumes"


@dataclass
class LineageNode:
    key: str
    node_type: NodeType
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class LineageEdge:
    src: str
    dst: str
    edge_type: EdgeType
    evidence: Dict[str, str] = field(default_factory=dict)


class LineageGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, LineageNode] = {}
        self.out_edges: Dict[str, Dict[EdgeType, Set[str]]] = {}
        self.in_edges: Dict[str, Dict[EdgeType, Set[str]]] = {}
        self.edge_metadata: Dict[Tuple[str, str, EdgeType], Dict[str, str]] = {}

    def add_node(self, node: LineageNode) -> None:
        if node.key not in self.nodes:
            self.nodes[node.key] = node
            self.out_edges[node.key] = {}
            self.in_edges[node.key] = {}
        else:
            existing = self.nodes[node.key]
            existing.attributes.update(node.attributes)

    def ensure_node(self, key: str, node_type: NodeType) -> None:
        if key not in self.nodes:
            self.add_node(LineageNode(key=key, node_type=node_type))

    def add_edge(self, edge: LineageEdge) -> None:
        self.ensure_node(
            edge.src,
            self.nodes.get(edge.src, LineageNode(edge.src, NodeType.DATASET)).node_type,
        )
        self.ensure_node(
            edge.dst,
            self.nodes.get(edge.dst, LineageNode(edge.dst, NodeType.DATASET)).node_type,
        )
        self.out_edges.setdefault(edge.src, {}).setdefault(edge.edge_type, set()).add(
            edge.dst
        )
        self.in_edges.setdefault(edge.dst, {}).setdefault(edge.edge_type, set()).add(
            edge.src
        )
        self.edge_metadata[(edge.src, edge.dst, edge.edge_type)] = edge.evidence

    def set_node_type(self, key: str, node_type: NodeType) -> None:
        if key in self.nodes:
            self.nodes[key].node_type = node_type
        else:
            self.add_node(LineageNode(key, node_type))

    def traverse(
        self,
        start: str,
        *,
        direction: str = "downstream",
        edge_types: Optional[Iterable[EdgeType]] = None,
        depth: Optional[int] = None,
    ) -> "LineageGraph":
        if start not in self.nodes:
            return LineageGraph()
        allowed = (
            set(edge_types)
            if edge_types
            else {EdgeType.DERIVES_FROM, EdgeType.PRODUCES, EdgeType.CONSUMES}
        )
        subgraph = LineageGraph()
        queue: deque[Tuple[str, int]] = deque([(start, 0)])
        visited = {start}
        while queue:
            node_key, dist = queue.popleft()
            node = self.nodes[node_key]
            subgraph.add_node(
                LineageNode(node.key, node.node_type, dict(node.attributes))
            )
            iterator = []
            if direction in {"downstream", "both"}:
                iterator.append((self.out_edges, True))
            if direction in {"upstream", "both"}:
                iterator.append((self.in_edges, False))
            for edge_map, forward in iterator:
                for edge_type, neighbors in edge_map.get(node_key, {}).items():
                    if edge_type not in allowed:
                        continue
                    for neighbor in neighbors:
                        src, dst = (
                            (node_key, neighbor) if forward else (neighbor, node_key)
                        )
                        evidence = self.edge_metadata.get((src, dst, edge_type), {})
                        neighbor_node = self.nodes[neighbor]
                        subgraph.add_node(
                            LineageNode(
                                neighbor_node.key,
                                neighbor_node.node_type,
                                dict(neighbor_node.attributes),
                            )
                        )
                        subgraph.add_edge(
                            LineageEdge(src, dst, edge_type, dict(evidence))
                        )
                        if neighbor not in visited and (
                            depth is None or dist + 1 <= depth
                        ):
                            visited.add(neighbor)
                            queue.append((neighbor, dist + 1))
        return subgraph

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "nodes": [
                {
                    "key": node.key,
                    "type": node.node_type.value,
                    "attributes": cast(Dict[str, Any], dict(node.attributes)),
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "src": src,
                    "dst": dst,
                    "type": edge_type.value,
                    "evidence": cast(Dict[str, Any], dict(evidence)),
                }
                for (src, dst, edge_type), evidence in self.edge_metadata.items()
            ],
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, List[Dict[str, Any]]]) -> "LineageGraph":
        graph = cls()
        for node in payload.get("nodes", []):
            graph.add_node(
                LineageNode(
                    key=node["key"],
                    node_type=NodeType(node["type"]),
                    attributes=node.get("attributes", {}),
                )
            )
        for edge in payload.get("edges", []):
            graph.add_edge(
                LineageEdge(
                    src=edge["src"],
                    dst=edge["dst"],
                    edge_type=EdgeType(edge["type"]),
                    evidence=edge.get("evidence", {}),
                )
            )
        return graph
