"""
Configuration management for the FastAPI application.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    app_name: str = "Market Analysis API"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        """Pydantic config."""
        env_file = ".env"

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
