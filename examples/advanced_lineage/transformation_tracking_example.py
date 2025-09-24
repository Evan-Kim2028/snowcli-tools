#!/usr/bin/env python
"""
Example: Transformation Tracking and Analysis

This example demonstrates how to:
1. Track and categorize data transformations
2. Analyze transformation patterns
3. Build transformation chains
4. Export transformation history
"""

from pathlib import Path
from datetime import datetime
from snowcli_tools.lineage import (
    ColumnLineageExtractor,
    TransformationTracker,
    ColumnTransformation,
    QualifiedColumn
)
from snowcli_tools.lineage.column_parser import TransformationType


def main():
    # Initialize the transformation tracker
    tracker = TransformationTracker(storage_path=Path("./transformation_history"))

    print("=" * 60)
    print("Example 1: Tracking Individual Transformations")
    print("=" * 60)

    # Create sample transformations
    transformations = [
        ColumnTransformation(
            source_columns=[
                QualifiedColumn(table="raw_data", column="customer_name",
                              database="STAGING", schema="PUBLIC")
            ],
            target_column=QualifiedColumn(
                table="clean_data", column="customer_name",
                database="ANALYTICS", schema="PUBLIC"
            ),
            transformation_type=TransformationType.FUNCTION,
            transformation_sql="TRIM(UPPER(customer_name))",
            function_name="TRIM",
            confidence=1.0
        ),
        ColumnTransformation(
            source_columns=[
                QualifiedColumn(table="clean_data", column="order_amount",
                              database="ANALYTICS", schema="PUBLIC"),
                QualifiedColumn(table="clean_data", column="tax_rate",
                              database="ANALYTICS", schema="PUBLIC")
            ],
            target_column=QualifiedColumn(
                table="financial_summary", column="total_with_tax",
                database="ANALYTICS", schema="PUBLIC"
            ),
            transformation_type=TransformationType.FUNCTION,
            transformation_sql="order_amount * (1 + tax_rate)",
            confidence=1.0
        ),
        ColumnTransformation(
            source_columns=[
                QualifiedColumn(table="clean_data", column="order_status",
                              database="ANALYTICS", schema="PUBLIC")
            ],
            target_column=QualifiedColumn(
                table="order_metrics", column="is_completed",
                database="ANALYTICS", schema="PUBLIC"
            ),
            transformation_type=TransformationType.CASE,
            transformation_sql="CASE WHEN order_status = 'COMPLETED' THEN 1 ELSE 0 END",
            confidence=0.95
        )
    ]

    # Track each transformation
    for trans in transformations:
        metadata = tracker.track_transformation(
            trans,
            source_object="STAGING.PUBLIC.raw_data",
            target_object="ANALYTICS.PUBLIC.clean_data",
            business_logic="Data cleansing and standardization"
        )
        print(f"\nTracked: {metadata.transformation_id}")
        print(f"  Category: {metadata.category.value}")
        print(f"  Type: {metadata.transformation_type.value}")
        print(f"  Columns: {', '.join(metadata.columns_affected)}")

    # Example 2: Analyze transformation patterns
    print("\n" + "=" * 60)
    print("Example 2: Pattern Analysis")
    print("=" * 60)

    patterns = tracker.analyze_patterns(min_frequency=1)

    print("\nIdentified Patterns:")
    for pattern in patterns:
        print(f"\n  Pattern: {pattern.name}")
        print(f"  Category: {pattern.category.value}")
        print(f"  Frequency: {pattern.frequency}")
        print(f"  Example SQL: {pattern.example[:50]}...")

    # Example 3: Find transformation chains
    print("\n" + "=" * 60)
    print("Example 3: Transformation Chains")
    print("=" * 60)

    # Add more transformations to create a chain
    chain_transformations = [
        ColumnTransformation(
            source_columns=[
                QualifiedColumn(table="source", column="raw_date",
                              database="STAGING", schema="PUBLIC")
            ],
            target_column=QualifiedColumn(
                table="intermediate", column="parsed_date",
                database="STAGING", schema="PUBLIC"
            ),
            transformation_type=TransformationType.FUNCTION,
            transformation_sql="TO_DATE(raw_date, 'YYYY-MM-DD')",
            function_name="TO_DATE",
            confidence=1.0
        ),
        ColumnTransformation(
            source_columns=[
                QualifiedColumn(table="intermediate", column="parsed_date",
                              database="STAGING", schema="PUBLIC")
            ],
            target_column=QualifiedColumn(
                table="final", column="fiscal_quarter",
                database="ANALYTICS", schema="PUBLIC"
            ),
            transformation_type=TransformationType.FUNCTION,
            transformation_sql="QUARTER(parsed_date)",
            function_name="QUARTER",
            confidence=1.0
        )
    ]

    for trans in chain_transformations:
        tracker.track_transformation(
            trans,
            source_object=trans.source_columns[0].fqn() if trans.source_columns else "unknown",
            target_object=trans.target_column.fqn()
        )

    chains = tracker.find_transformation_chains(
        start_column="STAGING.PUBLIC.source.raw_date",
        max_depth=5
    )

    print(f"\nFound {len(chains)} transformation chains")
    for chain in chains:
        print(f"\n  Chain ID: {chain.chain_id}")
        print(f"  Start: {chain.start_point}")
        print(f"  End: {chain.end_point}")
        print(f"  Length: {chain.total_transformations}")
        print(f"  Complexity: {chain.complexity_score:.2f}")
        print(f"  Categories: {', '.join([c.value for c in chain.categories_involved])}")

    # Example 4: Get transformation summary
    print("\n" + "=" * 60)
    print("Example 4: Transformation Summary")
    print("=" * 60)

    summary = tracker.get_transformation_summary()

    print("\nTransformation Statistics:")
    print(f"  Total Transformations: {summary['total_transformations']}")

    print("\n  By Type:")
    for t_type, count in summary['transformation_types'].items():
        print(f"    {t_type}: {count}")

    print("\n  By Category:")
    for category, count in summary['categories'].items():
        print(f"    {category}: {count}")

    print("\n  Top Transformed Columns:")
    for col, count in list(summary['most_transformed_columns'].items())[:5]:
        print(f"    {col}: {count} transformations")

    # Example 5: Export transformation history
    print("\n" + "=" * 60)
    print("Example 5: Exporting Transformation History")
    print("=" * 60)

    # Export as JSON
    json_path = tracker.export_transformations(
        Path("./transformation_report.json"),
        format="json"
    )
    print(f"\nExported to JSON: {json_path}")

    # Export as Markdown report
    md_path = tracker.export_transformations(
        Path("./transformation_report.md"),
        format="markdown"
    )
    print(f"Exported to Markdown: {md_path}")

    # Example 6: Performance impact analysis
    print("\n" + "=" * 60)
    print("Example 6: Performance Impact Analysis")
    print("=" * 60)

    high_impact = [
        t for t in tracker.transformation_history
        if t.performance_impact and t.performance_impact > 0.5
    ]

    print(f"\nHigh performance impact transformations: {len(high_impact)}")
    for trans in high_impact:
        print(f"  - {trans.transformation_id}: Impact score {trans.performance_impact:.2f}")
        print(f"    Type: {trans.transformation_type.value}")
        print(f"    Category: {trans.category.value}")

    # Example 7: Data quality rules extraction
    print("\n" + "=" * 60)
    print("Example 7: Data Quality Rules")
    print("=" * 60)

    for trans in tracker.transformation_history:
        if trans.data_quality_rules:
            print(f"\nTransformation: {trans.transformation_id}")
            print(f"  Rules: {', '.join(trans.data_quality_rules)}")


if __name__ == "__main__":
    main()