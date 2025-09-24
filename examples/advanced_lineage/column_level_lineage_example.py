#!/usr/bin/env python
"""
Example: Column-Level Lineage Analysis

This example demonstrates how to:
1. Extract column-level lineage from SQL statements
2. Track data flow at the column granularity
3. Visualize column dependencies
"""

from pathlib import Path
from snowcli_tools.lineage import ColumnLineageExtractor, ColumnLineageGraph


def main():
    # Example 1: Simple SELECT with column transformations
    simple_sql = """
    CREATE VIEW sales_summary AS
    SELECT
        c.customer_id,
        c.customer_name,
        UPPER(c.customer_email) as email,
        SUM(o.order_total) as total_spent,
        COUNT(o.order_id) as order_count,
        MAX(o.order_date) as last_order_date
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_name, c.customer_email
    """

    print("=" * 60)
    print("Example 1: Simple Column Lineage")
    print("=" * 60)

    extractor = ColumnLineageExtractor(
        default_database="SALES_DB",
        default_schema="PUBLIC"
    )

    lineage = extractor.extract_column_lineage(
        simple_sql,
        target_table="sales_summary"
    )

    print(f"\nFound {len(lineage.transformations)} column transformations:")
    for trans in lineage.transformations:
        print(f"\n  Target: {trans.target_column.fqn()}")
        print(f"  Type: {trans.transformation_type.value}")
        if trans.source_columns:
            print(f"  Sources: {[col.fqn() for col in trans.source_columns]}")
        if trans.function_name:
            print(f"  Function: {trans.function_name}")

    # Example 2: Complex transformation with CASE statements
    complex_sql = """
    CREATE TABLE customer_segments AS
    SELECT
        customer_id,
        customer_name,
        CASE
            WHEN total_spent > 10000 THEN 'VIP'
            WHEN total_spent > 5000 THEN 'Premium'
            WHEN total_spent > 1000 THEN 'Regular'
            ELSE 'Basic'
        END as customer_segment,
        total_spent * 0.1 as loyalty_points,
        DATEDIFF(day, first_order_date, last_order_date) as customer_lifetime_days
    FROM sales_summary
    """

    print("\n" + "=" * 60)
    print("Example 2: Complex Transformations")
    print("=" * 60)

    lineage2 = extractor.extract_column_lineage(
        complex_sql,
        target_table="customer_segments"
    )

    print(f"\nTransformation Summary:")
    transformation_types = {}
    for trans in lineage2.transformations:
        t_type = trans.transformation_type.value
        transformation_types[t_type] = transformation_types.get(t_type, 0) + 1

    for t_type, count in transformation_types.items():
        print(f"  {t_type}: {count}")

    # Example 3: Tracking column dependencies
    print("\n" + "=" * 60)
    print("Example 3: Column Dependencies")
    print("=" * 60)

    # Find all columns that depend on 'total_spent'
    source_column = "SALES_DB.PUBLIC.sales_summary.total_spent"
    downstream = lineage2.get_downstream_columns(source_column)

    if downstream:
        print(f"\nColumns that depend on {source_column}:")
        for col in downstream:
            print(f"  - {col}")

    # Example 4: Export lineage graph
    print("\n" + "=" * 60)
    print("Example 4: Exporting Column Lineage")
    print("=" * 60)

    output_data = {
        "transformations": [t.to_dict() for t in lineage.transformations],
        "dependencies": lineage.column_dependencies,
        "issues": lineage.issues
    }

    print("\nColumn lineage exported with:")
    print(f"  - {len(lineage.transformations)} transformations")
    print(f"  - {len(lineage.column_dependencies)} column dependencies")
    print(f"  - {len(lineage.issues)} parsing issues")

    # Example 5: Analyze transformation confidence
    print("\n" + "=" * 60)
    print("Example 5: Transformation Confidence Analysis")
    print("=" * 60)

    high_confidence = [t for t in lineage.transformations if t.confidence >= 0.8]
    low_confidence = [t for t in lineage.transformations if t.confidence < 0.8]

    print(f"\nHigh confidence transformations: {len(high_confidence)}")
    print(f"Low confidence transformations: {len(low_confidence)}")

    if low_confidence:
        print("\nTransformations needing review:")
        for trans in low_confidence:
            print(f"  - {trans.target_column.column}: {trans.transformation_type.value}")


if __name__ == "__main__":
    main()