from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .column_parser import (
    ColumnLineageGraph,
    ColumnTransformation,
    TransformationType,
)


class TransformationCategory(Enum):
    DATA_TYPE = "data_type"
    CLEANSING = "cleansing"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"
    JOINING = "joining"
    PIVOTING = "pivoting"
    WINDOW = "window"
    CALCULATION = "calculation"
    EXTRACTION = "extraction"
    FORMATTING = "formatting"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class TransformationPattern:
    pattern_id: str
    name: str
    category: TransformationCategory
    sql_pattern: str
    description: str
    example: str
    frequency: int = 0
    avg_performance_impact: Optional[float] = None


@dataclass
class TransformationMetadata:
    transformation_id: str
    timestamp: datetime
    source_object: str
    target_object: str
    transformation_type: TransformationType
    category: TransformationCategory
    sql_text: str
    columns_affected: List[str]
    business_logic: Optional[str] = None
    performance_impact: Optional[float] = None
    data_quality_rules: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "transformation_id": self.transformation_id,
            "timestamp": self.timestamp.isoformat(),
            "source_object": self.source_object,
            "target_object": self.target_object,
            "transformation_type": self.transformation_type.value,
            "category": self.category.value,
            "sql_text": self.sql_text,
            "columns_affected": self.columns_affected,
            "business_logic": self.business_logic,
            "performance_impact": self.performance_impact,
            "data_quality_rules": self.data_quality_rules,
            "tags": self.tags,
        }


@dataclass
class TransformationChain:
    chain_id: str
    transformations: List[TransformationMetadata]
    start_point: str
    end_point: str
    total_transformations: int
    categories_involved: Set[TransformationCategory]
    complexity_score: float

    def to_dict(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "transformations": [t.to_dict() for t in self.transformations],
            "start_point": self.start_point,
            "end_point": self.end_point,
            "total_transformations": self.total_transformations,
            "categories": [cat.value for cat in self.categories_involved],
            "complexity_score": self.complexity_score,
        }


