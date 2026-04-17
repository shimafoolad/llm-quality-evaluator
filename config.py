import os
from datetime import datetime
from dotenv import load_dotenv


class Config:
    """Central configuration class for managing all application settings"""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration only once"""
        if self._initialized:
            return

        # Load environment variables
        load_dotenv()

        # Environment Configuration
        self.OPIK_API_KEY = os.getenv("OPIK_API_KEY")
        self.OPIK_WORKSPACE = os.getenv("OPIK_WORKSPACE")

        # Model Configuration
        self.LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL")
        self.LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
        self.LLM_SERVER_PORT = os.getenv("LLM_SERVER_PORT")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        self.SWAGGER_BASE_URL = os.getenv("SWAGGER_BASE_URL")
        
        # Mark as initialized
        self._initialized = True

    def validate(self):
        """Validate required configuration settings"""
        required_vars = [
            
            "OPIK_API_KEY",
            "OPIK_WORKSPACE",
            "LLM_API_BASE_URL",
            "LLM_API_KEY",
            "SWAGGER_BASE_URL",
        ]

        missing = [var for var in required_vars if not getattr(self, var)]

        if missing:
            raise ValueError(
                f"Missing required configuration variables: {', '.join(missing)}"
            )

        return True


# Create a global config instance
config = Config()
