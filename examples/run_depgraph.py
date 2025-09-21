"""Example: Build a lineage cache and export focused lineage views.

Usage:
  # 1) Build a catalog first (see README for catalog options)
  uv run snowflake-cli catalog --database MY_DB --output-dir ./data_catalogue

  # 2) Run this example to rebuild the lineage cache and emit JSON/HTML outputs
  uv run python examples/run_depgraph.py \
    --catalog-dir ./data_catalogue \
    --object PIPELINE.RAW.VW_SAMPLE \
    --direction both \
    --depth 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from snowcli_tools.lineage import LineageQueryService
from snowcli_tools.lineage.queries import LineageQueryResult


def build_cache(service: LineageQueryService) -> None:
    """Ensure the lineage cache is populated from the catalog."""
    console_prefix = "[lineage-example]"
    print(f"{console_prefix} Building lineage cache at {service.cache_dir}...")
    service.build(force=True)
    print(f"{console_prefix} Cache ready: {service.graph_path}")


def export_outputs(
    result: LineageQueryResult,
    output_dir: Path,
    object_key: str,
    direction: str,
) -> None:
    """Write JSON and HTML representations of the lineage subgraph."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{direction}_{object_key.replace('.', '_')}.json"
    json_payload = LineageQueryService.to_json(result.graph)
    json_path.write_text(json.dumps(json_payload, indent=2))
    print(f"[lineage-example] JSON saved to {json_path}")

    html_path = output_dir / f"{direction}_{object_key.replace('.', '_')}.html"
    LineageQueryService.to_html(
        result.graph,
        html_path,
        title=f"{direction.title()} lineage for {object_key}",
        root_key=object_key,
    )
    print(f"[lineage-example] HTML saved to {html_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lineage query example")
    parser.add_argument(
        "--catalog-dir",
        type=Path,
        default=Path("./data_catalogue"),
        help="Path to a catalog directory containing JSON/JSONL exports",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("./lineage"),
        help="Directory to store lineage cache artifacts",
    )
    parser.add_argument(
        "--object",
        required=True,
        help="Fully qualified object name to inspect (e.g. DB.SCHEMA.OBJECT)",
    )
    parser.add_argument(
        "--direction",
        choices=["upstream", "downstream", "both"],
        default="both",
        help="Traversal direction for the lineage query",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Traversal depth (0 = only the object itself)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./lineage/example_outputs"),
        help="Directory to place JSON/HTML lineage artifacts",
    )
    args = parser.parse_args()

    if not args.catalog_dir.exists():
        print(
            f"[lineage-example] Catalog directory {args.catalog_dir} not found. "
            "Run `snowflake-cli catalog` first.",
        )
        sys.exit(1)

    service = LineageQueryService(args.catalog_dir, args.cache_dir)
    build_cache(service)

    try:
        result = service.object_subgraph(
            args.object,
            direction=args.direction,
            depth=args.depth,
        )
    except KeyError as exc:
        print(f"[lineage-example] {exc}")
        sys.exit(1)

    export_outputs(result, args.output_dir, args.object, args.direction)


if __name__ == "__main__":
    main()
