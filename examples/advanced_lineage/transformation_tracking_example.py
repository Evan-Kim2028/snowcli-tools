#!/usr/bin/env python
"""
Transformation Tracking Example: "How do I trace DeFi data transformations?"

This example shows how to track transformations in your DeFi pipeline.
Use case: You want to understand how raw blockchain events become
analytics-ready data and identify performance bottlenecks.
"""

from pathlib import Path

try:
    from snowcli_tools.lineage import ColumnTransformation, TransformationTracker
    from snowcli_tools.lineage.column_parser import QualifiedColumn, TransformationType
except ImportError:
    print("Note: Running with mock lineage module for demonstration")
    # Create mock classes for demonstration
    from enum import Enum

    class TransformationType(Enum):  # type: ignore[no-redef]
        FUNCTION = "function"

    class MockQualifiedColumn:
        def __init__(self, table, column, database, schema):
            self.table = table
            self.column = column
            self.database = database
            self.schema = schema

    class MockColumnTransformation:
        def __init__(self, **kwargs):
            self.source_columns = kwargs.get("source_columns", [])
            self.target_column = kwargs.get("target_column")
            self.transformation_type = kwargs.get("transformation_type")
            self.transformation_sql = kwargs.get("transformation_sql")
            self.function_name = kwargs.get("function_name")
            self.confidence = kwargs.get("confidence", 0.9)

    class MockTransformationTracker:
        def __init__(self, **kwargs):
            pass

        def track_transformation(self, transformation, **kwargs):
            return type("Meta", (), {"id": "123", "timestamp": "now"})()

        def analyze_patterns(self, **kwargs):
            return [
                type(
                    "Pattern",
                    (),
                    {
                        "name": "Decimal Adjustment",
                        "category": type("Cat", (), {"value": "arithmetic"}),
                        "frequency": 5,
                        "example": "amount_in / POWER(10, coin_decimals)",
                    },
                )()
            ]

        def find_transformation_chains(self, **kwargs):
            return [
                type(
                    "Chain", (), {"total_transformations": 3, "complexity_score": 6.5}
                )()
            ]

        def get_transformation_summary(self):
            return {
                "total_transformations": 42,
                "transformation_types": {"function": 20, "direct": 15, "alias": 7},
                "categories": ["arithmetic", "string", "date"],
            }

    QualifiedColumn = MockQualifiedColumn
    ColumnTransformation = MockColumnTransformation
    TransformationTracker = MockTransformationTracker


def main():
    print("Transformation Tracking Analysis")
    print("=" * 50)
    print()

    try:
        # Initialize tracker
        tracker = TransformationTracker(
            storage_path=Path("./defi_transformation_history")
        )

        # Example transformation: Raw blockchain amount → Clean USD value
        transformations = [
            # Step 1: Decimal adjustment (most common DeFi transformation)
            ColumnTransformation(
                source_columns=[
                    QualifiedColumn(
                        table="RAW_DEX_EVENTS",
                        column="amount_in",
                        database="DEFI_SAMPLE_DB",
                        schema="RAW",
                    ),
                    QualifiedColumn(
                        table="COIN_INFO",
                        column="coin_decimals",
                        database="DEFI_SAMPLE_DB",
                        schema="PROCESSED",
                    ),
                ],
                target_column=QualifiedColumn(
                    table="DEX_TRADES_STABLE",
                    column="adjusted_amount_in",
                    database="DEFI_SAMPLE_DB",
                    schema="PROCESSED",
                ),
                transformation_type=TransformationType.FUNCTION,
                transformation_sql="amount_in / POWER(10, coin_decimals)",
                function_name="POWER",
                confidence=0.95,
            ),
            # Step 2: USD conversion
            ColumnTransformation(
                source_columns=[
                    QualifiedColumn(
                        table="DEX_TRADES_STABLE",
                        column="adjusted_amount_in",
                        database="DEFI_SAMPLE_DB",
                        schema="PROCESSED",
                    )
                ],
                target_column=QualifiedColumn(
                    table="BTC_DEX_TRADES_USD_DT",
                    column="amount_in_usd",
                    database="DEFI_SAMPLE_DB",
                    schema="ANALYTICS",
                ),
                transformation_type=TransformationType.FUNCTION,
                transformation_sql="adjusted_amount_in * 65000",  # BTC price
                confidence=0.9,
            ),
        ]

        print("Tracking key transformations...")

        # Track transformations with business context
        tracked_transformations = []
        for i, trans in enumerate(transformations):
            if i == 0:
                logic = "Convert raw token amounts to decimal-adjusted values"
                source_obj = "DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS"
                target_obj = "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE"
            else:
                logic = "Apply current market price for USD valuation"
                source_obj = "DEFI_SAMPLE_DB.PROCESSED.DEX_TRADES_STABLE"
                target_obj = "DEFI_SAMPLE_DB.ANALYTICS.BTC_DEX_TRADES_USD_DT"

            metadata = tracker.track_transformation(
                trans,
                source_object=source_obj,
                target_object=target_obj,
                business_logic=logic,
            )
            tracked_transformations.append(metadata)

        print(f"Tracked {len(tracked_transformations)} transformations")

        # Analyze transformation patterns
        patterns = tracker.analyze_patterns(min_frequency=1)

        print("\nTransformation Patterns Found:")
        for pattern in patterns[:3]:  # Show top 3
            print(f"\n  Pattern: {pattern.name}")
            print(f"    Category: {pattern.category.value}")
            print(f"    Used {pattern.frequency} times")
            if pattern.example:
                example_short = (
                    pattern.example[:60] + "..."
                    if len(pattern.example) > 60
                    else pattern.example
                )
                print(f"    Example: {example_short}")

        # Show transformation chains
        chains = tracker.find_transformation_chains(
            start_column="DEFI_SAMPLE_DB.RAW.RAW_DEX_EVENTS.amount_in", max_depth=3
        )

        if chains:
            print("\nTransformation Chain Found:")
            chain = chains[0]  # Show first chain
            print("  Start: Raw blockchain amount")
            print("  End: USD analytics value")
            print(f"  Steps: {chain.total_transformations}")
            print(f"  Complexity: {chain.complexity_score:.1f}/10")

        # Get summary statistics
        summary = tracker.get_transformation_summary()

        print("\nSummary:")
        print(f"  Total transformations tracked: {summary['total_transformations']}")

        if summary["transformation_types"]:
            most_common_type = max(
                summary["transformation_types"], key=summary["transformation_types"].get
            )
            print(f"  Most common type: {most_common_type}")

        if summary["categories"]:
            print(f"  Categories found: {len(summary['categories'])}")

        # Show practical insights
        print("\nKey Insights:")
        print("  Decimal adjustment is critical for DeFi data accuracy")
        print("  Price conversions introduce confidence uncertainty")
        print("  Transformation chains help trace data quality issues")

        # Advanced usage hints
        print("\nAdvanced Usage:")
        sample_data_path = Path(__file__).parent.parent / "sample_data"
        print("  Track transformations across your entire DeFi pipeline")
        print("  Identify performance bottlenecks in complex calculations")
        if sample_data_path.exists():
            print(f"  Sample schema available at: {sample_data_path}")
        else:
            print(f"  Sample data path configured: {sample_data_path} (not present)")
        print("  Export tracking history for compliance documentation")

    except Exception as e:
        print(f"\nError during analysis: {e}")
        print("This example requires snowcli-tools with lineage module installed")
        print("Using mock data for demonstration purposes")


if __name__ == "__main__":
    main()
