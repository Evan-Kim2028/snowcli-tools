from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

from .graph import LineageGraph, LineageNode
from .utils import TimeoutError, timeout


class ChangeType(Enum):
    DROP = "drop"
    ALTER_SCHEMA = "alter_schema"
    ALTER_DATA_TYPE = "alter_data_type"
    RENAME = "rename"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_LOGIC = "modify_logic"
    PERMISSION_CHANGE = "permission_change"
    REFRESH_SCHEDULE = "refresh_schedule"
    UNKNOWN = "unknown"


class ImpactSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ImpactedObject:
    object_name: str
    object_type: str
    database: str
    schema: str
    impact_type: str
    severity: ImpactSeverity
    distance_from_source: int
    estimated_refresh_time: Optional[float] = None
    affected_users: List[str] = field(default_factory=list)
    affected_roles: List[str] = field(default_factory=list)
    remediation_steps: List[str] = field(default_factory=list)

    def fqn(self) -> str:
        return f"{self.database}.{self.schema}.{self.object_name}"

    def to_dict(self) -> dict:
        return {
            "fqn": self.fqn(),
            "object_type": self.object_type,
            "impact_type": self.impact_type,
            "severity": self.severity.value,
            "distance": self.distance_from_source,
            "estimated_refresh_time": self.estimated_refresh_time,
            "affected_users": self.affected_users,
            "affected_roles": self.affected_roles,
            "remediation_steps": self.remediation_steps,
        }


@dataclass
class ImpactPath:
    source_object: str
    target_object: str
    path: List[str]
    path_length: int
    critical_nodes: List[str]
    bottlenecks: List[str]

    def to_dict(self) -> dict:
        return {
            "source": self.source_object,
            "target": self.target_object,
            "path": self.path,
            "length": self.path_length,
            "critical_nodes": self.critical_nodes,
            "bottlenecks": self.bottlenecks,
        }


@dataclass
class ImpactReport:
    source_object: str
    change_type: ChangeType
    analysis_timestamp: datetime
    total_impacted_objects: int
    impacted_objects: List[ImpactedObject]
    critical_paths: List[ImpactPath]
    impact_summary: Dict[str, Any]
    risk_score: float
    recommendations: List[str]
    notification_list: List[Dict[str, str]]

    def to_dict(self) -> dict:
        return {
            "source_object": self.source_object,
            "change_type": self.change_type.value,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "total_impacted_objects": self.total_impacted_objects,
            "impacted_objects": [obj.to_dict() for obj in self.impacted_objects],
            "critical_paths": [path.to_dict() for path in self.critical_paths],
            "impact_summary": self.impact_summary,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations,
            "notification_list": self.notification_list,
        }


