#!/usr/bin/env python3
"""Example: Build a Snowflake data catalog via Python API and CLI.

This script demonstrates:
1) Using the Python API to build a catalog
2) The equivalent CLI commands

Prereqs:
- Configure a Snowflake CLI connection (e.g., `uv run snow connection add ...`)
- Optionally export SNOWFLAKE_PROFILE or pass --profile to the CLI
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

# Ensure local package import works when running directly from repo
sys.path.append(str((Path(__file__).resolve().parents[1] / "src")))


def run_python_example():
    out_dir = Path("./data_catalogue")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve build_catalog dynamically to avoid import issues when running from repo
    snowcli_tools = importlib.import_module("snowcli_tools")
    build_catalog = getattr(snowcli_tools, "build_catalog")

    # Build a catalog for the current database, JSON output
    totals = build_catalog(
        output_dir=str(out_dir),
        database=None,  # current DB
        account_scope=False,  # set True to scan all DBs in the account
        output_format="json",  # or "jsonl" for ingestion-friendly output
        include_ddl=True,  # DDL included by default; set False to skip
        max_ddl_concurrency=8,  # default concurrency for DDL fetches
    )

    # Print summary
    print("Catalog build complete via Python API:")
    print(json.dumps(totals, indent=2))

    # Peek at one of the files
    tables_path = out_dir / "tables.json"
    if tables_path.exists():
        print(f"\nSample from {tables_path}:")
        sample = json.loads(tables_path.read_text())[:3]
        print(json.dumps(sample, indent=2))


def print_cli_examples():
    print("\nEquivalent CLI examples:\n")
    print("# Build catalog for current database (JSON). Uses default ./data_catalogue")
    print("uv run snowflake-cli catalog")

    print("\n# Build catalog for a specific database")
    print("uv run snowflake-cli catalog -d YOUR_DATABASE -o ./data_catalogue_db")

    print("\n# Build across all databases in the account")
    print("uv run snowflake-cli catalog -a -o ./data_catalogue_all")

    print("\n# Disable DDL (included by default)")
    print("uv run snowflake-cli catalog -d YOUR_DATABASE "
          "-o ./data_catalogue_no_ddl --no-include-ddl")

    print("\n# JSONL output for ingestion")
    print("uv run snowflake-cli catalog -d YOUR_DATABASE "
          "-o ./data_catalogue_jsonl --format jsonl")


if __name__ == "__main__":
    run_python_example()
    print_cli_examples()
