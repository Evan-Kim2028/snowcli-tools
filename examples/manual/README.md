# Manual Snowflake Lineage Scripts

This directory contains ad-hoc scripts that were previously sitting in the
repository root. They are not part of the automated test suite; instead they
serve as manual diagnostics or compatibility checks while iterating on the
lineage APIs.

Scripts:
- `test_advanced_features.py` – exercises advanced lineage extractors against a
  local catalogue.
- `test_real_world_compatibility.py` – ensures the legacy `LineageGraph`
  façade still behaves like the original API.
- `verify_api_compatibility.py` – quick import/check script for backward
  compatibility.
- `visualize_cetus_lineage.py` – terminal renderer for CETUS lineage data.

These scripts assume you have the catalogue and sample data on disk. Update the
paths at the top of each file before running them locally.
