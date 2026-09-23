from functools import lru_cache
from pathlib import Path

from helix_api.core.config import get_settings
from helix_api.core.errors import RagConfigurationError
from helix_api.rag.embeddings import AzureOpenAIEmbeddingGateway, MockEmbeddingGateway
from helix_api.rag.search import AzureAISearchIndex, LocalSearchIndex
from helix_api.rag.storage import AzureBlobDocumentStorage, LocalDocumentStorage
from helix_api.rag.types import DocumentStorage, EmbeddingGateway, SearchIndex


@lru_cache
def get_embedding_gateway() -> EmbeddingGateway:
    settings = get_settings()

    if settings.helix_embedding_provider == "mock":
        return MockEmbeddingGateway(settings.helix_embedding_dimensions)

    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_embedding_deployment
    ):
        raise RagConfigurationError(
            "Azure embeddings require AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY "
            "and AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        )

    return AzureOpenAIEmbeddingGateway(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        deployment=settings.azure_openai_embedding_deployment,
        dimensions=settings.helix_embedding_dimensions,
    )


@lru_cache
def get_document_storage() -> DocumentStorage:
    settings = get_settings()

    if settings.helix_rag_storage_provider == "local":
        return LocalDocumentStorage(Path(settings.helix_local_rag_path))

    if not settings.azure_storage_connection_string:
        raise RagConfigurationError("Azure Blob Storage requires AZURE_STORAGE_CONNECTION_STRING")

    return AzureBlobDocumentStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_storage_container,
    )


@lru_cache
def get_search_index() -> SearchIndex:
    settings = get_settings()

    if settings.helix_rag_search_provider == "local":
        return LocalSearchIndex(Path(settings.helix_local_rag_path) / "search-index.json")

    if not settings.azure_ai_search_endpoint or not settings.azure_ai_search_api_key:
        raise RagConfigurationError(
            "Azure AI Search requires AZURE_AI_SEARCH_ENDPOINT and AZURE_AI_SEARCH_API_KEY"
        )

    return AzureAISearchIndex(
        endpoint=settings.azure_ai_search_endpoint,
        api_key=settings.azure_ai_search_api_key,
        index_name=settings.azure_ai_search_index,
        dimensions=settings.helix_embedding_dimensions,
    )
