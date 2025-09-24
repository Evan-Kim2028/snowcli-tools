from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import sqlglot
from sqlglot import exp

from .loader import CatalogLoader, CatalogObject, ObjectType
from .utils import validate_path


class ExternalSourceType(Enum):
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    LOCAL_FILE = "local_file"
    HTTP = "http"
    SNOWFLAKE_STAGE = "snowflake_stage"
    UNKNOWN = "unknown"


@dataclass
class ExternalSource:
    source_type: ExternalSourceType
    location: str
    stage_name: Optional[str] = None
    file_pattern: Optional[str] = None
    file_format: Optional[str] = None
    encryption: Optional[Dict] = None
    credentials_ref: Optional[str] = None  # Reference to env var or vault key

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type.value,
            "location": self.location,
            "stage_name": self.stage_name,
            "file_pattern": self.file_pattern,
            "file_format": self.file_format,
            "encryption": self.encryption,
            "has_credentials": bool(self.credentials_ref),
            "credentials_ref": self.credentials_ref,  # Don't expose actual credentials
        }

    def get_credentials(self) -> Optional[Dict]:
        """Securely retrieve credentials from environment variables or vault."""
        if not self.credentials_ref:
            return None

        # Check if it's an environment variable reference
        if self.credentials_ref.startswith("env:"):
            env_var = self.credentials_ref[4:]
            creds_json = os.environ.get(env_var)
            if creds_json:
                try:
                    return json.loads(creds_json)
                except json.JSONDecodeError:
                    # If not JSON, treat as single value credential
                    return {"credential": creds_json}
            return None

        # Check if it's a vault reference (placeholder for actual vault integration)
        if self.credentials_ref.startswith("vault:"):
            # This would integrate with HashiCorp Vault, AWS Secrets Manager, etc.
            # For now, return None to indicate vault integration needed
            return None

        # Default: treat as environment variable name
        return {"credential": os.environ.get(self.credentials_ref)}

    def get_bucket_name(self) -> Optional[str]:
        if self.source_type == ExternalSourceType.S3:
            match = re.match(r"s3://([^/]+)", self.location)
            if match:
                return match.group(1)
        elif self.source_type == ExternalSourceType.AZURE_BLOB:
            match = re.match(r"azure://([^.]+)", self.location)
            if match:
                return match.group(1)
        elif self.source_type == ExternalSourceType.GCS:
            match = re.match(r"gcs://([^/]+)", self.location)
            if match:
                return match.group(1)
        return None


@dataclass
class ExternalTableMapping:
    table_name: str
    database: str
    schema: str
    external_source: ExternalSource
    columns: List[Dict] = field(default_factory=list)
    partition_columns: List[str] = field(default_factory=list)
    auto_refresh: bool = False
    last_refresh_time: Optional[str] = None

    def fqn(self) -> str:
        return f"{self.database}.{self.schema}.{self.table_name}"


@dataclass
class StageMapping:
    stage_name: str
    database: str
    schema: str
    external_source: ExternalSource
    copy_operations: List[Dict] = field(default_factory=list)
    pipes: List[str] = field(default_factory=list)

    def fqn(self) -> str:
        return f"{self.database}.{self.schema}.{self.stage_name}"


@dataclass
class ExternalLineage:
    external_sources: Dict[str, ExternalSource] = field(default_factory=dict)
    external_tables: List[ExternalTableMapping] = field(default_factory=list)
    stages: List[StageMapping] = field(default_factory=list)
    source_to_tables: Dict[str, List[str]] = field(default_factory=dict)
    bucket_summary: Dict[str, Dict] = field(default_factory=dict)
    data_flow_paths: List[Dict] = field(default_factory=list)


