from pydantic import ValidationError

from helix_api.ai.prompts import INVESTIGATION_INTENT_SYSTEM_PROMPT
from helix_api.ai.types import ModelGateway, ModelMessage
from helix_api.core.errors import ModelProviderError
from helix_api.modules.ai.schemas import (
    InvestigationIntent,
    InvestigationInterpretResponse,
    ModelMetadata,
)


class InvestigationInterpretService:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway = gateway

    async def interpret(self, text: str) -> InvestigationInterpretResponse:
        response = await self.gateway.generate_structured(
            messages=[
                ModelMessage(role="system", content=INVESTIGATION_INTENT_SYSTEM_PROMPT),
                ModelMessage(role="user", content=text),
            ],
            schema_name="investigation_intent",
            schema=InvestigationIntent.model_json_schema(),
        )

        try:
            intent = InvestigationIntent.model_validate_json(response.text)
        except ValidationError as exc:
            raise ModelProviderError("The model returned invalid structured output") from exc

        return InvestigationInterpretResponse(
            intent=intent,
            model=ModelMetadata(
                model=response.model,
                response_id=response.response_id,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=response.latency_ms,
            ),
        )
