import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Hugging Face Configuration
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")
    
    # API Configuration
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
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
    def validate(cls):
        """Validate that all required environment variables are set."""
        if not cls.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is not set")
        return True
