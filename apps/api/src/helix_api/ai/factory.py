from functools import lru_cache

from helix_api.ai.mock_gateway import MockModelGateway
from helix_api.ai.openai_gateway import OpenAIResponsesGateway
from helix_api.ai.types import ModelGateway
from helix_api.core.config import get_settings
from helix_api.core.errors import ModelConfigurationError


@lru_cache
def get_model_gateway() -> ModelGateway:
    settings = get_settings()

    if settings.helix_model_provider == "mock":
        return MockModelGateway()

    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_deployment
    ):
        raise ModelConfigurationError(
            "Azure OpenAI requires AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT"
        )

    return OpenAIResponsesGateway(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        deployment=settings.azure_openai_deployment,
        default_max_output_tokens=settings.helix_model_max_output_tokens,
    )
