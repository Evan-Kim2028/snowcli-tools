#!/usr/bin/env python
"""
Column-Level Lineage Example: "Where does my trading data come from?"

This example shows how to trace data flow at the column level.
Use case: You want to understand how your processed trading data
relates back to the original blockchain events.
"""

from pathlib import Path

try:
    from snowcli_tools.lineage import ColumnLineageExtractor
except ImportError:
    print("Note: Running with mock lineage module for demonstration")

    # Create mock classes for demonstration
    class MockColumnLineageExtractor:
        def __init__(self, **kwargs):
            pass

        def extract_column_lineage(self, sql, target_table):
            class MockLineage:
                def __init__(self):
                    self.transformations = [
                        type(
                            "Trans",
                            (),
                            {
                                "target_column": type(
                                    "Col", (), {"column": "clean_amount"}
                                ),
                                "transformation_type": type(
                                    "Type", (), {"value": "function"}
                                ),
                                "source_columns": [
                                    type("Col", (), {"column": "amount_in"}),
                                    type("Col", (), {"column": "coin_decimals"}),
                                ],
                                "function_name": "POWER",
                            },
                        )(),
                        type(
                            "Trans",
                            (),
                            {
                                "target_column": type(
                                    "Col", (), {"column": "protocol"}
                                ),
                                "transformation_type": type(
                                    "Type", (), {"value": "direct"}
                                ),
                                "source_columns": [
                                    type("Col", (), {"column": "protocol"})
                                ],
                                "function_name": None,
                            },
                        )(),
                    ]

            return MockLineage()

    ColumnLineageExtractor = MockColumnLineageExtractor


def main():
    print("Column-Level Lineage Analysis")
    print("=" * 50)
    print()

    # Simple example: Processing raw trading events into clean data
    sql_example = """
    CREATE TABLE processed_trades AS
    SELECT
        raw_events.protocol,
        raw_events.amount_in,
        coin_info.coin_symbol,
        raw_events.amount_in / POWER(10, coin_info.coin_decimals) as clean_amount
    FROM raw_events
    JOIN coin_info ON raw_events.coin_type = coin_info.coin_type
    """

    try:
        print("SQL Example:")
        print(sql_example)

        print("Analyzing column lineage...")
        extractor = ColumnLineageExtractor(
            default_database="DEFI_SAMPLE_DB", default_schema="PROCESSED"
        )
        lineage = extractor.extract_column_lineage(
            sql_example, target_table="processed_trades"
        )

        print(f"\nFound {len(lineage.transformations)} column transformations")

        # Show only the most interesting transformations
        interesting_transformations = [
            t
            for t in lineage.transformations
            if t.transformation_type.value in ["function", "unknown"]
            or len(t.source_columns) > 1
        ]

        print("\nKey Data Transformations:")
        for trans in interesting_transformations[:3]:  # Show top 3
            print(f"\n  Column: {trans.target_column.column}")
            print(f"    Type: {trans.transformation_type.value}")
            if trans.source_columns:
                sources = [col.column for col in trans.source_columns]
                print(f"    Sources: {', '.join(sources)}")
            if trans.function_name:
                print(f"    Function: {trans.function_name}")

        print("\nSummary:")
        print(
            f"  Direct mappings: {sum(1 for t in lineage.transformations if t.transformation_type.value == 'direct')}"
        )
        calc_fields_count = sum(
            1
            for t in lineage.transformations
            if t.transformation_type.value in ["function", "unknown"]
        )
        print(f"  Calculated fields: {calc_fields_count}")
        print(
            f"  Enriched from joins: "
            f"{sum(1 for t in lineage.transformations if t.transformation_type.value == 'alias')}"
        )

        # Show practical insights
        print("\nKey Insights:")
        print(
            "  The 'clean_amount' field combines two data sources (amount + decimals)"
        )
        print("  Raw blockchain amounts need decimal adjustment to be human-readable")
        print("  Join with coin_info table enriches raw events with metadata")

        # Mention advanced capabilities without overwhelming
        print("\nAdvanced Usage:")
        sample_data_path = Path(__file__).parent.parent / "sample_data"
        print("  This analysis works with your actual SQL and data catalog")
        if sample_data_path.exists():
            print(f"  Sample DeFi pipeline available at: {sample_data_path}")
        else:
            print(f"  Sample data path configured: {sample_data_path} (not present)")
        print("  Export lineage to JSON/HTML for documentation")
        print("  Track confidence levels to identify complex transformations")

    except Exception as e:
        print(f"\nError during analysis: {e}")
        print("This example requires snowcli-tools with lineage module installed")
        print("Using mock data for demonstration purposes")


if __name__ == "__main__":
    main()
