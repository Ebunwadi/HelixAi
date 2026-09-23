from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or apps/api/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # General application/network configuration.
    helix_env: str = "local"
    helix_api_host: str = "0.0.0.0"
    helix_api_port: int = 8001
    database_url: str = "postgresql+asyncpg://helix:helix@localhost:5432/helix"
    cors_origins: str = "http://localhost:3000"

    # Authentication is deliberately configurable so local development can use
    # explicit dev headers while production can validate real JWTs.
    helix_auth_mode: Literal["dev", "jwt"] = "dev"
    helix_auth_issuer: str | None = None
    helix_auth_audience: str | None = None
    helix_auth_jwks_url: str | None = None

    # The model provider defaults to a deterministic mock so developers and CI
    # can exercise the complete AI flow without Azure credentials or API cost.
    helix_model_provider: Literal["mock", "azure_openai"] = "mock"
    helix_model_max_output_tokens: int = 800

    # We intentionally send only recent conversation history to the model.
    # This is a simple Sprint 3 context-window policy that later sprints can improve.
    helix_model_history_limit: int = 20

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        """Convert the comma-separated CORS setting into FastAPI's list format."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    # Settings are immutable for a running process in practice, so caching avoids
    # reparsing the environment on every request.
    return Settings()
