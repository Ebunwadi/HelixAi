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

    # Authentication.
    helix_auth_mode: Literal["dev", "jwt"] = "dev"
    helix_auth_issuer: str | None = None
    helix_auth_audience: str | None = None
    helix_auth_jwks_url: str | None = None

    # Generation model configuration introduced in Sprint 3.
    helix_model_provider: Literal["mock", "azure_openai"] = "mock"
    helix_model_max_output_tokens: int = 800
    helix_model_history_limit: int = 20
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None

    # Sprint 4 RAG configuration. Local providers keep development and CI
    # independent of cloud credentials while using the same application interfaces.
    helix_embedding_provider: Literal["mock", "azure_openai"] = "mock"
    helix_rag_storage_provider: Literal["local", "azure_blob"] = "local"
    helix_rag_search_provider: Literal["local", "azure_ai_search"] = "local"
    helix_embedding_dimensions: int = 64
    helix_chunk_size: int = 1200
    helix_chunk_overlap: int = 200
    helix_rag_top_k: int = 5
    helix_document_max_bytes: int = 5_000_000
    helix_local_rag_path: str = ".helix"

    azure_openai_embedding_deployment: str | None = None
    azure_storage_connection_string: str | None = None
    azure_storage_container: str = "helix-knowledge"
    azure_ai_search_endpoint: str | None = None
    azure_ai_search_api_key: str | None = None
    azure_ai_search_index: str = "helix-knowledge"

    @property
    def cors_origin_list(self) -> list[str]:
        """Convert the comma-separated CORS setting into FastAPI's list format."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    # Settings are effectively immutable for one process, so cache the parsed object.
    return Settings()
