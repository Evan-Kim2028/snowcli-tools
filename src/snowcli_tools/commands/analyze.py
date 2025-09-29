"""Analysis-oriented command implementations."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional, Tuple

import anyio
import click
from rich.console import Console

from ..config import get_config
from ..context import create_service_context
from ..errors import UnifiedErrorFormatter
from ..lineage import LineageQueryService
from ..lineage.graph import LineageGraph, LineageNode
from ..lineage.identifiers import QualifiedName, parse_table_name
from ..lineage.queries import LineageQueryResult
from ..logging import StructuredLogger
from ..models import DependencyGraph
from ..pipelines.dependency import DependencyOptions, DependencyPipeline
from ..service_layer.dependency import DependencyService
from ..snow_cli import SnowCLIError
from .registry import CommandDescriptor, registry
from .utils import DefaultCommandGroup

LINEAGE_SERVICE_CLASS = LineageQueryService

console = Console()
formatter = UnifiedErrorFormatter()
logger = StructuredLogger(__name__)


@click.group(name="analyze", cls=DefaultCommandGroup, default_command="dependencies")
def analyze() -> None:
    """Analytical commands for lineage and dependencies."""


registry.register_group(analyze)


@analyze.command(name="dependencies")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help=(
        "Output path. Defaults to './dependencies' directory. If a directory is provided, a default filename is used."
    ),
)
@click.option("--format", "-f", type=click.Choice(["json", "dot"]), default="json")
@click.option("--database", help="Restrict to a database (optional)")
@click.option("--schema", help="Restrict to a schema (optional)")
@click.option(
    "--account",
    "-a",
    is_flag=True,
    help="Use ACCOUNT_USAGE scope (broader coverage)",
)
def dependencies_command(
    output: Optional[str],
    format: str,
    database: Optional[str],
    schema: Optional[str],
    account: bool,
) -> None:
    """Create a dependency graph of Snowflake objects."""

    context = create_service_context()
    service = DependencyService(context=context)
    if output:
        cache_dir = (
            Path(output).parent if Path(output).suffix else Path(output)
        ) / ".cache"
    else:
        cache_dir = Path("./dependencies/.cache")
    start = perf_counter()
    try:
        options = DependencyOptions(
            database=database,
            schema=schema,
            account_scope=account,
        )
        pipeline = DependencyPipeline(service, cache_dir=cache_dir)
        graph = anyio.run(pipeline.execute, options)
        duration = perf_counter() - start
        logger.log_tool_execution(
            "analyze.dependencies",
            duration,
            True,
            database=database,
            schema=schema,
            account_scope=account,
        )
        payload = (
            json.dumps(graph.model_dump(by_alias=True), indent=2)
            if format == "json"
            else service.to_dot(graph)
        )

        default_dir = Path("./dependencies")
        if not output:
            out_dir = default_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / (
                "dependencies.json" if format == "json" else "dependencies.dot"
            )
        else:
            path = Path(output)
            if path.exists() and path.is_dir():
                out_path = path / (
                    "dependencies.json" if format == "json" else "dependencies.dot"
                )
            elif path.suffix.lower() in (".json", ".dot"):
                out_path = path
            else:
                path.mkdir(parents=True, exist_ok=True)
                out_path = path / (
                    "dependencies.json" if format == "json" else "dependencies.dot"
                )

            out_path.write_text(payload, encoding="utf-8")
        console.print(f"[green]✓[/green] Dependency graph written to {out_path}")
    except SnowCLIError as exc:
        duration = perf_counter() - start
        logger.log_tool_execution(
            "analyze.dependencies",
            duration,
            False,
            database=database,
            schema=schema,
            account_scope=account,
            error=str(exc),
        )
        console.print(formatter.format_for_cli(exc))
        raise SystemExit(1)


registry.register(
    CommandDescriptor(
        name="dependencies",
        group="analyze",
        cli_handler=dependencies_command,
        description="Generate dependency graphs",
        schema=DependencyGraph,
    )
)


@analyze.group(name="lineage")
def lineage_group() -> None:
    """Lineage graph utilities backed by the local catalog."""


registry.register(
    CommandDescriptor(
        name="lineage",
        group="analyze",
        cli_handler=lineage_group,
        description="Lineage exploration commands",
    )
)


@lineage_group.command(name="rebuild")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing JSON/JSONL exports",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
def rebuild_command(catalog_dir: str, cache_dir: str) -> None:
    """Parse catalog JSON and rebuild the cached lineage graph."""

    from .. import cli as cli_module

    service_cls = getattr(cli_module, "LineageQueryService", LINEAGE_SERVICE_CLASS)
    service = service_cls(catalog_dir, cache_dir)
    console.print(
        f"[blue]🧭[/blue] Rebuilding lineage graph from [cyan]{catalog_dir}[/cyan]"
    )
    console.print(f"[blue]ℹ[/blue] Cache directory: [cyan]{service.cache_dir}[/cyan]")
    result = service.build(force=True)
    totals = result.audit.totals()
    console.print(
        " | ".join(
            [
                f"Objects: {totals.get('objects', 0)}",
                f"Parsed: {totals.get('parsed', 0)}",
                f"Missing SQL: {totals.get('missing_sql', 0)}",
                f"Parse errors: {totals.get('parse_error', 0)}",
                f"Unknown refs: {len(result.audit.unknown_references)}",
            ]
        )
    )


def _traverse_lineage(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    direction: str,
    depth: int,
    output_format: str,
    output: Optional[str],
) -> None:
    from .. import cli as cli_module

    service_cls = getattr(cli_module, "LineageQueryService", LINEAGE_SERVICE_CLASS)
    service = service_cls(catalog_dir, cache_dir)
    cfg = get_config()
    default_db = cfg.snowflake.database
    default_schema = cfg.snowflake.schema
    qn = parse_table_name(object_name).with_defaults(default_db, default_schema)
    base_object_key = qn.key()
    candidate_keys = [base_object_key]
    if not base_object_key.endswith("::task"):
        candidate_keys.append(f"{base_object_key}::task")

    result: Optional[LineageQueryResult] = None
    resolved_key: Optional[str] = None

    for candidate in candidate_keys:
        try:
            result = service.object_subgraph(
                candidate, direction=direction, depth=depth
            )
            resolved_key = candidate
            break
        except KeyError:
            continue

    if result is None or resolved_key is None:
        try:
            cached = service.load_cached()
        except FileNotFoundError:
            console.print(
                "[red]✗[/red] Lineage graph not available. Run `sct analyze lineage rebuild` first."
            )
            raise SystemExit(1)

        matches = find_matches_by_partial_name(object_name, cached.graph)

        if not matches:
            console.print(
                f"[red]✗[/red] No matches found for '{object_name}' in lineage graph"
            )
            console.print(
                "[dim]💡[/dim] Try using the fully qualified name (database.schema.object)."
            )
            raise SystemExit(1)

        resolved_key, result = resolve_partial_match(
            matches,
            object_name,
            base_object_key,
            qn,
            cached.graph,
            service,
            direction,
            depth,
        )

        if result is None or resolved_key is None:
            raise SystemExit(1)

    assert result is not None
    assert resolved_key is not None

    graph = result.graph
    direction_desc = {
        "upstream": "depends on",
        "downstream": "is used by",
        "both": "is connected to",
    }[direction]

    if output and output_format in ["json", "html"]:
        if output_format == "json":
            output_path = Path(output)
            output_path.write_text(json.dumps(service_cls.to_json(graph), indent=2))
            console.print(f"[green]✓[/green] Lineage JSON written to {output_path}")
        else:
            html_path = Path(output)
            full_html_path = service_cls.to_html(
                graph,
                html_path,
                title=f"{direction.title()} Lineage: {resolved_key}",
                root_key=resolved_key,
            )
            console.print(
                f"[green]✓[/green] Interactive HTML lineage written to {full_html_path}"
            )
        return

    if output_format == "json" and not output:
        json_dir = Path("lineage/json")
        json_dir.mkdir(parents=True, exist_ok=True)
        safe_name = resolved_key.replace(".", "_").replace("::", "_")
        json_filename = f"{direction}_{safe_name}.json"
        json_path = json_dir / json_filename
        json_path.write_text(json.dumps(service_cls.to_json(graph), indent=2))
        console.print(f"[blue]💾[/blue] Lineage JSON auto-saved to {json_path}")

    if output_format == "json":
        console.print_json(data=service_cls.to_json(graph))
        return

    console.print(
        f"[blue]🔗[/blue] {direction.title()} lineage for [cyan]{resolved_key}[/cyan]"
    )
    console.print(
        f"[blue]📏[/blue] Depth: {depth} | Nodes: {len(graph.nodes)} | Edges: {len(graph.edge_metadata)}"
    )

    if not graph.nodes:
        console.print(f"[yellow]⚠[/yellow] No {direction} lineage found")
        return

    by_type: Dict[str, List[LineageNode]] = {}
    for node in graph.nodes.values():
        node_type = node.node_type.value
        by_type.setdefault(node_type, []).append(node)

    for node_type, nodes in sorted(by_type.items()):
        plural = "s" if len(nodes) != 1 else ""
        in_catalog = sum(1 for n in nodes if n.attributes.get("in_catalog") == "true")
        console.print(
            f"[blue]📊[/blue] {len(nodes)} {node_type}{plural} ({in_catalog} in catalog)"
        )

    if graph.edge_metadata:
        console.print(f"\n[blue]🔗[/blue] Connections ({direction_desc}):")
        for (src, dst, edge_type), _ in sorted(graph.edge_metadata.items()):
            src_name = graph.nodes[src].attributes.get("name", src.split(".")[-1])
            dst_name = graph.nodes[dst].attributes.get("name", dst.split(".")[-1])
            console.print(f"  - {src_name} → {dst_name} [{edge_type.value}]")


@lineage_group.command(name="neighbors")
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=3,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def neighbors_command(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show upstream AND downstream lineage for a Snowflake object."""

    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "both", depth, format, output
    )


