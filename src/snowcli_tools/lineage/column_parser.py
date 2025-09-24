from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from sqlglot import exp
from sqlglot.expressions import Expression

from .identifiers import normalize
from .utils import cached_sql_parse, validate_object_name


class TransformationType(Enum):
    DIRECT = "direct"
    ALIAS = "alias"
    FUNCTION = "function"
    AGGREGATE = "aggregate"
    CASE = "case"
    WINDOW = "window"
    JOIN = "join"
    SUBQUERY = "subquery"
    LITERAL = "literal"
    UNKNOWN = "unknown"


@dataclass
class QualifiedColumn:
    table: str
    column: str
    database: Optional[str] = None
    schema: Optional[str] = None
    alias: Optional[str] = None

    def fqn(self) -> str:
        parts = []
        if self.database:
            parts.append(normalize(self.database))
        if self.schema:
            parts.append(normalize(self.schema))
        parts.append(normalize(self.table))
        parts.append(normalize(self.column))
        return ".".join(parts)

    def __hash__(self):
        return hash(self.fqn())

    def __eq__(self, other):
        if isinstance(other, QualifiedColumn):
            return self.fqn() == other.fqn()
        return False


@dataclass
class ColumnTransformation:
    source_columns: List[QualifiedColumn]
    target_column: QualifiedColumn
    transformation_type: TransformationType
    transformation_sql: str
    confidence: float = 1.0
    function_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_columns": [col.fqn() for col in self.source_columns],
            "target_column": self.target_column.fqn(),
            "type": self.transformation_type.value,
            "sql": self.transformation_sql,
            "confidence": self.confidence,
            "function": self.function_name,
        }


@dataclass
class ColumnLineageGraph:
    transformations: List[ColumnTransformation] = field(default_factory=list)
    column_dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    def add_transformation(self, transformation: ColumnTransformation):
        self.transformations.append(transformation)
        target_fqn = transformation.target_column.fqn()
        if target_fqn not in self.column_dependencies:
            self.column_dependencies[target_fqn] = set()
        for source_col in transformation.source_columns:
            self.column_dependencies[target_fqn].add(source_col.fqn())

    def get_upstream_columns(self, column_fqn: str) -> Set[str]:
        return self.column_dependencies.get(column_fqn, set())

    def get_downstream_columns(self, column_fqn: str) -> Set[str]:
        downstream = set()
        for target, sources in self.column_dependencies.items():
            if column_fqn in sources:
                downstream.add(target)
        return downstream


