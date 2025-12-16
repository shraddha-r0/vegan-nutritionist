from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAIError

from config import Config


class SQLGenerationError(Exception):
    """Raised when the LLM fails to produce a valid SQL statement."""


class SQLExecutionError(Exception):
    """Raised when the generated SQL cannot be executed safely."""


@dataclass
class SQLPlan:
    sql: str
    reasoning: str
    confidence: float


@dataclass
class AssistantResponse:
    message: str
    sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class LLMSQLAssistant:
    """Bridges user requests to SQLite queries using an LLM for text-to-SQL."""

    MAX_ROWS = 200

    def __init__(self):
        Config.validate()
        self.client = Config.get_openai_client()
        self.schema = Config.load_database_schema()
        self.schema_yaml = Config.load_database_schema_text()
        self.profile = Config.load_nutrition_profile()
        self.profile_yaml = Config.load_nutrition_profile_text()
        self.profile_system_prompt = self.profile.get(
            "system_prompt",
            "You are a careful vegan nutrition analyst.",
        )
        self.schema_context = self._build_schema_context()

    def answer_question(self, question: str) -> AssistantResponse:
        """High-level helper that produces SQL, runs it, and summarizes the result."""
        try:
            plan = self._generate_sql_plan(question)
            rows = self._execute_sql(plan.sql)
            summary = self._summarize_answer(question, plan, rows)
            return AssistantResponse(
                message=summary,
                sql=plan.sql,
                rows=rows,
                reasoning=plan.reasoning,
                confidence=plan.confidence,
            )
        except (SQLGenerationError, SQLExecutionError) as exc:
            return AssistantResponse(
                message="I ran into an issue while analyzing your data. Please try rephrasing the request.",
                error=str(exc),
            )

    def _generate_sql_plan(self, question: str) -> SQLPlan:
        """Use the LLM to convert a natural-language question into SQL."""
        messages = [
            {
                "role": "system",
                "content": self._sql_system_prompt(),
            },
            {
                "role": "user",
                "content": question.strip(),
            },
        ]
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=messages,
                temperature=0.0,
                max_tokens=600,
                top_p=1,
            )
        except OpenAIError as exc:
            raise SQLGenerationError(f"Model error while generating SQL: {exc}") from exc

        content = response.choices[0].message.content.strip()
        plan_data = self._extract_json(content)

        sql = plan_data.get("sql", "").strip()
        if not sql:
            raise SQLGenerationError("The assistant did not return SQL.")
        if not self._is_select_query(sql):
            raise SQLGenerationError("Only read-only SELECT/WITH queries are allowed.")

        reasoning = plan_data.get("reasoning") or plan_data.get("analysis") or ""
        confidence = float(plan_data.get("confidence", 0.5))
        confidence = max(0.0, min(confidence, 1.0))
        return SQLPlan(sql=sql, reasoning=reasoning, confidence=confidence)

    def _execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Run a SQL query against the nutrition SQLite database."""
        db_path = Config.database_path()
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise SQLExecutionError(f"Unable to connect to database: {exc}") from exc

        try:
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(self.MAX_ROWS)
            return [self._normalize_row(dict(row)) for row in rows]
        except sqlite3.Error as exc:
            raise SQLExecutionError(f"Database error: {exc}") from exc
        finally:
            conn.close()

    def _summarize_answer(self, question: str, plan: SQLPlan, rows: List[Dict[str, Any]]) -> str:
        """Send the SQL output back through the LLM for a grounded explanation."""
        system_prompt = (
            self.profile_system_prompt
            + "\nAlways base your answers strictly on the data provided. "
              "If there is no relevant data, say so instead of guessing."
        )
        result_preview = json.dumps(rows[:20], indent=2, ensure_ascii=False)
        row_count = len(rows)
        user_message = (
            f"Question: {question.strip()}\n"
            f"SQL Query: {plan.sql}\n"
            f"SQL reasoning: {plan.reasoning}\n"
            f"Row count: {row_count}\n"
            f"Result sample (JSON):\n{result_preview}\n\n"
            "Nutrition profile (YAML):\n"
            f"{self.profile_yaml}\n"
            "Write a concise, encouraging answer. Reference concrete numbers when possible."
        )

        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=Config.MODEL_TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                top_p=Config.TOP_P,
            )
        except OpenAIError as exc:
            raise SQLExecutionError(f"Model error while summarizing answer: {exc}") from exc

        return response.choices[0].message.content.strip()

    def _sql_system_prompt(self) -> str:
        example_queries = self.schema.get("example_queries", [])
        sample_text = "\n".join(
            f"- {ex.get('name')}: {ex.get('sql','').strip()}"
            for ex in example_queries
        )
        return (
            "You are an elite SQLite analyst for a vegan nutrition tracker.\n"
            "Follow the rules:\n"
            "1. Only output JSON with keys sql, reasoning, confidence.\n"
            "2. SQL must be a single SELECT or WITH statement compatible with SQLite.\n"
            "3. Never modify data (no INSERT/UPDATE/DELETE).\n"
            "4. Use meaningful column aliases for aggregates.\n"
            f"{self.schema_context}\n"
            "Full database schema (YAML) for reference:\n"
            f"{self.schema_yaml}\n"
            "Nutrition profile and system prompt (YAML):\n"
            f"{self.profile_yaml}\n"
            "Example query patterns:\n"
            f"{sample_text}\n"
            "Respond with JSON only."
        )

    @staticmethod
    def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any non-JSON-serializable values into strings."""
        normalized = {}
        for key, value in row.items():
            if isinstance(value, bytes):
                normalized[key] = value.decode("utf-8")
            else:
                normalized[key] = value
        return normalized

    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:
        """Handle raw JSON or fenced code block JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise SQLGenerationError("Unable to parse SQL plan JSON.")
            return json.loads(match.group(0))

    @staticmethod
    def _is_select_query(sql: str) -> bool:
        stripped = sql.strip().lower()
        return stripped.startswith("select") or stripped.startswith("with")

    def _build_schema_context(self) -> str:
        """Format schema YAML into readable bullet points for prompting."""
        table = self.schema.get("table", "meals")
        description = self.schema.get("description", "")
        columns = self.schema.get("columns", [])
        column_lines = []
        for col in columns:
            bits = [col.get("name", ""), f"({col.get('type','')})"]
            if col.get("description"):
                bits.append(f"- {col['description']}")
            if col.get("allowed_values"):
                bits.append(f"Allowed: {', '.join(col['allowed_values'])}")
            column_lines.append(" ".join(bit for bit in bits if bit))
        return (
            f"Table `{table}`: {description}\n"
            "Columns:\n"
            + "\n".join(f"- {line}" for line in column_lines)
        )
