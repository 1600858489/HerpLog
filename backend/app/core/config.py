from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "HerpLog API"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./herplog.db"
    jwt_secret_key: str = Field(default="development-only-secret-key-32-bytes!")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    upload_dir: Path = Path("./uploads")
    redis_url: str = "redis://localhost:6379/0"
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    def validate_production_security(self) -> None:
        """Reject the development JWT secret when running outside development."""
        if self.environment != "development" and self.jwt_secret_key == "development-only-secret-key-32-bytes!":
            raise ValueError("JWT secret key must be configured outside development")


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    settings = Settings()
    settings.validate_production_security()
    return settings