class ColumnLineageExtractor:
    def __init__(
        self,
        default_database: Optional[str] = None,
        default_schema: Optional[str] = None,
    ):
        self.default_database = default_database
        self.default_schema = default_schema
        self._table_aliases: Dict[str, str] = {}
        self._cte_columns: Dict[str, List[str]] = {}

    def extract_column_lineage(
        self, sql: str, target_table: Optional[str] = None
    ) -> ColumnLineageGraph:
        graph = ColumnLineageGraph()

        # Validate target table name if provided
        if target_table and not validate_object_name(target_table):
            graph.issues.append(f"Invalid target table name: {target_table}")
            return graph

        # Use cached safe parsing
        parsed = cached_sql_parse(sql, "snowflake")
        if not parsed:
            graph.issues.append("Failed to parse SQL")
            return graph

        # Handle multi-statement SQL
        if isinstance(parsed, list):
            graph.issues.append(
                "Multi-statement SQL detected, processing first statement only"
            )
            parsed = parsed[0] if parsed else None
            if not parsed:
                return graph

        if isinstance(parsed, exp.Create):
            self._process_create_statement(parsed, graph, target_table)
        elif isinstance(parsed, exp.Insert):
            self._process_insert_statement(parsed, graph)
        elif isinstance(parsed, exp.Select):
            self._process_select_statement(parsed, graph, target_table)
        elif isinstance(parsed, exp.Merge):
            self._process_merge_statement(parsed, graph)

        return graph

    def _process_create_statement(
        self,
        stmt: exp.Create,
        graph: ColumnLineageGraph,
        target_table: Optional[str] = None,
    ):
        table_name = self._extract_table_name(stmt.this)
        if not table_name and target_table:
            table_name = target_table

        if expr := stmt.args.get("expression"):
            if isinstance(expr, exp.Select):
                self._process_select_columns(expr, graph, table_name)

    def _process_insert_statement(self, stmt: exp.Insert, graph: ColumnLineageGraph):
        table_name = self._extract_table_name(stmt.this)

        if expr := stmt.expression:
            if isinstance(expr, exp.Select):
                target_columns = []
                if columns := stmt.columns:
                    target_columns = [col.name for col in columns]
                self._process_select_columns(expr, graph, table_name, target_columns)

    def _process_select_statement(
        self,
        stmt: exp.Select,
        graph: ColumnLineageGraph,
        target_table: Optional[str] = None,
    ):
        if not target_table:
            target_table = "SELECT_RESULT"

        self._extract_ctes(stmt)
        self._extract_table_aliases(stmt)
        self._process_select_columns(stmt, graph, target_table)

    def _process_merge_statement(self, stmt: exp.Merge, graph: ColumnLineageGraph):
        target_table = self._extract_table_name(stmt.this)

        for when_clause in stmt.args.get("whens", []):
            if updates := when_clause.args.get("updates"):
                for update in updates:
                    if isinstance(update, exp.Update):
                        self._process_update_columns(update, graph, target_table)

    def _process_select_columns(
        self,
        select_stmt: exp.Select,
        graph: ColumnLineageGraph,
        target_table: str,
        target_columns: Optional[List[str]] = None,
    ):
        for i, expr in enumerate(select_stmt.expressions):
            if isinstance(expr, exp.Star):
                self._process_star_column(expr, graph, target_table)
            else:
                target_col_name = (
                    target_columns[i]
                    if target_columns and i < len(target_columns)
                    else None
                )
                self._process_single_column(expr, graph, target_table, target_col_name)

    def _process_single_column(
        self,
        expr: Expression,
        graph: ColumnLineageGraph,
        target_table: str,
        target_column_name: Optional[str] = None,
    ):
        if not target_column_name:
            if alias := expr.alias:
                target_column_name = alias
            elif isinstance(expr, exp.Column):
                target_column_name = expr.name
            else:
                target_column_name = f"column_{len(graph.transformations) + 1}"

        target_column = QualifiedColumn(
            table=target_table,
            column=target_column_name,
            database=self.default_database,
            schema=self.default_schema,
        )

        source_columns = []
        transformation_type = TransformationType.UNKNOWN
        function_name = None
        sql_text = expr.sql()

        if isinstance(expr, exp.Column):
            source_col = self._resolve_column(expr)
            if source_col:
                source_columns = [source_col]
                transformation_type = TransformationType.DIRECT

        elif isinstance(expr, exp.Alias):
            inner_expr = expr.this
            if isinstance(inner_expr, exp.Column):
                source_col = self._resolve_column(inner_expr)
                if source_col:
                    source_columns = [source_col]
                    transformation_type = TransformationType.ALIAS
            else:
                source_columns = self._extract_columns_from_expression(inner_expr)
                transformation_type = self._determine_transformation_type(inner_expr)
                if isinstance(inner_expr, exp.Func):
                    function_name = inner_expr.sql_name()

        elif isinstance(expr, exp.Func):
            source_columns = self._extract_columns_from_expression(expr)
            if hasattr(expr, "is_aggregate") and expr.is_aggregate:
                transformation_type = TransformationType.AGGREGATE
            elif any(
                isinstance(arg, exp.Window)
                for arg in expr.args.values()
                if hasattr(expr.args, "values")
            ):
                transformation_type = TransformationType.WINDOW
            else:
                # Check function name for aggregate detection
                func_class = expr.__class__.__name__.upper()
                if func_class in [
                    "SUM",
                    "AVG",
                    "COUNT",
                    "MAX",
                    "MIN",
                    "STDDEV",
                    "VARIANCE",
                ]:
                    transformation_type = TransformationType.AGGREGATE
                else:
                    transformation_type = TransformationType.FUNCTION
            function_name = (
                expr.sql_name()
                if hasattr(expr, "sql_name")
                else expr.__class__.__name__
            )

        elif isinstance(expr, exp.Case):
            source_columns = self._extract_columns_from_expression(expr)
            transformation_type = TransformationType.CASE

        elif isinstance(expr, exp.Subquery):
            source_columns = self._extract_columns_from_subquery(expr)
            transformation_type = TransformationType.SUBQUERY

        elif isinstance(expr, exp.Literal):
            transformation_type = TransformationType.LITERAL

        else:
            source_columns = self._extract_columns_from_expression(expr)
            transformation_type = self._determine_transformation_type(expr)

        confidence = 1.0 if source_columns else 0.5

        transformation = ColumnTransformation(
            source_columns=source_columns,
            target_column=target_column,
            transformation_type=transformation_type,
            transformation_sql=sql_text[:500],
            confidence=confidence,
            function_name=function_name,
        )

        graph.add_transformation(transformation)

    def _process_star_column(
        self, star: exp.Star, graph: ColumnLineageGraph, target_table: str
    ):
        if table := star.args.get("table"):
            source_table = self._resolve_table_name(table)
            graph.issues.append(
                f"Star expansion from {source_table} not fully resolved"
            )
        else:
            graph.issues.append("Star expansion across all tables not fully resolved")

    def _process_update_columns(
        self, update: exp.Update, graph: ColumnLineageGraph, target_table: str
    ):
        for set_expr in update.args.get("set", []):
            if isinstance(set_expr, exp.EQ):
                left = set_expr.left
                right = set_expr.right

                if isinstance(left, exp.Column):
                    target_column = QualifiedColumn(
                        table=target_table,
                        column=left.name,
                        database=self.default_database,
                        schema=self.default_schema,
                    )

                    source_columns = self._extract_columns_from_expression(right)
                    transformation_type = self._determine_transformation_type(right)

                    transformation = ColumnTransformation(
                        source_columns=source_columns,
                        target_column=target_column,
                        transformation_type=transformation_type,
                        transformation_sql=right.sql()[:500],
                        confidence=1.0 if source_columns else 0.5,
                    )

                    graph.add_transformation(transformation)

    def _resolve_column(self, col: exp.Column) -> Optional[QualifiedColumn]:
        table_name = None
        if table := col.table:
            table_name = self._resolve_table_name(table)

        if not table_name:
            return None

        return QualifiedColumn(
            table=table_name,
            column=col.name,
            database=self.default_database,
            schema=self.default_schema,
        )

    def _resolve_table_name(self, table_ref: str) -> str:
        if table_ref in self._table_aliases:
            return self._table_aliases[table_ref]
        return table_ref

    def _extract_table_name(self, table_expr: Expression) -> Optional[str]:
        if isinstance(table_expr, exp.Table):
            parts = []
            if db := table_expr.db:
                parts.append(db)
            if catalog := table_expr.catalog:
                parts.append(catalog)
            parts.append(table_expr.name)
            return ".".join(parts)
        return None

    def _extract_table_aliases(self, stmt: Expression):
        for table in stmt.find_all(exp.Table):
            if alias := table.alias:
                full_name = self._extract_table_name(table)
                if full_name:
                    self._table_aliases[alias] = full_name

    def _extract_ctes(self, stmt: Expression):
        for cte in stmt.find_all(exp.CTE):
            if alias := cte.alias:
                cte_name = alias.name if hasattr(alias, "name") else str(alias)
                if query := cte.this:
                    if isinstance(query, exp.Select):
                        columns = []
                        for expr in query.expressions:
                            if alias := expr.alias:
                                columns.append(alias)
                            elif isinstance(expr, exp.Column):
                                columns.append(expr.name)
                        self._cte_columns[cte_name] = columns

    def _extract_columns_from_expression(
        self, expr: Expression
    ) -> List[QualifiedColumn]:
        columns = []
        for col in expr.find_all(exp.Column):
            if resolved := self._resolve_column(col):
                columns.append(resolved)
        return columns

    def _extract_columns_from_subquery(
        self, subquery: exp.Subquery
    ) -> List[QualifiedColumn]:
        columns = []
        if query := subquery.this:
            if isinstance(query, exp.Select):
                for col in query.find_all(exp.Column):
                    if resolved := self._resolve_column(col):
                        columns.append(resolved)
        return columns

    def _determine_transformation_type(self, expr: Expression) -> TransformationType:
        if isinstance(expr, exp.Func):
            if hasattr(expr, "is_aggregate") and expr.is_aggregate:
                return TransformationType.AGGREGATE
            # Check for common aggregate functions
            func_name = expr.__class__.__name__.upper()
            if func_name in ["SUM", "AVG", "COUNT", "MAX", "MIN", "STDDEV", "VARIANCE"]:
                return TransformationType.AGGREGATE
            return TransformationType.FUNCTION
        elif isinstance(expr, exp.Case):
            return TransformationType.CASE
        elif isinstance(expr, exp.Subquery):
            return TransformationType.SUBQUERY
        elif isinstance(expr, exp.Column):
            return TransformationType.DIRECT
        elif isinstance(expr, exp.Literal):
            return TransformationType.LITERAL
        return TransformationType.UNKNOWN
