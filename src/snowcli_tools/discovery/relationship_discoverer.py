"""
RelationshipDiscoverer - Multi-strategy foreign key detection.

Discovers foreign key relationships that aren't explicitly defined using:
1. Name pattern matching (customer_id → CUSTOMERS table)
2. Value overlap analysis (check if values exist in target column)
"""

import re
from typing import Any

from snowcli_tools.discovery.models import Relationship
from snowcli_tools.snow_cli import SnowCLI


class RelationshipDiscoverer:
    """Discover foreign key relationships using multiple strategies."""

    def __init__(
        self,
        snow_cli: SnowCLI,
        database: str,
        schema: str,
        min_confidence: float = 0.7,
        sample_size: int = 1000,
    ):
        """
        Initialize RelationshipDiscoverer.

        Args:
            snow_cli: SnowCLI instance
            database: Database to search for relationships
            schema: Schema to search for relationships
            min_confidence: Minimum confidence threshold (default: 0.7)
            sample_size: Sample size for value overlap analysis (default: 1000)
        """
        self.snow_cli = snow_cli
        self.database = database
        self.schema = schema
        self.min_confidence = min_confidence
        self.sample_size = sample_size

    def discover_relationships(
        self, table_name: str, columns: list[str]
    ) -> list[Relationship]:
        """
        Discover foreign key relationships for table columns.

        Args:
            table_name: Source table name
            columns: List of column names to analyze

        Returns:
            List of discovered Relationship objects
        """
        candidates = []

        # Strategy 1: Name pattern matching for all columns
        for column_name in columns:
            name_candidates = self._discover_by_name_patterns(table_name, column_name)
            candidates.extend(name_candidates)

        # Strategy 2: Value overlap analysis for high-potential columns
        # (Only for columns that look like IDs to avoid expensive queries)
        for column_name in columns:
            if self._is_id_column(column_name):
                overlap_candidates = self._discover_by_value_overlap(
                    table_name, column_name
                )
                candidates.extend(overlap_candidates)

        # Deduplicate and score
        relationships = self._deduplicate_and_score(candidates)

        # Filter by confidence threshold
        return [r for r in relationships if r.confidence >= self.min_confidence]

    def _is_id_column(self, column_name: str) -> bool:
        """Check if column name suggests it's an ID column."""
        name_lower = column_name.lower()
        return any(
            pattern in name_lower for pattern in ["_id", "_key", "_uuid", "_fk", "_ref"]
        )

    def _discover_by_name_patterns(
        self, table_name: str, column_name: str
    ) -> list[dict]:
        """
        Strategy 1: Name pattern matching.

        Patterns:
        - customer_id → CUSTOMERS.id
        - order_id → ORDERS.id
        - user_uuid → USERS.uuid
        """
        candidates = []

        # Common patterns
        patterns = [
            (r"(.+)_id$", "ID"),  # customer_id → CUSTOMERS.ID
            (r"(.+)_uuid$", "UUID"),  # user_uuid → USERS.UUID
            (r"(.+)_key$", "KEY"),  # order_key → ORDERS.KEY
            (r"fk_(.+)$", "ID"),  # fk_customer → CUSTOMERS.ID
        ]

        for pattern, target_col_suffix in patterns:
            match = re.match(pattern, column_name.lower())
            if match:
                # Extract table name from column
                potential_table = match.group(1).upper()

                # Try common table name variations
                table_variations = [
                    potential_table,  # CUSTOMER
                    potential_table + "S",  # CUSTOMERS
                    "DIM_" + potential_table,  # DIM_CUSTOMER
                    potential_table + "_DIM",  # CUSTOMER_DIM
                ]

                for variant in table_variations:
                    if self._table_exists(variant):
                        candidates.append(
                            {
                                "from_table": table_name,
                                "from_column": column_name,
                                "to_table": variant,
                                "to_column": target_col_suffix,
                                "strategy": "name_pattern",
                                "raw_confidence": 0.6,
                                "evidence": [
                                    f"Column name pattern: {column_name} → {variant}.{target_col_suffix}"
                                ],
                            }
                        )
                        break  # Found match, stop checking variations

        return candidates

    def _discover_by_value_overlap(
        self, table_name: str, column_name: str
    ) -> list[dict]:
        """
        Strategy 2: Value overlap analysis.

        Check if values in source column exist in potential target columns.
        """
        candidates: list[dict[str, Any]] = []

        # Get sample values from source column
        try:
            sample_sql = f"""
                SELECT DISTINCT "{column_name}"
                FROM "{self.database}"."{self.schema}"."{table_name}"
                WHERE "{column_name}" IS NOT NULL
                LIMIT {self.sample_size}
            """
            result = self.snow_cli.run_query(sample_sql, output_format="json")
            if not result.rows:
                return candidates

            source_values = [
                row[column_name] for row in result.rows if row.get(column_name)
            ]
            if not source_values:
                return candidates

        except Exception:
            return candidates

        # Find potential target columns with same data type
        # For simplicity, check common ID column names in other tables
        target_columns = ["ID", "KEY", "UUID"]

        # Get list of tables in schema
        tables = self._get_tables_in_schema()

        for target_table in tables:
            if target_table == table_name:
                continue  # Skip self

            for target_col in target_columns:
                # Check if target table has this column and calculate overlap
                overlap_pct = self._calculate_overlap(
                    target_table, target_col, source_values
                )

                if overlap_pct >= 70:  # 70%+ overlap suggests FK relationship
                    confidence = min(0.95, overlap_pct / 100.0)
                    candidates.append(
                        {
                            "from_table": table_name,
                            "from_column": column_name,
                            "to_table": target_table,
                            "to_column": target_col,
                            "strategy": "value_overlap",
                            "raw_confidence": confidence,
                            "evidence": [
                                f"Value overlap: {overlap_pct:.1f}% of values exist in {target_table}.{target_col}"
                            ],
                        }
                    )

        return candidates

    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in database/schema."""
        try:
            sql = f"""
                SELECT COUNT(*) as cnt
                FROM "{self.database}".INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{self.schema}'
                  AND TABLE_NAME = '{table_name}'
            """
            result = self.snow_cli.run_query(sql, output_format="json")
            return bool(result.rows and int(result.rows[0]["CNT"]) > 0)
        except Exception:
            return False

    def _get_tables_in_schema(self) -> list[str]:
        """Get list of table names in the schema."""
        try:
            sql = f"""
                SELECT TABLE_NAME
                FROM "{self.database}".INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{self.schema}'
                LIMIT 100
            """
            result = self.snow_cli.run_query(sql, output_format="json")
            return [row["TABLE_NAME"] for row in result.rows] if result.rows else []
        except Exception:
            return []

    def _calculate_overlap(
        self, target_table: str, target_column: str, source_values: list
    ) -> float:
        """Calculate percentage of source values that exist in target column."""
        if not source_values:
            return 0.0

        try:
            # Create a temporary values list for IN clause (limit to avoid SQL issues)
            sample_values = source_values[: min(100, len(source_values))]

            # Format values for SQL IN clause
            if isinstance(sample_values[0], str):
                values_str = ", ".join([f"'{v}'" for v in sample_values])
            else:
                values_str = ", ".join([str(v) for v in sample_values])

            sql = f"""
                SELECT COUNT(DISTINCT "{target_column}") as match_count
                FROM "{self.database}"."{self.schema}"."{target_table}"
                WHERE "{target_column}" IN ({values_str})
            """

            result = self.snow_cli.run_query(sql, output_format="json")
            if not result.rows:
                return 0.0

            match_count = int(result.rows[0]["MATCH_COUNT"])
            overlap_pct = (match_count / len(sample_values)) * 100.0
            return overlap_pct

        except Exception:
            return 0.0

    def _deduplicate_and_score(self, candidates: list[dict]) -> list[Relationship]:
        """
        Deduplicate candidates and calculate combined confidence.

        If multiple strategies identify same relationship, boost confidence.
        """
        # Group by (from_table, from_column, to_table, to_column)
        grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
        for candidate in candidates:
            key = (
                candidate["from_table"],
                candidate["from_column"],
                candidate["to_table"],
                candidate["to_column"],
            )

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)

        # Calculate combined confidence
        relationships = []
        for key, cands in grouped.items():
            # Combine evidence
            all_evidence = []
            for c in cands:
                all_evidence.extend(c["evidence"])

            # Calculate confidence (higher if multiple strategies agree)
            if len(cands) == 1:
                confidence = cands[0]["raw_confidence"]
                strategy = cands[0]["strategy"]
            else:
                # Multiple strategies - boost confidence
                confidence = min(0.95, max(c["raw_confidence"] for c in cands) + 0.15)
                strategy = "combined"

            relationships.append(
                Relationship(
                    from_table=key[0],
                    from_column=key[1],
                    to_table=key[2],
                    to_column=key[3],
                    confidence=confidence,
                    evidence=all_evidence,
                    strategy=strategy,
                )
            )

        return relationships