@lineage_group.command(name="upstream")
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=5,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def upstream_command(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show upstream lineage for a Snowflake object."""

    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "upstream", depth, format, output
    )


@lineage_group.command(name="downstream")
@click.argument("object_name")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--depth",
    "-d",
    type=int,
    default=5,
    show_default=True,
    help="Maximum traversal depth (0 = only the object itself)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    show_default=True,
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (for JSON/HTML formats)",
)
def downstream_command(
    object_name: str,
    catalog_dir: str,
    cache_dir: str,
    depth: int,
    format: str,
    output: Optional[str],
) -> None:
    """Show downstream lineage for a Snowflake object."""

    _traverse_lineage(
        object_name, catalog_dir, cache_dir, "downstream", depth, format, output
    )


@lineage_group.command(name="audit")
@click.option(
    "--catalog-dir",
    "-c",
    type=click.Path(exists=True),
    default="./data_catalogue",
    show_default=True,
    help="Catalog directory containing lineage graph artifacts",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default="./lineage",
    show_default=True,
    help="Directory to store lineage cache artifacts",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format",
)
def audit_command(catalog_dir: str, cache_dir: str, format: str) -> None:
    """Display lineage parsing coverage and unknown references."""

    service = LineageQueryService(catalog_dir, cache_dir)
    try:
        lineage = service.load_cached()
    except FileNotFoundError:
        console.print(
            "[red]✗[/red] Lineage graph not found. Run `sct analyze lineage rebuild` first."
        )
        raise SystemExit(1)

    console.print(f"[blue]ℹ[/blue] Cache directory: [cyan]{service.cache_dir}[/cyan]")
    audit_report = lineage.audit
    if format == "json":
        console.print_json(data=audit_report.to_dict())
        return

    totals = audit_report.totals()
    console.print(
        " | ".join(
            [
                f"Objects: {totals.get('objects', 0)}",
                f"Parsed: {totals.get('parsed', 0)}",
                f"Missing SQL: {totals.get('missing_sql', 0)}",
                f"Parse errors: {totals.get('parse_error', 0)}",
                f"Unknown refs: {len(audit_report.unknown_references)}",
            ]
        )
    )
    if audit_report.unknown_references:
        console.print("\n[blue]Unresolved references:[/blue]")
        for ref, count in audit_report.unknown_references.items():
            console.print(f"  - {ref}: {count}")


def resolve_partial_match(
    matches: List[str],
    raw_input: str,
    base_object_key: str,
    parsed_input: QualifiedName,
    graph: LineageGraph,
    service: LineageQueryService,
    direction: str,
    depth: int,
) -> Tuple[Optional[str], Optional[LineageQueryResult]]:
    """Select the best match and execute the lineage query."""

    def _try(lineage_key: str) -> Tuple[Optional[str], Optional[LineageQueryResult]]:
        try:
            result = service.object_subgraph(
                lineage_key, direction=direction, depth=depth
            )
            console.print(f"[green]✓[/green] Using lineage node: {lineage_key}")
            return lineage_key, result
        except KeyError:
            return None, None

    normalized_target = base_object_key.lower()
    exact_key_matches = [key for key in matches if key.lower() == normalized_target]
    if exact_key_matches:
        return _try(exact_key_matches[0])

    target_name = parsed_input.name.lower()

    def _object_name(lineage_key: str) -> str:
        return lineage_key.replace("::task", "").split(".")[-1].lower()

    name_matches = [key for key in matches if _object_name(key) == target_name]
    if len(name_matches) == 1:
        return _try(name_matches[0])

    if len(matches) == 1:
        return _try(matches[0])

    chosen = disambiguate_matches(matches, raw_input, graph)
    if chosen is None:
        return None, None
    return _try(chosen)


def find_matches_by_partial_name(partial_name: str, graph: LineageGraph) -> List[str]:
    tokens = [token for token in re.split(r"[\s.]+", partial_name.lower()) if token]
    if not tokens:
        return []

    matches: List[str] = []
    seen: set[str] = set()

    for node_key, node in graph.nodes.items():
        key_lower = node_key.lower()
        haystacks = {key_lower}

        attrs = node.attributes
        db = attrs.get("database", "").lower()
        schema = attrs.get("schema", "").lower()
        name = attrs.get("name", "").lower()

        if name:
            haystacks.add(name)
        if schema and name:
            haystacks.add(f"{schema}.{name}")
        if db and schema and name:
            haystacks.add(f"{db}.{schema}.{name}")

        for haystack in haystacks:
            if haystack and all(token in haystack for token in tokens):
                if node_key not in seen:
                    matches.append(node_key)
                    seen.add(node_key)
                break

    return matches


def disambiguate_matches(
    matches: List[str], raw_input: str, graph: LineageGraph
) -> Optional[str]:
    if not sys.stdin.isatty():
        console.print(
            f"[red]✗[/red] Ambiguous lineage lookup for '{raw_input}'. "
            "Provide a more specific name (e.g. database.schema.object).",
        )
        return None

    console.print(f"[yellow]⚠[/yellow] Found {len(matches)} matches for '{raw_input}':")
    for index, key in enumerate(matches, start=1):
        node = graph.nodes.get(key)
        obj_type = node.attributes.get("object_type") if node else None
        type_label = f" [{obj_type}]" if obj_type else ""
        console.print(f"  {index}. {key}{type_label}")

    choice = click.prompt(
        "Select the desired object",
        type=click.IntRange(1, len(matches)),
        default=1,
    )
    return matches[choice - 1]


# Register lineage subgroup on the analyze group
analyze.add_command(lineage_group)