class ImpactAnalyzer:
    def __init__(self, lineage_graph: LineageGraph):
        self.lineage_graph = lineage_graph
        self.nx_graph = self._build_networkx_graph()
        self.object_metadata: Dict[str, Dict] = {}
        self.user_access_map: Dict[str, List[str]] = {}
        self.role_access_map: Dict[str, List[str]] = {}
        # Build reverse index for O(1) downstream lookups
        self.reverse_graph = self.nx_graph.reverse(copy=True)

    def analyze_impact(
        self,
        object_name: str,
        change_type: ChangeType,
        max_depth: int = 10,
        include_upstream: bool = False,
        timeout_seconds: int = 60,
    ) -> ImpactReport:
        if object_name not in self.nx_graph:
            raise ValueError(f"Object {object_name} not found in lineage graph")

        try:
            with timeout(
                timeout_seconds, f"Impact analysis timed out after {timeout_seconds}s"
            ):
                impacted_objects = self._find_impacted_objects(
                    object_name, change_type, max_depth, include_upstream
                )

                critical_paths = self._identify_critical_paths(
                    object_name, impacted_objects
                )

                impact_summary = self._generate_impact_summary(
                    impacted_objects, change_type
                )

                risk_score = self._calculate_risk_score(
                    impacted_objects, critical_paths, change_type
                )

                recommendations = self._generate_recommendations(
                    change_type, impacted_objects, risk_score
                )

                notification_list = self._build_notification_list(impacted_objects)

        except TimeoutError:
            # Return partial results if timeout occurs
            return ImpactReport(
                source_object=object_name,
                change_type=change_type,
                analysis_timestamp=datetime.now(),
                total_impacted_objects=0,
                impacted_objects=[],
                critical_paths=[],
                risk_score=0.0,
                impact_summary={
                    "error": f"Analysis timed out after {timeout_seconds} seconds"
                },
                recommendations=[
                    "Analysis incomplete due to timeout. Consider increasing timeout or reducing max_depth."
                ],
                notification_list=[],
            )

        return ImpactReport(
            source_object=object_name,
            change_type=change_type,
            analysis_timestamp=datetime.now(),
            total_impacted_objects=len(impacted_objects),
            impacted_objects=impacted_objects,
            critical_paths=critical_paths,
            impact_summary=impact_summary,
            risk_score=risk_score,
            recommendations=recommendations,
            notification_list=notification_list,
        )

    def calculate_blast_radius(
        self, object_name: str, max_depth: int = 5
    ) -> Dict[str, Any]:
        if object_name not in self.nx_graph:
            return {"error": f"Object {object_name} not found"}

        downstream = list(nx.descendants(self.nx_graph, object_name))
        upstream = list(nx.ancestors(self.nx_graph, object_name))

        downstream_by_distance: dict[int, list[str]] = {}
        for target in downstream:
            try:
                distance = nx.shortest_path_length(self.nx_graph, object_name, target)
                if distance <= max_depth:
                    if distance not in downstream_by_distance:
                        downstream_by_distance[distance] = []
                    downstream_by_distance[distance].append(target)
            except nx.NetworkXNoPath:
                continue

        return {
            "source": object_name,
            "total_downstream": len(downstream),
            "total_upstream": len(upstream),
            "downstream_by_distance": downstream_by_distance,
            "immediate_downstream": downstream_by_distance.get(1, []),
            "max_distance_analyzed": max_depth,
        }

    def find_single_points_of_failure(self, min_dependent_count: int = 3) -> List[Dict]:
        spofs = []

        for node in self.nx_graph.nodes():
            downstream = list(nx.descendants(self.nx_graph, node))
            if len(downstream) >= min_dependent_count:
                node_data: LineageNode | dict[str, Any] = self.lineage_graph.nodes.get(
                    node, {}
                )

                # Handle both LineageNode objects and dict-based nodes
                if hasattr(node_data, "attributes"):
                    object_type = node_data.attributes.get("object_type", "unknown")
                elif isinstance(node_data, dict):
                    object_type = node_data.get("object_type", "unknown")
                else:
                    object_type = "unknown"

                spof_info = {
                    "object": node,
                    "object_type": object_type,
                    "downstream_count": len(downstream),
                    "downstream_objects": downstream[:10],
                    "criticality_score": self._calculate_criticality(node, downstream),
                }

                spofs.append(spof_info)

        return sorted(spofs, key=lambda x: x["criticality_score"], reverse=True)

    def analyze_change_propagation_time(
        self, object_name: str, refresh_schedules: Optional[Dict[str, float]] = None
    ) -> Dict:
        if object_name not in self.nx_graph:
            return {"error": f"Object {object_name} not found"}

        propagation_times = {}
        downstream = nx.descendants(self.nx_graph, object_name)

        for target in downstream:
            try:
                path = nx.shortest_path(self.nx_graph, object_name, target)
                time_estimate = self._estimate_propagation_time(path, refresh_schedules)
                propagation_times[target] = {
                    "path": path,
                    "estimated_time_hours": time_estimate,
                    "path_length": len(path) - 1,
                }
            except nx.NetworkXNoPath:
                continue

        max_time = max(
            (t["estimated_time_hours"] for t in propagation_times.values()), default=0
        )

        return {
            "source": object_name,
            "total_affected": len(propagation_times),
            "max_propagation_time_hours": max_time,
            "propagation_details": dict(
                sorted(
                    propagation_times.items(),
                    key=lambda x: x[1]["estimated_time_hours"],
                    reverse=True,
                )[:20]
            ),
        }

    def identify_circular_dependencies(self) -> List[List[str]]:
        try:
            cycles = list(nx.simple_cycles(self.nx_graph))
            return cycles
        except (nx.NetworkXError, nx.NetworkXNotImplemented) as e:
            import logging

            logging.warning(f"Could not compute cycles in graph: {e}")
            return []

    def generate_impact_heatmap(
        self, change_scenarios: List[Tuple[str, ChangeType]]
    ) -> Dict:
        heatmap = {}

        for object_name, change_type in change_scenarios:
            if object_name not in self.nx_graph:
                continue

            impact = self.analyze_impact(object_name, change_type, max_depth=5)
            heatmap[object_name] = {
                "change_type": change_type.value,
                "risk_score": impact.risk_score,
                "total_impacted": impact.total_impacted_objects,
                "critical_count": sum(
                    1
                    for obj in impact.impacted_objects
                    if obj.severity == ImpactSeverity.CRITICAL
                ),
            }

        return heatmap

    def export_impact_report(
        self, report: ImpactReport, output_path: Path, format: str = "html"
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "html":
            html_content = self._generate_html_report(report)
            with open(output_path, "w") as f:
                f.write(html_content)

        elif format == "json":
            with open(output_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2)

        elif format == "markdown":
            md_content = self._generate_markdown_report(report)
            with open(output_path, "w") as f:
                f.write(md_content)

        return output_path

    def _build_networkx_graph(self) -> nx.DiGraph:
        graph = nx.DiGraph()

        for node_key, node in self.lineage_graph.nodes.items():
            # Handle both LineageNode objects and dict-based mock objects
            if hasattr(node, "attributes"):
                graph.add_node(node_key, **node.attributes)
            elif isinstance(node, dict):
                # For dict-based nodes (e.g., in tests)
                graph.add_node(node_key, **node)
            else:
                # Fallback for other types
                graph.add_node(node_key)

        for edge in self.lineage_graph.edges:
            edge_type = (
                edge.edge_type.value
                if hasattr(edge.edge_type, "value")
                else edge.edge_type
            )
            graph.add_edge(edge.source, edge.target, type=edge_type)

        return graph

    def _find_impacted_objects(
        self,
        source: str,
        change_type: ChangeType,
        max_depth: int,
        include_upstream: bool,
    ) -> List[ImpactedObject]:
        impacted = []

        # Use BFS to calculate distances efficiently in O(V+E) time
        distances = nx.single_source_shortest_path_length(
            self.nx_graph, source, cutoff=max_depth
        )

        for target, distance in distances.items():
            if target == source:
                continue  # Skip the source node itself

            node_data = self.lineage_graph.nodes.get(target)
            if not node_data:
                continue

            severity = self._determine_severity(distance, change_type, node_data)
            impact_type = self._determine_impact_type(change_type, node_data)

            impacted_obj = ImpactedObject(
                object_name=node_data.attributes.get("name", target),
                object_type=node_data.attributes.get("object_type", "unknown"),
                database=node_data.attributes.get("database", ""),
                schema=node_data.attributes.get("schema", ""),
                impact_type=impact_type,
                severity=severity,
                distance_from_source=distance,
                remediation_steps=self._suggest_remediation(change_type, node_data),
            )

            impacted.append(impacted_obj)

        if include_upstream:
            upstream = nx.ancestors(self.nx_graph, source)
            for target in upstream:
                try:
                    distance = nx.shortest_path_length(self.nx_graph, target, source)
                    if distance > max_depth:
                        continue
                except nx.NetworkXNoPath:
                    continue

                node_data = self.lineage_graph.nodes.get(target)
                if not node_data:
                    continue

                impacted_obj = ImpactedObject(
                    object_name=node_data.attributes.get("name", target),
                    object_type=node_data.attributes.get("object_type", "unknown"),
                    database=node_data.attributes.get("database", ""),
                    schema=node_data.attributes.get("schema", ""),
                    impact_type="upstream_dependency",
                    severity=ImpactSeverity.INFO,
                    distance_from_source=-distance,
                    remediation_steps=[],
                )

                impacted.append(impacted_obj)

        return sorted(
            impacted, key=lambda x: (x.severity.value, x.distance_from_source)
        )

    def _identify_critical_paths(
        self, source: str, impacted_objects: List[ImpactedObject]
    ) -> List[ImpactPath]:
        critical_paths = []

        critical_targets = [
            obj.fqn()
            for obj in impacted_objects
            if obj.severity in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH]
        ][:10]

        for target in critical_targets:
            target_key = None
            for key in self.nx_graph.nodes():
                if target in key:
                    target_key = key
                    break

            if not target_key:
                continue

            try:
                path = nx.shortest_path(self.nx_graph, source, target_key)
                critical_nodes = self._identify_critical_nodes_in_path(path)
                bottlenecks = self._identify_bottlenecks_in_path(path)

                critical_paths.append(
                    ImpactPath(
                        source_object=source,
                        target_object=target,
                        path=path,
                        path_length=len(path) - 1,
                        critical_nodes=critical_nodes,
                        bottlenecks=bottlenecks,
                    )
                )
            except nx.NetworkXNoPath:
                continue

        return critical_paths

    def _determine_severity(
        self, distance: int, change_type: ChangeType, node_data
    ) -> ImpactSeverity:
        base_severity = {
            ChangeType.DROP: ImpactSeverity.CRITICAL,
            ChangeType.ALTER_SCHEMA: ImpactSeverity.HIGH,
            ChangeType.ALTER_DATA_TYPE: ImpactSeverity.HIGH,
            ChangeType.DROP_COLUMN: ImpactSeverity.HIGH,
            ChangeType.RENAME: ImpactSeverity.MEDIUM,
            ChangeType.MODIFY_LOGIC: ImpactSeverity.MEDIUM,
            ChangeType.ADD_COLUMN: ImpactSeverity.LOW,
            ChangeType.PERMISSION_CHANGE: ImpactSeverity.MEDIUM,
            ChangeType.REFRESH_SCHEDULE: ImpactSeverity.LOW,
            ChangeType.UNKNOWN: ImpactSeverity.INFO,
        }.get(change_type, ImpactSeverity.INFO)

        if distance == 1:
            return base_severity
        elif distance == 2:
            if base_severity == ImpactSeverity.CRITICAL:
                return ImpactSeverity.HIGH
            elif base_severity == ImpactSeverity.HIGH:
                return ImpactSeverity.MEDIUM
            return base_severity
        else:
            if base_severity == ImpactSeverity.CRITICAL:
                return ImpactSeverity.MEDIUM
            elif base_severity == ImpactSeverity.HIGH:
                return ImpactSeverity.LOW
            return ImpactSeverity.INFO

    def _determine_impact_type(self, change_type: ChangeType, node_data) -> str:
        if change_type == ChangeType.DROP:
            return "complete_failure"
        elif change_type in [ChangeType.ALTER_SCHEMA, ChangeType.ALTER_DATA_TYPE]:
            return "schema_mismatch"
        elif change_type == ChangeType.DROP_COLUMN:
            return "missing_column"
        elif change_type == ChangeType.RENAME:
            return "reference_broken"
        elif change_type == ChangeType.MODIFY_LOGIC:
            return "logic_change"
        elif change_type == ChangeType.PERMISSION_CHANGE:
            return "access_denied"
        return "indirect_impact"

    def _suggest_remediation(self, change_type: ChangeType, node_data) -> List[str]:
        remediation = []

        if change_type == ChangeType.DROP:
            remediation.append("Update or remove references to dropped object")
            remediation.append("Consider creating a replacement object")
        elif change_type == ChangeType.ALTER_SCHEMA:
            remediation.append("Update schema references in dependent objects")
            remediation.append("Test data type compatibility")
        elif change_type == ChangeType.DROP_COLUMN:
            remediation.append("Remove column references from queries")
            remediation.append("Update SELECT * queries to explicit column lists")
        elif change_type == ChangeType.RENAME:
            remediation.append("Update object references to use new name")
            remediation.append("Consider creating an alias for backward compatibility")
        elif change_type == ChangeType.PERMISSION_CHANGE:
            remediation.append("Review and update access permissions")
            remediation.append("Notify affected users of permission changes")

        return remediation

    def _calculate_risk_score(
        self,
        impacted_objects: List[ImpactedObject],
        critical_paths: List[ImpactPath],
        change_type: ChangeType,
    ) -> float:
        score = 0.0

        severity_weights = {
            ImpactSeverity.CRITICAL: 1.0,
            ImpactSeverity.HIGH: 0.7,
            ImpactSeverity.MEDIUM: 0.4,
            ImpactSeverity.LOW: 0.2,
            ImpactSeverity.INFO: 0.1,
        }

        for obj in impacted_objects:
            score += severity_weights.get(obj.severity, 0.1)

        score += len(critical_paths) * 0.5

        change_multiplier = {
            ChangeType.DROP: 2.0,
            ChangeType.ALTER_SCHEMA: 1.5,
            ChangeType.ALTER_DATA_TYPE: 1.5,
            ChangeType.DROP_COLUMN: 1.4,
            ChangeType.RENAME: 1.2,
            ChangeType.MODIFY_LOGIC: 1.3,
            ChangeType.PERMISSION_CHANGE: 1.1,
            ChangeType.REFRESH_SCHEDULE: 1.0,
        }.get(change_type, 1.0)

        score *= change_multiplier

        return min(score / 10.0, 1.0)

    def _generate_impact_summary(
        self, impacted_objects: List[ImpactedObject], change_type: ChangeType
    ) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "by_severity": {},
            "by_object_type": {},
            "by_database": {},
            "average_distance": 0,
            "max_distance": 0,
            "direct_impacts": 0,
        }

        for obj in impacted_objects:
            sev = obj.severity.value
            summary["by_severity"][sev] = summary["by_severity"].get(sev, 0) + 1

            obj_type = obj.object_type
            summary["by_object_type"][obj_type] = (
                summary["by_object_type"].get(obj_type, 0) + 1
            )

            db = obj.database
            summary["by_database"][db] = summary["by_database"].get(db, 0) + 1

            if obj.distance_from_source == 1:
                summary["direct_impacts"] += 1

        if impacted_objects:
            distances = [obj.distance_from_source for obj in impacted_objects]
            summary["average_distance"] = sum(distances) / len(distances)
            summary["max_distance"] = max(distances)

        return summary

    def _generate_recommendations(
        self,
        change_type: ChangeType,
        impacted_objects: List[ImpactedObject],
        risk_score: float,
    ) -> List[str]:
        recommendations = []

        if risk_score > 0.7:
            recommendations.append(
                "⚠️ HIGH RISK: Consider breaking this change into smaller increments"
            )
            recommendations.append("Schedule change during maintenance window")
            recommendations.append("Prepare rollback plan before execution")

        if change_type == ChangeType.DROP:
            recommendations.append("Archive object definition before dropping")
            recommendations.append("Verify no active queries reference this object")

        critical_count = sum(
            1 for obj in impacted_objects if obj.severity == ImpactSeverity.CRITICAL
        )

        if critical_count > 0:
            recommendations.append(
                f"Review {critical_count} critical dependencies before proceeding"
            )
            recommendations.append("Test changes in development environment first")

        if len(impacted_objects) > 20:
            recommendations.append(
                "Consider sending advance notification to stakeholders"
            )
            recommendations.append("Document changes in release notes")

        return recommendations

    def _build_notification_list(
        self, impacted_objects: List[ImpactedObject]
    ) -> List[Dict[str, str]]:
        notifications = []
        notified_users = set()

        for obj in impacted_objects:
            if obj.severity in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH]:
                for user in obj.affected_users:
                    if user not in notified_users:
                        notifications.append(
                            {
                                "user": user,
                                "severity": obj.severity.value,
                                "object": obj.fqn(),
                                "impact_type": obj.impact_type,
                            }
                        )
                        notified_users.add(user)

        return notifications

    def _calculate_criticality(self, node: str, downstream: List[str]) -> float:
        downstream_count = len(downstream)

        try:
            betweenness = nx.betweenness_centrality(self.nx_graph).get(node, 0)
        except (nx.NetworkXError, KeyError, ValueError) as e:
            import logging

            logging.debug(f"Could not calculate betweenness centrality for {node}: {e}")
            betweenness = 0

        criticality = (downstream_count / 100.0) + (betweenness * 2)
        return min(criticality, 1.0)

    def _estimate_propagation_time(
        self, path: List[str], refresh_schedules: Optional[Dict[str, float]]
    ) -> float:
        if not refresh_schedules:
            return len(path) * 0.5

        total_time = 0.0
        for node in path:
            total_time += refresh_schedules.get(node, 0.5)

        return total_time

    def _identify_critical_nodes_in_path(self, path: List[str]) -> List[str]:
        critical = []
        for node in path:
            if self.nx_graph.out_degree(node) > 5:
                critical.append(node)
        return critical

    def _identify_bottlenecks_in_path(self, path: List[str]) -> List[str]:
        bottlenecks = []
        for i, node in enumerate(path[:-1]):
            if self.nx_graph.in_degree(path[i + 1]) > 5:
                bottlenecks.append(node)
        return bottlenecks

    def _generate_html_report(self, report: ImpactReport) -> str:
        html_lines = []
        html_lines.append("<!DOCTYPE html>")
        html_lines.append("<html><head>")
        html_lines.append("<title>Impact Analysis Report</title>")
        html_lines.append("<style>")
        html_lines.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html_lines.append(".critical { color: #d32f2f; }")
        html_lines.append(".high { color: #f57c00; }")
        html_lines.append(".medium { color: #fbc02d; }")
        html_lines.append(".low { color: #388e3c; }")
        html_lines.append("table { border-collapse: collapse; width: 100%; }")
        html_lines.append(
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        )
        html_lines.append("th { background-color: #f2f2f2; }")
        html_lines.append("</style>")
        html_lines.append("</head><body>")

        html_lines.append(
            f"<h1>Impact Analysis: {html.escape(report.source_object)}</h1>"
        )
        html_lines.append(
            f"<p>Change Type: <strong>{html.escape(report.change_type.value)}</strong></p>"
        )
        html_lines.append(
            f"<p>Risk Score: <strong>{report.risk_score:.2f}</strong></p>"
        )
        html_lines.append(
            f"<p>Total Impacted: <strong>{report.total_impacted_objects}</strong></p>"
        )

        html_lines.append("<h2>Impact Summary</h2>")
        html_lines.append("<table>")
        html_lines.append("<tr><th>Severity</th><th>Count</th></tr>")
        for severity, count in report.impact_summary.get("by_severity", {}).items():
            html_lines.append(
                f'<tr><td class="{html.escape(severity)}">{html.escape(severity)}</td><td>{count}</td></tr>'
            )
        html_lines.append("</table>")

        html_lines.append("<h2>Recommendations</h2>")
        html_lines.append("<ul>")
        for rec in report.recommendations:
            html_lines.append(f"<li>{html.escape(rec)}</li>")
        html_lines.append("</ul>")

        html_lines.append("<h2>Impacted Objects</h2>")
        html_lines.append("<table>")
        html_lines.append(
            "<tr><th>Object</th><th>Type</th><th>Severity</th><th>Distance</th></tr>"
        )
        for obj in report.impacted_objects[:50]:
            html_lines.append("<tr>")
            html_lines.append(f"<td>{html.escape(obj.fqn())}</td>")
            html_lines.append(f"<td>{html.escape(str(obj.object_type))}</td>")
            html_lines.append(
                f'<td class="{html.escape(obj.severity.value)}">{html.escape(obj.severity.value)}</td>'
            )
            html_lines.append(f"<td>{html.escape(str(obj.distance_from_source))}</td>")
            html_lines.append("</tr>")
        html_lines.append("</table>")

        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    def _generate_markdown_report(self, report: ImpactReport) -> str:
        md = []
        md.append(f"# Impact Analysis Report: {report.source_object}\n")
        md.append(f"**Change Type:** {report.change_type.value}\n")
        md.append(f"**Risk Score:** {report.risk_score:.2f}\n")
        md.append(f"**Analysis Time:** {report.analysis_timestamp.isoformat()}\n")
        md.append(f"**Total Impacted Objects:** {report.total_impacted_objects}\n\n")

        md.append("## Impact Summary\n")
        md.append("| Severity | Count |\n")
        md.append("|----------|-------|\n")
        for severity, count in report.impact_summary.get("by_severity", {}).items():
            md.append(f"| {severity} | {count} |\n")
        md.append("\n")

        md.append("## Recommendations\n")
        for rec in report.recommendations:
            md.append(f"- {rec}\n")
        md.append("\n")

        md.append("## Critical Paths\n")
        for path in report.critical_paths[:5]:
            md.append(f"- **{path.source_object}** → **{path.target_object}**\n")
            md.append(f"  - Path length: {path.path_length}\n")
            md.append(f"  - Critical nodes: {', '.join(path.critical_nodes[:3])}\n")
        md.append("\n")

        md.append("## Top Impacted Objects\n")
        md.append("| Object | Type | Severity | Distance | Impact Type |\n")
        md.append("|--------|------|----------|----------|-------------|\n")
        for obj in report.impacted_objects[:20]:
            md.append(f"| {obj.fqn()} | {obj.object_type} | ")
            md.append(f"{obj.severity.value} | {obj.distance_from_source} | ")
            md.append(f"{obj.impact_type} |\n")

        return "".join(md)
