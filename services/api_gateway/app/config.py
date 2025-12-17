from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API gateway service."""

    app_name: str = "VentureBots API Gateway"
    database_url: str = "sqlite:///./data/chat.sqlite3"
    orchestrator_timeout_seconds: float = 20.0
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VENTUREBOTS_",
        case_sensitive=False,
        extra="allow",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
