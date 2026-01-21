from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database Configuration (Supabase PostgreSQL)
    database_url: str

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # External JWT Authentication (from main system)
    external_jwt_secret: str  # Shared secret key from main user system

    # Gemini AI Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    # Modern Pydantic V2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore" # This prevents errors if there are extra variables in .env
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()