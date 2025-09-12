"""Example: Generate a dependency graph.

Usage:
  uv run snowflake-cli depgraph --database PIPELINE_V2_GROOT_DB --format json -o deps.json
  uv run snowflake-cli depgraph --account --format dot -o deps.dot
"""

from snowcli_tools.dependency import build_dependency_graph, to_dot


def main() -> None:
    graph = build_dependency_graph(database=None, schema=None, account_scope=True)
    print(to_dot(graph))


if __name__ == "__main__":
    main()
