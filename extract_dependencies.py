#!/usr/bin/env python3
"""Extract dependencies using the current role/context and save outputs.

This script uses SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES when permitted by
the current role, and otherwise falls back to INFORMATION_SCHEMA (view->table).
Results are saved into a folder.
"""

import json
from pathlib import Path
from typing import Any, Dict, cast

from snowcli_tools.dependency import build_dependency_graph, to_dot


def extract_dependencies(
    output_dir: str = "./dependencies",
    database: str | None = None,
    schema: str | None = None,
    account_scope: bool = True,
) -> None:
    """Extract dependencies using current Snowflake CLI profile and save to a folder.

    - Uses ACCOUNT_USAGE when permitted by current role; otherwise falls back.
    - Saves both JSON and DOT files into `output_dir`.
    """
    print("Building dependency graph using current profile/context...")
    graph = build_dependency_graph(
        database=database, schema=schema, account_scope=account_scope
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    json_path = out_path / "dependencies.json"
    dot_path = out_path / "dependencies.dot"

    with open(json_path, "w") as f:
        json.dump(graph, f, indent=2)
    with open(dot_path, "w") as f:
        f.write(to_dot(graph))

    counts = cast(Dict[str, Any], graph.get("counts", {}))
    print(
        f"Extracted {counts.get('edges', 0)} edges across {counts.get('nodes', 0)} objects"
    )
    print(f"Results saved to {json_path} and {dot_path}")


if __name__ == "__main__":
    # Example: use current role/context for the active profile; write into ./dependencies
    extract_dependencies()
