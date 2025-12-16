from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from openai import OpenAIError

from config import Config


@dataclass
class MealEntryResult:
    row: Optional[Dict[str, Any]]
    summary: str
    error: Optional[str] = None


class MealLogger:
    """LLM-assisted logger that converts meal descriptions into DB rows."""

    def __init__(self):
        Config.validate()
        self.client = Config.get_openai_client()
        self.schema = Config.load_database_schema()
        self.schema_text = Config.load_database_schema_text()
        self.table_name = self.schema.get("table", "meals")
        self.columns = [col["name"] for col in self.schema.get("columns", [])]
        self.required_columns = [
            col["name"] for col in self.schema.get("columns", []) if col.get("required")
        ]
        self.numeric_columns = {
            col["name"]
            for col in self.schema.get("columns", [])
            if str(col.get("type", "")).upper() in {"FLOAT", "INTEGER", "REAL", "NUMERIC"}
        }

    @staticmethod
    def clarification_prompt() -> str:
        return (
            "Happy to log that meal! Please share approximate quantities (cups, grams, Tbsp) "
            "for each component, when you ate it, and whether it was breakfast, lunch, dinner, or a snack."
        )

    def build_entry(self, description: str, details: str) -> MealEntryResult:
        """Use the LLM to turn the meal description into a structured row."""
        now = datetime.now()
        today_iso = now.strftime("%Y-%m-%d")
        now_time = now.strftime("%H:%M:%S")
        user_message = (
            "A user wants to log a vegan meal. Craft a detailed meal entry using the database schema.\n"
            f"Original note:\n{description.strip()}\n\n"
            f"Additional details:\n{details.strip()}\n\n"
            "Return JSON with two keys: `row` containing the column/value map, "
            "and `summary` describing the meal in one sentence."
        )
        system_message = (
            "You are a meticulous vegan nutrition meal logging assistant. "
            "Use nutrition knowledge to estimate macros and micronutrients in realistic quantities. "
            "If data is missing, make a reasonable estimate but avoid impossible values. "
            "Use ISO date format (YYYY-MM-DD) and 24h time (HH:MM:SS). "
            "Allowed meal_type values: Breakfast, Lunch, Dinner, Snack, Drink.\n\n"
            f"Today's date is {today_iso} and the current time is {now_time}. "
            "When the user mentions relative phrases like 'today', 'this morning', or 'yesterday', "
            "resolve them using this reference.\n\n"
            "Database schema:\n"
            f"{self.schema_text}\n"
            "Respond with JSON only."
        )
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.4,
                max_tokens=600,
            )
        except OpenAIError as exc:
            return MealEntryResult(row=None, summary="", error=str(exc))

        content = response.choices[0].message.content or ""
        try:
            data = self._extract_json(content)
        except ValueError as exc:
            return MealEntryResult(row=None, summary="", error=str(exc))

        row = data.get("row")
        summary = data.get("summary", "").strip()
        if not isinstance(row, dict):
            return MealEntryResult(row=None, summary="", error="Model did not return a row object.")

        normalized_row = self._normalize_row(row)
        missing = [col for col in self.required_columns if not normalized_row.get(col)]
        if missing:
            return MealEntryResult(
                row=None,
                summary="",
                error=f"The following required fields are missing: {', '.join(missing)}.",
            )

        return MealEntryResult(row=normalized_row, summary=summary or "Here are the meal details.")

    def insert_entry(self, row: Dict[str, Any]) -> None:
        """Insert the prepared row into the meals table."""
        filtered = {k: v for k, v in row.items() if v not in (None, "", [])}
        columns = list(filtered.keys())
        if not columns:
            raise ValueError("Meal row is empty.")
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        values: List[Any] = [filtered[col] for col in columns]

        conn = sqlite3.connect(Config.database_path())
        try:
            conn.execute(sql, values)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _extract_json(content: str) -> Dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        try:
            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise ValueError("Unable to parse meal logging JSON.")
            return json.loads(match.group(0), strict=False)

    def _normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        now = datetime.now()
        defaults = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "meal_source": row.get("meal_source") or "Homemade",
        }
        for key in self.columns:
            value = row.get(key)
            if value in (None, "", "null", "None"):
                if key in defaults:
                    normalized[key] = defaults[key]
                continue
            if key in self.numeric_columns:
                try:
                    normalized[key] = float(value)
                except (TypeError, ValueError):
                    continue
            else:
                normalized[key] = str(value)
        return normalized
