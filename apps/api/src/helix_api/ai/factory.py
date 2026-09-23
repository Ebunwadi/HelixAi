from functools import lru_cache

from helix_api.ai.mock_gateway import MockModelGateway
from helix_api.ai.openai_gateway import OpenAIResponsesGateway
from helix_api.ai.types import ModelGateway
from helix_api.core.config import get_settings
from helix_api.core.errors import ModelConfigurationError


@lru_cache
def get_model_gateway() -> ModelGateway:
    """Build the configured model provider once for the running process."""

    settings = get_settings()

    # Mock mode keeps local development and CI deterministic and offline.
    if settings.helix_model_provider == "mock":
        return MockModelGateway()

    # Fail early with a clear application error instead of allowing the SDK to
    # fail later with a less helpful authentication/configuration exception.
    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_deployment
    ):
        raise ModelConfigurationError(
            "Azure OpenAI requires AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT"
        )

    # The rest of the application receives the ModelGateway interface and does
    # not need to know that this concrete implementation uses Azure OpenAI.
    return OpenAIResponsesGateway(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        deployment=settings.azure_openai_deployment,
        default_max_output_tokens=settings.helix_model_max_output_tokens,
    )