class TransformationTracker:
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./transformation_history")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.patterns: Dict[str, TransformationPattern] = self._load_patterns()
        self.transformation_history: List[TransformationMetadata] = []

    def track_transformation(
        self,
        transformation: ColumnTransformation,
        source_object: str,
        target_object: str,
        business_logic: Optional[str] = None,
    ) -> TransformationMetadata:
        transformation_id = self._generate_transformation_id(
            source_object, target_object, transformation.transformation_sql
        )

        category = self._categorize_transformation(transformation)

        columns_affected = [col.column for col in transformation.source_columns]
        if transformation.target_column:
            columns_affected.append(transformation.target_column.column)

        metadata = TransformationMetadata(
            transformation_id=transformation_id,
            timestamp=datetime.now(),
            source_object=source_object,
            target_object=target_object,
            transformation_type=transformation.transformation_type,
            category=category,
            sql_text=transformation.transformation_sql,
            columns_affected=columns_affected,
            business_logic=business_logic,
            performance_impact=self._estimate_performance_impact(transformation),
            data_quality_rules=self._extract_data_quality_rules(transformation),
            tags=self._generate_tags(transformation),
        )

        self.transformation_history.append(metadata)
        self._save_transformation(metadata)

        return metadata

    def track_lineage_transformations(
        self, lineage_graph: ColumnLineageGraph, source_object: str, target_object: str
    ) -> List[TransformationMetadata]:
        tracked_transformations = []

        for transformation in lineage_graph.transformations:
            metadata = self.track_transformation(
                transformation, source_object, target_object
            )
            tracked_transformations.append(metadata)

        return tracked_transformations

    def find_transformation_chains(
        self, start_column: str, end_column: Optional[str] = None, max_depth: int = 10
    ) -> List[TransformationChain]:
        chains = []
        visited = set()

        def trace_chain(current: str, chain: List[TransformationMetadata], depth: int):
            if depth > max_depth:
                return

            if current in visited:
                return

            visited.add(current)

            if end_column and current == end_column:
                chain_id = self._generate_chain_id(chain)
                categories = {t.category for t in chain}
                complexity = self._calculate_complexity(chain)

                chains.append(
                    TransformationChain(
                        chain_id=chain_id,
                        transformations=chain.copy(),
                        start_point=start_column,
                        end_point=current,
                        total_transformations=len(chain),
                        categories_involved=categories,
                        complexity_score=complexity,
                    )
                )
                return

            for trans in self.transformation_history:
                if any(current in col for col in trans.columns_affected):
                    new_chain = chain + [trans]
                    trace_chain(trans.target_object, new_chain, depth + 1)

        trace_chain(start_column, [], 0)
        return chains

    def analyze_patterns(self, min_frequency: int = 2) -> List[TransformationPattern]:
        pattern_counts: Dict[str, int] = {}
        pattern_examples: Dict[str, str] = {}

        for trans in self.transformation_history:
            pattern_key = self._extract_pattern_key(trans)
            pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1
            if pattern_key not in pattern_examples:
                pattern_examples[pattern_key] = trans.sql_text

        patterns = []
        for pattern_key, count in pattern_counts.items():
            if count >= min_frequency:
                pattern = TransformationPattern(
                    pattern_id=hashlib.md5(pattern_key.encode()).hexdigest()[:8],
                    name=self._generate_pattern_name(pattern_key),
                    category=self._pattern_to_category(pattern_key),
                    sql_pattern=pattern_key,
                    description=f"Pattern occurring {count} times",
                    example=pattern_examples[pattern_key],
                    frequency=count,
                )
                patterns.append(pattern)

        return sorted(patterns, key=lambda x: x.frequency, reverse=True)

    def get_transformation_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "total_transformations": len(self.transformation_history),
            "transformation_types": {},
            "categories": {},
            "top_patterns": [],
            "average_complexity": 0.0,
            "most_transformed_columns": {},
            "transformation_chains": [],
        }

        for trans in self.transformation_history:
            type_key = trans.transformation_type.value
            summary["transformation_types"][type_key] = (
                summary["transformation_types"].get(type_key, 0) + 1
            )

            cat_key = trans.category.value
            summary["categories"][cat_key] = summary["categories"].get(cat_key, 0) + 1

            for col in trans.columns_affected:
                summary["most_transformed_columns"][col] = (
                    summary["most_transformed_columns"].get(col, 0) + 1
                )

        patterns = self.analyze_patterns()
        summary["top_patterns"] = [
            {"name": p.name, "frequency": p.frequency, "category": p.category.value}
            for p in patterns[:10]
        ]

        return summary

    def export_transformations(self, output_path: Path, format: str = "json") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = {
                "transformations": [t.to_dict() for t in self.transformation_history],
                "summary": self.get_transformation_summary(),
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "jsonl":
            with open(output_path, "w") as f:
                for trans in self.transformation_history:
                    f.write(json.dumps(trans.to_dict()) + "\n")

        elif format == "markdown":
            content = self._generate_markdown_report()
            with open(output_path, "w") as f:
                f.write(content)

        return output_path

    def _categorize_transformation(
        self, transformation: ColumnTransformation
    ) -> TransformationCategory:
        trans_type = transformation.transformation_type
        func_name = transformation.function_name

        if trans_type == TransformationType.AGGREGATE:
            return TransformationCategory.AGGREGATION
        elif trans_type == TransformationType.WINDOW:
            return TransformationCategory.WINDOW
        elif trans_type == TransformationType.JOIN:
            return TransformationCategory.JOINING
        elif trans_type == TransformationType.CASE:
            return TransformationCategory.VALIDATION

        if func_name:
            func_lower = func_name.lower()
            if any(f in func_lower for f in ["cast", "convert", "to_"]):
                return TransformationCategory.DATA_TYPE
            elif any(f in func_lower for f in ["trim", "replace", "clean", "remove"]):
                return TransformationCategory.CLEANSING
            elif any(f in func_lower for f in ["concat", "||", "append", "merge"]):
                return TransformationCategory.ENRICHMENT
            elif any(f in func_lower for f in ["substr", "split", "extract", "parse"]):
                return TransformationCategory.EXTRACTION
            elif any(f in func_lower for f in ["format", "to_char", "date_format"]):
                return TransformationCategory.FORMATTING
            elif any(
                f in func_lower
                for f in ["add", "subtract", "multiply", "divide", "sum"]
            ):
                return TransformationCategory.CALCULATION

        return TransformationCategory.UNKNOWN

    def _generate_transformation_id(self, source: str, target: str, sql: str) -> str:
        content = f"{source}|{target}|{sql}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_chain_id(self, chain: List[TransformationMetadata]) -> str:
        if not chain:
            return ""
        content = "|".join([t.transformation_id for t in chain])
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _estimate_performance_impact(
        self, transformation: ColumnTransformation
    ) -> float:
        impact = 0.0

        if transformation.transformation_type == TransformationType.AGGREGATE:
            impact += 0.3
        elif transformation.transformation_type == TransformationType.WINDOW:
            impact += 0.4
        elif transformation.transformation_type == TransformationType.JOIN:
            impact += 0.5
        elif transformation.transformation_type == TransformationType.SUBQUERY:
            impact += 0.6

        num_source_cols = len(transformation.source_columns)
        impact += num_source_cols * 0.05

        if transformation.function_name:
            if "regex" in transformation.function_name.lower():
                impact += 0.3
            elif "parse" in transformation.function_name.lower():
                impact += 0.2

        return min(impact, 1.0)

    def _extract_data_quality_rules(
        self, transformation: ColumnTransformation
    ) -> List[str]:
        rules = []

        sql_lower = transformation.transformation_sql.lower()

        if "not null" in sql_lower:
            rules.append("NOT_NULL")
        if "unique" in sql_lower:
            rules.append("UNIQUE")
        if "check" in sql_lower:
            rules.append("CHECK_CONSTRAINT")
        if transformation.transformation_type == TransformationType.CASE:
            rules.append("CONDITIONAL_VALIDATION")
        if "between" in sql_lower:
            rules.append("RANGE_CHECK")
        if "in (" in sql_lower:
            rules.append("ALLOWED_VALUES")

        return rules

    def _generate_tags(self, transformation: ColumnTransformation) -> List[str]:
        tags = []

        if transformation.confidence < 0.8:
            tags.append("low_confidence")
        if transformation.transformation_type == TransformationType.UNKNOWN:
            tags.append("needs_review")
        if len(transformation.source_columns) > 5:
            tags.append("complex")
        if transformation.function_name:
            tags.append(f"uses_{transformation.function_name.lower()}")

        return tags

    def _extract_pattern_key(self, trans: TransformationMetadata) -> str:
        return f"{trans.transformation_type.value}:{trans.category.value}"

    def _generate_pattern_name(self, pattern_key: str) -> str:
        parts = pattern_key.split(":")
        if len(parts) == 2:
            return f"{parts[1].replace('_', ' ').title()} via {parts[0].replace('_', ' ').title()}"
        return pattern_key

    def _pattern_to_category(self, pattern_key: str) -> TransformationCategory:
        parts = pattern_key.split(":")
        if len(parts) == 2:
            try:
                return TransformationCategory(parts[1])
            except ValueError:
                pass
        return TransformationCategory.UNKNOWN

    def _calculate_complexity(self, chain: List[TransformationMetadata]) -> float:
        if not chain:
            return 0.0

        complexity = len(chain) * 0.1
        unique_categories = len({t.category for t in chain})
        complexity += unique_categories * 0.15

        for trans in chain:
            if trans.performance_impact:
                complexity += trans.performance_impact * 0.2

        return min(complexity, 1.0)

    def _save_transformation(self, metadata: TransformationMetadata):
        file_path = self.storage_path / f"{metadata.transformation_id}.json"
        with open(file_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)

    def _load_patterns(self) -> Dict[str, TransformationPattern]:
        return {}

    def _generate_markdown_report(self) -> str:
        summary = self.get_transformation_summary()

        report = []
        report.append("# Transformation Analysis Report\n")
        report.append(f"Generated: {datetime.now().isoformat()}\n")

        report.append("## Summary\n")
        report.append(f"- Total Transformations: {summary['total_transformations']}\n")
        report.append(
            f"- Unique Transformation Types: {len(summary['transformation_types'])}\n"
        )
        report.append(f"- Categories Covered: {len(summary['categories'])}\n")

        report.append("\n## Transformation Types\n")
        for trans_type, count in sorted(summary["transformation_types"].items()):
            report.append(f"- {trans_type}: {count}\n")

        report.append("\n## Top Patterns\n")
        for pattern in summary["top_patterns"]:
            report.append(
                f"- **{pattern['name']}** (Frequency: {pattern['frequency']})\n"
            )

        report.append("\n## Most Transformed Columns\n")
        for col, count in sorted(
            summary["most_transformed_columns"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]:
            report.append(f"- {col}: {count} transformations\n")

        return "".join(report)
