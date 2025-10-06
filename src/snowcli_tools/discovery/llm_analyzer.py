"""
LLMAnalyzer - AI-powered business purpose inference.

Uses Snowflake Cortex Complete (mistral-large) to infer:
- Table business purpose
- Column meanings
- PII detection
- Category classification (dimension, fact, event log, reference)
"""

import json
import re
from datetime import datetime
from typing import Any

from snowcli_tools.discovery.models import (
    ColumnMeaning,
    LLMAnalysis,
    TableCategory,
    TableProfile,
)
from snowcli_tools.snow_cli import SnowCLI


class LLMAnalyzer:
    """Analyze table purpose using Cortex Complete AI."""

    DEFAULT_MODEL = "mistral-large"
    DEFAULT_TEMPERATURE = 0.1  # Low for consistency
    DEFAULT_MAX_TOKENS = 2048

    def __init__(
        self,
        snow_cli: SnowCLI,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        """
        Initialize LLMAnalyzer.

        Args:
            snow_cli: SnowCLI instance for Cortex Complete calls
            model: Cortex model to use (default: mistral-large)
            temperature: Sampling temperature (default: 0.1 for consistency)
            max_tokens: Maximum response tokens (default: 2048)
        """
        self.snow_cli = snow_cli
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def analyze_table(self, profile: TableProfile) -> LLMAnalysis:
        """
        Analyze table using AI inference.

        Args:
            profile: TableProfile from TableProfiler

        Returns:
            LLMAnalysis with inferred business purpose, column meanings, PII detection

        Raises:
            ValueError: If LLM returns malformed response
            RuntimeError: If Cortex Complete call fails
        """
        start_time = datetime.now()

        # Build prompt
        prompt = self._build_analysis_prompt(profile)

        # Call Cortex Complete
        try:
            response = self._call_cortex_complete(prompt)

            # Parse JSON response
            analysis_data = self._parse_llm_response(response)

            # Build ColumnMeaning objects
            column_meanings = {}
            for col_name, col_data in analysis_data.get("columns", {}).items():
                column_meanings[col_name] = ColumnMeaning(
                    purpose=col_data.get("purpose", "Unknown"),
                    category=col_data.get("category", "unknown"),
                    is_pii=col_data.get("is_pii", False),
                    confidence=col_data.get("confidence", 0) / 100.0,
                )

            # Extract PII columns
            pii_columns = [
                col_name
                for col_name, meaning in column_meanings.items()
                if meaning.is_pii
            ]

            end_time = datetime.now()
            analysis_time = (end_time - start_time).total_seconds()

            # Calculate confidence
            confidence = analysis_data.get("confidence", 0) / 100.0

            return LLMAnalysis(
                table_purpose=analysis_data.get("table_purpose", "Unknown"),
                category=TableCategory(analysis_data.get("category", "unknown")),
                confidence=confidence,
                column_meanings=column_meanings,
                pii_columns=pii_columns,
                suggested_description=analysis_data.get("suggested_description", ""),
                analysis_time_seconds=analysis_time,
                token_usage=analysis_data.get("token_usage"),
            )

        except (json.JSONDecodeError, ValueError) as e:
            # LLM returned malformed JSON - fall back to low-confidence analysis
            return self._create_fallback_analysis(profile, str(e))
        except Exception as e:
            # Other errors - re-raise with context
            raise RuntimeError(f"LLM analysis failed: {str(e)}") from e

    def _sanitize_sample_data(
        self, sample_rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Sanitize sample data to prevent prompt injection.

        Truncates long strings and removes potentially dangerous content.
        """
        sanitized = []
        for row in sample_rows:
            sanitized_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Truncate long strings
                    if len(value) > 100:
                        value = value[:100] + "..."
                    # Remove control characters
                    value = "".join(
                        char for char in value if ord(char) >= 32 or char == "\n"
                    )
                sanitized_row[key] = value
            sanitized.append(sanitized_row)
        return sanitized

    def _build_analysis_prompt(self, profile: TableProfile) -> str:
        """
        Build structured prompt for Cortex Complete.

        Prompt engineering for consistent, parseable responses.
        """
        # Format columns for prompt (limit to first 20 to avoid token bloat)
        columns_text = "\n".join(
            [
                f"  - {col.name} ({col.data_type}): "
                f"null={col.null_percentage:.1f}%, "
                f"cardinality={col.cardinality:,}, "
                f"pattern={col.pattern or 'none'}"
                for col in profile.columns[:20]
            ]
        )

        if len(profile.columns) > 20:
            columns_text += f"\n  ... and {len(profile.columns) - 20} more columns"

        # Format sample rows (first 3 only) with sanitization
        sample_rows = profile.sample_rows[:3]
        sanitized_rows = self._sanitize_sample_data(sample_rows)
        sample_text = json.dumps(sanitized_rows, indent=2, default=str)

        prompt = f"""Analyze this Snowflake table and infer its business purpose.

TABLE: {profile.database}.{profile.schema}.{profile.table_name}
ROWS: {profile.row_count:,}

COLUMNS ({len(profile.columns)}):
{columns_text}

SAMPLE ROWS (first 3):
{sample_text}

Based on the table structure and sample data, provide a detailed analysis as JSON.

Respond with ONLY valid JSON (no markdown, no code blocks), using this exact structure:
{{
  "table_purpose": "Clear business description of what this table represents",
  "category": "dimension_table | fact_table | event_log | reference_data | unknown",
  "confidence": 85,
  "suggested_description": "2-3 sentence documentation for data catalog",
  "columns": {{
    "column_name": {{
      "purpose": "Business meaning of this column",
      "category": "id | name | contact | timestamp | amount | status | other",
      "is_pii": true,
      "confidence": 90
    }}
  }},
  "reasoning": "Brief explanation of your analysis"
}}

Key guidelines:
1. Set is_pii=true for ANY column that could identify an individual (email, phone, name, SSN, etc.)
2. Confidence should be 0-100 based on how certain you are
3. Use actual column names from the table in the "columns" object
4. Be specific and concise in purposes and descriptions

JSON response:"""

        return prompt

    def _call_cortex_complete(self, prompt: str) -> str:
        """
        Call Snowflake Cortex Complete.

        Uses Cortex Complete via SQL:
        SELECT SNOWFLAKE.CORTEX.COMPLETE(model, prompt, options)
        """
        # Build Cortex Complete SQL
        options = {"temperature": self.temperature, "max_tokens": self.max_tokens}
        options_json = json.dumps(options)

        # Escape single quotes in prompt
        prompt_escaped = prompt.replace("'", "''")

        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{self.model}',
                '{prompt_escaped}',
                {options_json}
            ) as response
        """

        result = self.snow_cli.run_query(sql, output_format="json")

        if not result.rows or not result.rows[0].get("RESPONSE"):
            raise ValueError("Cortex Complete returned empty response")

        response_text = result.rows[0]["RESPONSE"]
        if not response_text or not response_text.strip():
            raise ValueError("Cortex Complete returned empty response text")

        return response_text

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM JSON response.

        Handles:
        - Markdown code blocks (```json ... ```)
        - Malformed JSON
        - Missing fields
        """
        # Strip markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            # Extract JSON from code block (use non-greedy match)
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                response = match.group(1)
            else:
                # Try without code block markers
                match = re.search(r"\{.*?\}", response, re.DOTALL)
                if match:
                    response = match.group(0)

        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON object with non-greedy regex
            match = re.search(r"\{.*?\}", response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except json.JSONDecodeError:
                    # Last resort: try greedy match
                    match = re.search(r"\{.*\}", response, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                    else:
                        raise ValueError(
                            f"Could not parse JSON from response: {response[:200]}"
                        )
            else:
                raise ValueError(
                    f"Could not parse JSON from response: {response[:200]}"
                )

        # Validate required fields
        required = ["table_purpose", "category", "confidence"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return data

    def _create_fallback_analysis(
        self, profile: TableProfile, error: str
    ) -> LLMAnalysis:
        """
        Create low-confidence fallback analysis when LLM fails.

        Returns basic analysis based on table/column names only.
        """
        # Simple heuristic: look for common patterns in table name
        table_lower = profile.table_name.lower()

        if any(word in table_lower for word in ["customer", "user", "person"]):
            category = TableCategory.DIMENSION
            purpose = f"Likely a {profile.table_name} dimension table"
        elif any(word in table_lower for word in ["transaction", "order", "sale"]):
            category = TableCategory.FACT
            purpose = f"Likely a {profile.table_name} fact table"
        elif any(word in table_lower for word in ["event", "log", "audit"]):
            category = TableCategory.EVENT_LOG
            purpose = f"Likely a {profile.table_name} event log"
        else:
            category = TableCategory.UNKNOWN
            purpose = f"Table: {profile.table_name}"

        # Detect PII columns by name
        pii_keywords = ["email", "phone", "ssn", "name", "address"]
        pii_columns = [
            col.name
            for col in profile.columns
            if any(keyword in col.name.lower() for keyword in pii_keywords)
        ]

        return LLMAnalysis(
            table_purpose=purpose,
            category=category,
            confidence=0.3,  # Low confidence
            column_meanings={},
            pii_columns=pii_columns,
            suggested_description=f"Analysis failed: {error}. Using fallback heuristics.",
            analysis_time_seconds=0.0,
            token_usage=None,
        )
