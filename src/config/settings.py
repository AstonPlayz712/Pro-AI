"""Settings and configuration management using python-dotenv"""

import os
from functools import lru_cache
from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self):
        # Load .env file
        load_dotenv()

        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")

        # Anthropic Configuration
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

        # Google Configuration
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_model = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")

        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")

        # Default Model
        self.default_model = os.getenv("DEFAULT_MODEL", "openai")

        # Server Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_debug = os.getenv("API_DEBUG", "false").lower() == "true"

        # Memory Configuration
        self.memory_file = os.getenv("MEMORY_FILE", "data/memory.json")
        self.max_memory_entries = int(os.getenv("MAX_MEMORY_ENTRIES", "1000"))

    def get_model_config(self, model_name: str) -> dict:
        """Get configuration for a specific model"""
        configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            },
            "google": {
                "api_key": self.google_api_key,
                "model": self.google_model,
            },
            "ollama": {
                "base_url": self.ollama_base_url,
                "model": self.ollama_model,
            },
        }
        return configs.get(model_name, {})


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
