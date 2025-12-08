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
    
    # Model Parameters
    MODEL_TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    TOP_P = 0.95
    TOP_K = 50
    REPETITION_PENALTY = 1.1
    
    # App Configuration
    APP_TITLE = "🍽️ Vegan Nutritionist Assistant"
    PAGE_ICON = "🥗"
    
    # API Endpoints
    HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models"
    
    @classmethod
    def get_model_endpoint(cls):
        """Get the full model endpoint URL."""
        return f"{cls.HUGGINGFACE_API_URL}/{cls.MODEL_NAME}"
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        if not cls.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is not set")
        return True