class ExternalSourceMapper:
    def __init__(self, catalog_path: Path):
        self.catalog_path = Path(catalog_path)
        self.loader = CatalogLoader(self.catalog_path)
        self.external_lineage = ExternalLineage()

    def map_external_sources(
        self,
        include_stages: bool = True,
        include_external_tables: bool = True,
        include_copy_history: bool = False,
    ) -> ExternalLineage:
        catalog = self.loader.load()

        for obj in catalog:
            if obj.object_type == ObjectType.TABLE:
                self._process_table(obj)
            elif obj.object_type == ObjectType.VIEW:
                self._process_view_for_external_refs(obj)

        if include_stages:
            self._extract_stages_from_catalog(catalog)

        if include_external_tables:
            self._extract_external_tables(catalog)

        if include_copy_history:
            self._analyze_copy_operations(catalog)

        self._build_source_mappings()
        self._analyze_buckets()
        self._trace_data_flow_paths()

        return self.external_lineage

    def find_external_dependencies(self, object_name: str) -> List[ExternalSource]:
        dependencies = []

        for table in self.external_lineage.external_tables:
            if table.fqn() == object_name or table.table_name == object_name:
                dependencies.append(table.external_source)

        for stage in self.external_lineage.stages:
            if stage.fqn() == object_name or stage.stage_name == object_name:
                dependencies.append(stage.external_source)

        return dependencies

    def get_tables_from_source(self, source_location: str) -> List[str]:
        return self.external_lineage.source_to_tables.get(source_location, [])

    def analyze_external_access_patterns(self) -> Dict[str, Any]:
        patterns: Dict[str, Any] = {
            "by_source_type": {},
            "by_bucket": {},
            "by_file_format": {},
            "external_table_count": len(self.external_lineage.external_tables),
            "stage_count": len(self.external_lineage.stages),
            "unique_sources": len(self.external_lineage.external_sources),
        }

        for source in self.external_lineage.external_sources.values():
            source_type = source.source_type.value
            patterns["by_source_type"][source_type] = (
                patterns["by_source_type"].get(source_type, 0) + 1
            )

            if bucket := source.get_bucket_name():
                patterns["by_bucket"][bucket] = patterns["by_bucket"].get(bucket, 0) + 1

            if source.file_format:
                patterns["by_file_format"][source.file_format] = (
                    patterns["by_file_format"].get(source.file_format, 0) + 1
                )

        return patterns

    def export_external_mappings(self, output_path: Path, format: str = "json") -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = {
                "external_sources": {
                    key: source.to_dict()
                    for key, source in self.external_lineage.external_sources.items()
                },
                "external_tables": [
                    {
                        "fqn": table.fqn(),
                        "external_source": table.external_source.to_dict(),
                        "columns": table.columns,
                        "partition_columns": table.partition_columns,
                        "auto_refresh": table.auto_refresh,
                    }
                    for table in self.external_lineage.external_tables
                ],
                "stages": [
                    {
                        "fqn": stage.fqn(),
                        "external_source": stage.external_source.to_dict(),
                        "copy_operations": stage.copy_operations,
                        "pipes": stage.pipes,
                    }
                    for stage in self.external_lineage.stages
                ],
                "source_to_tables": self.external_lineage.source_to_tables,
                "bucket_summary": self.external_lineage.bucket_summary,
                "data_flow_paths": self.external_lineage.data_flow_paths,
            }

            # Validate path to prevent traversal attacks
            if not validate_path(
                output_path, must_exist=False, create_if_missing=False
            ):
                raise ValueError(f"Invalid output path: {output_path}")

            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "markdown":
            # Validate path to prevent traversal attacks
            if not validate_path(
                output_path, must_exist=False, create_if_missing=False
            ):
                raise ValueError(f"Invalid output path: {output_path}")

            content = self._generate_markdown_report()
            with open(output_path, "w") as f:
                f.write(content)

        elif format == "dot":
            # Validate path to prevent traversal attacks
            if not validate_path(
                output_path, must_exist=False, create_if_missing=False
            ):
                raise ValueError(f"Invalid output path: {output_path}")

            dot_content = self._generate_dot_graph()
            with open(output_path, "w") as f:
                f.write(dot_content)

        return output_path

    def _process_table(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        sql_lower = text.lower()

        if "external table" in sql_lower:
            self._extract_external_table_info(obj)

        if "copy into" in sql_lower:
            self._extract_copy_info(obj)

    def _process_view_for_external_refs(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        sql_lower = text.lower()

        if "@" in sql_lower:
            self._extract_stage_references(obj)

        if any(pattern in sql_lower for pattern in ["s3://", "azure://", "gcs://"]):
            self._extract_direct_external_refs(obj)

    def _extract_external_table_info(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        try:
            parsed = sqlglot.parse_one(text, read="snowflake")
            if isinstance(parsed, exp.Create):
                location = None
                file_format = None
                pattern = None
                auto_refresh = False

                for prop in parsed.args.get("properties", []):
                    if hasattr(prop, "name"):
                        prop_name = str(prop.name).upper()
                        if prop_name == "LOCATION":
                            location = self._extract_property_value(prop)
                        elif prop_name == "FILE_FORMAT":
                            file_format = self._extract_property_value(prop)
                        elif prop_name == "PATTERN":
                            pattern = self._extract_property_value(prop)
                        elif prop_name == "AUTO_REFRESH":
                            auto_refresh = True

                if location:
                    source = self._parse_external_location(location)
                    source.file_pattern = pattern
                    source.file_format = file_format

                    mapping = ExternalTableMapping(
                        table_name=obj.name,
                        database=obj.database or "",
                        schema=obj.schema or "",
                        external_source=source,
                        auto_refresh=auto_refresh,
                    )

                    self.external_lineage.external_tables.append(mapping)
                    self._register_external_source(source)

        except (sqlglot.errors.ParseError, AttributeError, KeyError) as e:
            # Log but don't crash - external table parsing can fail
            import logging

            logging.debug(f"Failed to parse external table info: {e}")

    def _extract_stages_from_catalog(self, catalog: List[CatalogObject]):
        for obj in catalog:
            text = obj.payload.get("text", "")
            if text and "create stage" in text.lower():
                self._extract_stage_info(obj)

    def _extract_stage_info(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        try:
            parsed = sqlglot.parse_one(text, read="snowflake")
            if isinstance(parsed, exp.Create):
                url = None
                credentials = {}
                encryption = {}

                for prop in parsed.args.get("properties", []):
                    if hasattr(prop, "name"):
                        prop_name = str(prop.name).upper()
                        if prop_name == "URL":
                            url = self._extract_property_value(prop)
                        elif prop_name in ["STORAGE_INTEGRATION", "CREDENTIALS"]:
                            # Store reference to credentials, not the actual values
                            value = self._extract_property_value(prop)
                            # Check if it looks like a credential value
                            if value and not value.startswith(("env:", "vault:")):
                                # Log warning about inline credentials
                                import logging

                                logging.warning(
                                    f"Inline credentials detected in {obj.name}. "
                                    "Consider using environment variables (env:VAR_NAME) "
                                    "or vault references (vault:secret/path)"
                                )
                            credentials[prop_name] = value
                        elif prop_name in ["ENCRYPTION"]:
                            encryption[prop_name] = self._extract_property_value(prop)

                if url:
                    source = self._parse_external_location(url)
                    source.stage_name = obj.name
                    # Store credential reference, not actual credentials
                    if credentials:
                        # If multiple credential properties, combine them
                        if "STORAGE_INTEGRATION" in credentials:
                            source.credentials_ref = f"storage_integration:{credentials['STORAGE_INTEGRATION']}"
                        elif "CREDENTIALS" in credentials:
                            source.credentials_ref = credentials["CREDENTIALS"]
                        else:
                            source.credentials_ref = json.dumps(credentials)
                    source.encryption = encryption if encryption else None

                    mapping = StageMapping(
                        stage_name=obj.name,
                        database=obj.database or "",
                        schema=obj.schema or "",
                        external_source=source,
                    )

                    self.external_lineage.stages.append(mapping)
                    self._register_external_source(source)

        except (sqlglot.errors.ParseError, AttributeError, KeyError) as e:
            # Log but don't crash - external table parsing can fail
            import logging

            logging.debug(f"Failed to parse external table info: {e}")

    def _extract_external_tables(self, catalog: List[CatalogObject]):
        for obj in catalog:
            text = obj.payload.get("text")
            if text and "external table" in text.lower():
                self._extract_external_table_info(obj)

    def _extract_copy_info(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        copy_pattern = re.compile(
            r"copy\s+into\s+(\S+)\s+from\s+([^\s\)]+)", re.IGNORECASE | re.DOTALL
        )

        matches = copy_pattern.findall(text)
        for target_table, source_location in matches:
            source_location = source_location.strip("'\"")

            if source_location.startswith("@"):
                stage_name = source_location[1:].split("/")[0]
                for stage in self.external_lineage.stages:
                    if stage.stage_name == stage_name:
                        stage.copy_operations.append(
                            {
                                "target_table": target_table,
                                "source_location": source_location,
                            }
                        )

    def _extract_stage_references(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        stage_pattern = re.compile(r"@(\w+(?:\.\w+)*)", re.IGNORECASE)
        matches = stage_pattern.findall(text)

        for stage_ref in matches:
            parts = stage_ref.split(".")
            if len(parts) >= 1:
                stage_name = parts[-1]
                for stage in self.external_lineage.stages:
                    if stage.stage_name == stage_name:
                        if obj.fqn() not in stage.pipes:
                            stage.pipes.append(obj.fqn())

    def _extract_direct_external_refs(self, obj: CatalogObject):
        text = obj.payload.get("text")
        if not text:
            return

        url_pattern = re.compile(r"((?:s3|azure|gcs)://[^\s\)\'\"]+)", re.IGNORECASE)

        matches = url_pattern.findall(text)
        for url in matches:
            source = self._parse_external_location(url)
            self._register_external_source(source)

            if source.location not in self.external_lineage.source_to_tables:
                self.external_lineage.source_to_tables[source.location] = []
            self.external_lineage.source_to_tables[source.location].append(obj.fqn())

    def _analyze_copy_operations(self, catalog: List[CatalogObject]):
        for obj in catalog:
            text = obj.payload.get("text")
            if text and "copy into" in text.lower():
                self._extract_copy_info(obj)

    def _parse_external_location(self, location: str) -> ExternalSource:
        location = location.strip("'\"")

        if location.startswith("s3://"):
            source_type = ExternalSourceType.S3
        elif location.startswith("azure://"):
            source_type = ExternalSourceType.AZURE_BLOB
        elif location.startswith("gcs://"):
            source_type = ExternalSourceType.GCS
        elif location.startswith("http://") or location.startswith("https://"):
            source_type = ExternalSourceType.HTTP
        elif location.startswith("@"):
            source_type = ExternalSourceType.SNOWFLAKE_STAGE
        elif location.startswith("/"):
            source_type = ExternalSourceType.LOCAL_FILE
        else:
            source_type = ExternalSourceType.UNKNOWN

        return ExternalSource(source_type=source_type, location=location)

    def _register_external_source(self, source: ExternalSource):
        key = source.location
        if key not in self.external_lineage.external_sources:
            self.external_lineage.external_sources[key] = source

    def _extract_property_value(self, prop) -> Optional[str]:
        if hasattr(prop, "value"):
            if hasattr(prop.value, "value"):
                return str(prop.value.value)
            return str(prop.value)
        return None

    def _build_source_mappings(self):
        for table in self.external_lineage.external_tables:
            source_key = table.external_source.location
            if source_key not in self.external_lineage.source_to_tables:
                self.external_lineage.source_to_tables[source_key] = []
            self.external_lineage.source_to_tables[source_key].append(table.fqn())

        for stage in self.external_lineage.stages:
            source_key = stage.external_source.location
            if source_key not in self.external_lineage.source_to_tables:
                self.external_lineage.source_to_tables[source_key] = []

            for op in stage.copy_operations:
                target = op.get("target_table")
                if (
                    target
                    and target not in self.external_lineage.source_to_tables[source_key]
                ):
                    self.external_lineage.source_to_tables[source_key].append(target)

    def _analyze_buckets(self):
        for source in self.external_lineage.external_sources.values():
            if bucket := source.get_bucket_name():
                if bucket not in self.external_lineage.bucket_summary:
                    self.external_lineage.bucket_summary[bucket] = {
                        "bucket_name": bucket,
                        "source_type": source.source_type.value,
                        "tables": [],
                        "stages": [],
                        "total_references": 0,
                    }

                for table in self.external_lineage.external_tables:
                    if table.external_source.get_bucket_name() == bucket:
                        self.external_lineage.bucket_summary[bucket]["tables"].append(
                            table.fqn()
                        )

                for stage in self.external_lineage.stages:
                    if stage.external_source.get_bucket_name() == bucket:
                        self.external_lineage.bucket_summary[bucket]["stages"].append(
                            stage.fqn()
                        )

                self.external_lineage.bucket_summary[bucket]["total_references"] = len(
                    self.external_lineage.bucket_summary[bucket]["tables"]
                ) + len(self.external_lineage.bucket_summary[bucket]["stages"])

    def _trace_data_flow_paths(self):
        for source_location, tables in self.external_lineage.source_to_tables.items():
            if tables:
                path = {
                    "source": source_location,
                    "source_type": self._get_source_type(source_location),
                    "targets": tables,
                    "flow_type": "direct" if "@" not in source_location else "staged",
                }
                self.external_lineage.data_flow_paths.append(path)

    def _get_source_type(self, location: str) -> str:
        if location in self.external_lineage.external_sources:
            return self.external_lineage.external_sources[location].source_type.value
        return ExternalSourceType.UNKNOWN.value

    def _generate_markdown_report(self) -> str:
        report = []
        report.append("# External Data Source Mappings\n\n")

        report.append("## Summary\n")
        patterns = self.analyze_external_access_patterns()
        report.append(f"- External Tables: {patterns['external_table_count']}\n")
        report.append(f"- Stages: {patterns['stage_count']}\n")
        report.append(f"- Unique Sources: {patterns['unique_sources']}\n\n")

        report.append("## Source Types\n")
        for source_type, count in patterns["by_source_type"].items():
            report.append(f"- {source_type}: {count}\n")
        report.append("\n")

        report.append("## Bucket Summary\n")
        for bucket, info in self.external_lineage.bucket_summary.items():
            report.append(f"### {bucket}\n")
            report.append(f"- Type: {info['source_type']}\n")
            report.append(f"- Total References: {info['total_references']}\n")
            report.append(f"- Tables: {', '.join(info['tables'][:5])}")
            if len(info["tables"]) > 5:
                report.append(f" and {len(info['tables']) - 5} more")
            report.append("\n\n")

        report.append("## Data Flow Paths\n")
        for path in self.external_lineage.data_flow_paths[:20]:
            report.append(f"- **{path['source']}** -> ")
            report.append(f"{', '.join(path['targets'][:3])}")
            if len(path["targets"]) > 3:
                report.append(f" and {len(path['targets']) - 3} more")
            report.append(f" ({path['flow_type']})\n")

        return "".join(report)

    def _generate_dot_graph(self) -> str:
        lines = ["digraph ExternalLineage {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")

        lines.append("  subgraph cluster_external {")
        lines.append('    label="External Sources";')
        lines.append("    style=filled;")
        lines.append('    fillcolor="#FFE5B420";')

        for source in self.external_lineage.external_sources.values():
            label = f"{source.source_type.value}\\n{source.location[:30]}..."
            color = {
                ExternalSourceType.S3: "#FF9500",
                ExternalSourceType.AZURE_BLOB: "#0078D4",
                ExternalSourceType.GCS: "#4285F4",
            }.get(source.source_type, "#95A5A6")
            lines.append(
                f'    "{source.location}" [label="{label}", fillcolor="{color}40"];'
            )

        lines.append("  }")

        lines.append("  subgraph cluster_snowflake {")
        lines.append('    label="Snowflake Objects";')
        lines.append("    style=filled;")
        lines.append('    fillcolor="#00D2FF20";')

        all_tables = set()
        for table in self.external_lineage.external_tables:
            all_tables.add(table.fqn())
        for tables in self.external_lineage.source_to_tables.values():
            all_tables.update(tables)

        for table_fqn in all_tables:
            lines.append(
                f'    "{table_fqn}" [label="{table_fqn}", fillcolor="#00D2FF40"];'
            )

        lines.append("  }")

        for source_loc, table_list in self.external_lineage.source_to_tables.items():
            for table_fqn in table_list:
                lines.append(f'  "{source_loc}" -> "{table_fqn}";')

        lines.append("}")
        return "\n".join(lines)
