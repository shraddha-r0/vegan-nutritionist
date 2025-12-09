import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Hugging Face Configuration
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")
    
    # Paths & Data Files
    FRONTEND_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = FRONTEND_DIR.parent
    DB_PATH = PROJECT_ROOT / "backend" / "data" / "nutrition.db"
    SCHEMA_PATH = FRONTEND_DIR / "config" / "database_schema.yaml"
    PROFILE_PATH = FRONTEND_DIR / "config" / "nutrition_profile.yaml"

    # Model + API configuration
    HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
    
    # Model Parameters
    MODEL_TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    TOP_P = 0.95
    
    # App Configuration
    APP_TITLE = "🍽️ Vegan Nutritionist Assistant"
    PAGE_ICON = "🥗"
    
    @classmethod
    def get_openai_client(cls):
        """Get an OpenAI client configured for Hugging Face router."""
        from openai import OpenAI
        return OpenAI(
            base_url=cls.HUGGINGFACE_BASE_URL,
            api_key=cls.HUGGINGFACE_API_KEY
        )
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required environment variables and files are available."""
        if not cls.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is not set")
        if not cls.DB_PATH.exists():
            raise FileNotFoundError(f"Database file missing at {cls.DB_PATH}")
        if not cls.SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Database schema file missing at {cls.SCHEMA_PATH}")
        if not cls.PROFILE_PATH.exists():
            raise FileNotFoundError(f"Nutrition profile file missing at {cls.PROFILE_PATH}")
        return True

    @classmethod
    @lru_cache(maxsize=1)
    def load_database_schema(cls) -> Dict[str, Any]:
        """Load the YAML schema description used to guide SQL generation."""
        with cls.SCHEMA_PATH.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    @classmethod
    @lru_cache(maxsize=1)
    def load_nutrition_profile(cls) -> Dict[str, Any]:
        """Load the nutrition profile that feeds the assistant personality."""
        with cls.PROFILE_PATH.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    @classmethod
    def database_path(cls) -> Path:
        """Expose the sqlite database path for downstream helpers."""
        return cls.DB_PATH
