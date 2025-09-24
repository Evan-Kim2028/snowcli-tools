#!/usr/bin/env python3
"""Example: Build a Snowflake data catalog via Python API and CLI.

This script demonstrates:
1) Using the Python API to build a catalog for the sample DeFi dataset
2) The equivalent CLI commands

Prereqs:
- Configure a Snowflake CLI connection (e.g., `uv run snow connection add ...`)
- Set up the sample dataset: python examples/sample_data/setup_sample_data.py
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
    # Use sample data catalog directory
    out_dir = Path("./sample_data_catalog")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve build_catalog dynamically to avoid import issues when running from repo
    snowcli_tools = importlib.import_module("snowcli_tools")
    build_catalog = getattr(snowcli_tools, "build_catalog")

    # Build a catalog for the DeFi sample database
    print("Building catalog for DEFI_SAMPLE_DB...")
    totals = build_catalog(
        output_dir=str(out_dir),
        database="DEFI_SAMPLE_DB",  # Sample database
        account_scope=False,  # Focus on sample DB only
        output_format="json",  # Human-readable JSON
        include_ddl=True,  # Include DDL for complete metadata
        max_ddl_concurrency=4,  # Reasonable concurrency for sample data
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
    print("\nEquivalent CLI examples for the sample dataset:\n")

    print("# Build catalog for the DeFi sample database")
    print("uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -o ./sample_data_catalog")

    print("\n# Build catalog for specific schema (analytics layer)")
    print(
        "uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -s ANALYTICS -o ./analytics_catalog"
    )

    print("\n# Build catalog for processed layer (fact tables)")
    print(
        "uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -s PROCESSED -o ./processed_catalog"
    )

    print("\n# JSONL output (good for data ingestion)")
    print(
        "uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -o ./sample_data_catalog --format jsonl"
    )

    print("\n# Disable DDL extraction (faster but less complete)")
    print(
        "uv run snowflake-cli catalog -d DEFI_SAMPLE_DB -o ./sample_data_catalog --no-include-ddl"
    )

    print("\n# Build across entire account (if you have access)")
    print("uv run snowflake-cli catalog -a -o ./account_catalog")


if __name__ == "__main__":
    run_python_example()
    print_cli_examples()
