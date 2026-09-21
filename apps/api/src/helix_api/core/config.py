from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or apps/api/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    helix_env: str = "local"
    helix_api_host: str = "0.0.0.0"
    helix_api_port: int = 8000
    database_url: str = "postgresql+asyncpg://helix:helix@localhost:5432/helix"
    cors_origins: str = "http://localhost:3000"

    helix_auth_mode: Literal["dev", "jwt"] = "dev"
    helix_auth_issuer: str | None = None
    helix_auth_audience: str | None = None
    helix_auth_jwks_url: str | None = None

    helix_model_provider: Literal["mock", "azure_openai"] = "mock"
    helix_model_max_output_tokens: int = 800
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
