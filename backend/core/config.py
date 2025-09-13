"""
Backend configuration for M32 Business Intelligence Copilot.
Handles database, JWT, and application settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "M32 Business Intelligence Copilot"
    debug: bool = Field(False, env="DEBUG")
    version: str = "1.0.0"
    
    # Security
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="SECRET_KEY"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = Field("sqlite:///./m32_business_copilot.db", env="DATABASE_URL")
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # AI Configuration (inherit from main config)
    groq_api_key: str = Field("", env="GROQ_API_KEY")
    groq_model_name: str = Field("openai/gpt-oss-120b", env="GROQ_MODEL_NAME")
    
    # Google OAuth Configuration
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field("http://localhost:8000/api/auth/google/callback", env="GOOGLE_REDIRECT_URI")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Allow extra fields from env file
    }


# Global settings instance
settings = Settings()
