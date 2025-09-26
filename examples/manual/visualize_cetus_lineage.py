#!/usr/bin/env python3
# ruff: noqa
"""
Visualize CETUS_GENERALIZED_LP_LIVE_DT lineage in a terminal-friendly format
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(
    0, "/Users/evandekim/Documents/snowflake_connector_py_advanced_lineage/src"
)

from snowcli_tools.lineage.builder import LineageBuilder

CATALOG_PATH = Path("/Users/evandekim/Documents/snowflake_connector_py/data_catalogue")


def shorten_name(full_name: str, max_len: int = 40) -> str:
    """Shorten long table names for display."""
    parts = full_name.split(".")
    if len(parts) >= 3:
        # Keep only schema.table
        short = f"{parts[-2]}.{parts[-1]}"
    else:
        short = parts[-1] if parts else full_name

    if len(short) > max_len:
        return short[: max_len - 3] + "..."
    return short


def create_tree_view(
    node_name: str, graph, direction: str = "both", max_depth: int = 3, visited=None
):
    """Create a tree view of dependencies."""
    if visited is None:
        visited = set()

    tree_lines = []

    def add_node(name: str, prefix: str = "", is_last: bool = True, depth: int = 0):
        if depth > max_depth or name in visited:
            if name in visited and depth > 0:
                tree_lines.append(
                    f"{prefix}{'└── ' if is_last else '├── '}[circular ref: {shorten_name(name)}]"
                )
            return

        visited.add(name)

        # Add current node
        if depth == 0:
            tree_lines.append(f"📊 {shorten_name(name)}")
        else:
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{shorten_name(name)}")

        # Find connected nodes
        upstream = []
        downstream = []

        for edge in graph.edges:
            if direction in ["upstream", "both"] and edge.target == name:
                upstream.append(edge.source)
            if direction in ["downstream", "both"] and edge.source == name:
                downstream.append(edge.target)

        # Add upstream nodes
        if upstream and direction in ["upstream", "both"]:
            if depth == 0:
                tree_lines.append("│")
                tree_lines.append("├─📥 UPSTREAM (data sources)")

            for i, up_node in enumerate(upstream):
                is_last_up = (i == len(upstream) - 1) and not (
                    downstream and direction == "both"
                )
                new_prefix = prefix + ("│   " if not is_last else "    ")
                if depth == 0:
                    new_prefix = "│   "
                add_node(up_node, new_prefix, is_last_up, depth + 1)

        # Add downstream nodes
        if downstream and direction in ["downstream", "both"]:
            if depth == 0:
                tree_lines.append("│")
                tree_lines.append("└─📤 DOWNSTREAM (dependent objects)")

            for i, down_node in enumerate(downstream):
                is_last_down = i == len(downstream) - 1
                new_prefix = prefix + ("    " if is_last else "    ")
                if depth == 0:
                    new_prefix = "    "
                add_node(down_node, new_prefix, is_last_down, depth + 1)

    add_node(node_name)
    return tree_lines


def create_box_flow_diagram(center_node: str, graph):
    """Create a box-style flow diagram."""
    lines = []

    # Find direct connections
    upstream = []
    downstream = []

    for edge in graph.edges:
        if edge.target == center_node:
            upstream.append(edge.source)
        elif edge.source == center_node:
            downstream.append(edge.target)

    # Calculate box widths
    max_width = 50

    lines.append("=" * 80)
    lines.append("LINEAGE FLOW DIAGRAM")
    lines.append("=" * 80)
    lines.append("")

    # Upstream section
    if upstream:
        lines.append("    📥 UPSTREAM SOURCES")
        lines.append("    " + "─" * 40)

        for i, node in enumerate(upstream[:10]):  # Limit to 10 for readability
            short = shorten_name(node, 35)
            lines.append(f"    [{i+1:2}] {short}")

        if len(upstream) > 10:
            lines.append(f"    ... and {len(upstream)-10} more")

        lines.append("")
        lines.append("              ↓ ↓ ↓")
        lines.append("")

    # Center node
    center_short = shorten_name(center_node, max_width - 4)
    box_width = len(center_short) + 4
    lines.append("    ┌" + "─" * box_width + "┐")
    lines.append(f"    │ 🎯 {center_short} │")
    lines.append("    └" + "─" * box_width + "┘")

    # Downstream section
    if downstream:
        lines.append("")
        lines.append("              ↓ ↓ ↓")
        lines.append("")
        lines.append("    📤 DOWNSTREAM TARGETS")
        lines.append("    " + "─" * 40)

        for i, node in enumerate(downstream[:10]):
            short = shorten_name(node, 35)
            lines.append(f"    [{i+1:2}] {short}")

        if len(downstream) > 10:
            lines.append(f"    ... and {len(downstream)-10} more")

    lines.append("")
    lines.append("=" * 80)

    # Statistics
    lines.append("📊 Statistics:")
    lines.append(f"   • Total upstream dependencies: {len(upstream)}")
    lines.append(f"   • Total downstream dependencies: {len(downstream)}")
    lines.append(f"   • Total connections: {len(upstream) + len(downstream)}")

    return lines


def create_ascii_flow(center_node: str, graph):
    """Create an ASCII art flow diagram."""
    lines = []

    # Find connections
    upstream = []
    downstream = []

    for edge in graph.edges:
        if edge.target == center_node:
            upstream.append(edge.source)
        elif edge.source == center_node:
            downstream.append(edge.target)

    lines.append("\n" + "▀" * 80)
    lines.append(f"  DATA FLOW THROUGH: {shorten_name(center_node)}")
    lines.append("▄" * 80 + "\n")

    # Create flow visualization
    if upstream:
        lines.append("  🔹 DATA SOURCES (Upstream)")
        lines.append("  " + "─" * 76)

        # Group by schema
        by_schema = defaultdict(list)
        for node in upstream:
            parts = node.split(".")
            schema = parts[-2] if len(parts) >= 2 else "DEFAULT"
            table = parts[-1]
            by_schema[schema].append(table)

        for schema, tables in sorted(by_schema.items()):
            lines.append(f"\n  📁 {schema}/")
            for table in sorted(tables)[:5]:
                lines.append(f"      • {table[:40]}")
            if len(tables) > 5:
                lines.append(f"      ... ({len(tables)-5} more tables)")

    # Center with flow arrows
    lines.append("\n" + " " * 30 + "╔═══════════╗")
    lines.append(" " * 30 + "║     ↓     ║")
    lines.append(" " * 30 + "║     ↓     ║")
    lines.append(" " * 30 + "╚═══════════╝")

    center_display = shorten_name(center_node, 40)
    padding = (50 - len(center_display)) // 2
    lines.append("\n" + " " * padding + "╔" + "═" * (len(center_display) + 4) + "╗")
    lines.append(" " * padding + "║ " + f"🎯 {center_display}" + " ║")
    lines.append(" " * padding + "╚" + "═" * (len(center_display) + 4) + "╝")

    if downstream:
        lines.append("\n" + " " * 30 + "╔═══════════╗")
        lines.append(" " * 30 + "║     ↓     ║")
        lines.append(" " * 30 + "║     ↓     ║")
        lines.append(" " * 30 + "╚═══════════╝")

        lines.append("\n  🔸 CONSUMING OBJECTS (Downstream)")
        lines.append("  " + "─" * 76)

        # Group by schema
        by_schema = defaultdict(list)
        for node in downstream:
            parts = node.split(".")
            schema = parts[-2] if len(parts) >= 2 else "DEFAULT"
            table = parts[-1]
            by_schema[schema].append(table)

        for schema, tables in sorted(by_schema.items()):
            lines.append(f"\n  📁 {schema}/")
            for table in sorted(tables)[:5]:
                lines.append(f"      • {table[:40]}")
            if len(tables) > 5:
                lines.append(f"      ... ({len(tables)-5} more tables)")

    lines.append("\n" + "▀" * 80)

    return lines


def main():
    # Build lineage
    print("🔄 Building lineage graph...")
    builder = LineageBuilder(CATALOG_PATH)
    result = builder.build()

    # Find CETUS table
    cetus_node = None
    dex_trades_node = None

    for node_key in result.graph.nodes:
        if "CETUS_GENERALIZED_LP_LIVE_DT" in node_key:
            cetus_node = node_key
        if "DEX_TRADES_STABLE" in node_key and "::task" not in node_key:
            dex_trades_node = node_key

    if not cetus_node:
        print("❌ CETUS_GENERALIZED_LP_LIVE_DT not found in lineage")
        return

    print(f"✅ Found: {cetus_node}\n")

    # Generate different visualizations
    print("\n" + "🌳 " + "=" * 76 + " 🌳")
    print("  TREE VIEW - CETUS_GENERALIZED_LP_LIVE_DT")
    print("🌳 " + "=" * 76 + " 🌳\n")

    tree = create_tree_view(cetus_node, result.graph, direction="both", max_depth=2)
    for line in tree:
        print(line)

    print("\n")

    # Box flow diagram
    box_lines = create_box_flow_diagram(cetus_node, result.graph)
    for line in box_lines:
        print(line)

    print("\n")

    # ASCII flow
    ascii_lines = create_ascii_flow(cetus_node, result.graph)
    for line in ascii_lines:
        print(line)

    # Also show DEX_TRADES_STABLE if found
    if dex_trades_node:
        print("\n\n" + "🌊 " + "=" * 76 + " 🌊")
        print("  BONUS: DEX_TRADES_STABLE LINEAGE")
        print("🌊 " + "=" * 76 + " 🌊\n")

        # Show simplified view for dex_trades
        upstream = []
        downstream = []

        for edge in result.graph.edges:
            if edge.target == dex_trades_node:
                upstream.append(shorten_name(edge.source, 30))
            elif edge.source == dex_trades_node:
                downstream.append(shorten_name(edge.target, 30))

        if upstream:
            print("📥 FEEDS FROM:")
            for i, node in enumerate(upstream[:8], 1):
                print(f"   {i:2}. {node}")
            if len(upstream) > 8:
                print(f"   ... and {len(upstream)-8} more sources")

        print("\n🎯 DEX_TRADES_STABLE")

        if downstream:
            print("\n📤 FEEDS INTO:")
            for i, node in enumerate(downstream[:8], 1):
                print(f"   {i:2}. {node}")
            if len(downstream) > 8:
                print(f"   ... and {len(downstream)-8} more targets")


if __name__ == "__main__":
    main()
