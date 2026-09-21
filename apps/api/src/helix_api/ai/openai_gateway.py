from collections.abc import AsyncIterator
from time import perf_counter
from typing import Any

from openai import APIError, AsyncOpenAI

from helix_api.ai.types import ModelMessage, ModelResponse, ModelStreamEvent, ModelUsage
from helix_api.core.errors import ModelProviderError


class OpenAIResponsesGateway:
    """Direct OpenAI Responses API adapter configured for an Azure OpenAI v1 endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        deployment: str,
        default_max_output_tokens: int,
    ) -> None:
        self.deployment = deployment
        self.default_max_output_tokens = default_max_output_tokens
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=f"{endpoint.rstrip('/')}/openai/v1/",
        )

    @staticmethod
    def _input(messages: list[ModelMessage]) -> Any:
        return [{"role": message.role, "content": message.content} for message in messages]

    @staticmethod
    def _usage(response: Any) -> ModelUsage:
        usage = getattr(response, "usage", None)
        return ModelUsage(
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )

    def _result(
        self,
        response: Any,
        *,
        started_at: float,
        text: str | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            text=text if text is not None else getattr(response, "output_text", ""),
            model=getattr(response, "model", self.deployment),
            response_id=getattr(response, "id", None),
            usage=self._usage(response),
            latency_ms=round((perf_counter() - started_at) * 1000),
        )

    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> ModelResponse:
        started_at = perf_counter()
        try:
            response = await self.client.responses.create(
                model=self.deployment,
                input=self._input(messages),
                max_output_tokens=max_output_tokens or self.default_max_output_tokens,
                store=False,
            )
        except APIError as exc:
            raise ModelProviderError() from exc
        return self._result(response, started_at=started_at)

    async def generate_structured(
        self,
        *,
        messages: list[ModelMessage],
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> ModelResponse:
        started_at = perf_counter()
        text_config: Any = {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        }
        try:
            response = await self.client.responses.create(
                model=self.deployment,
                input=self._input(messages),
                max_output_tokens=max_output_tokens or self.default_max_output_tokens,
                text=text_config,
                store=False,
            )
        except APIError as exc:
            raise ModelProviderError() from exc
        return self._result(response, started_at=started_at)

    async def stream(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[ModelStreamEvent]:
        started_at = perf_counter()
        parts: list[str] = []
        try:
            stream = await self.client.responses.create(
                model=self.deployment,
                input=self._input(messages),
                max_output_tokens=max_output_tokens or self.default_max_output_tokens,
                store=False,
                stream=True,
            )
            async for event in stream:
                event_type = getattr(event, "type", "")
                if event_type == "response.output_text.delta":
                    delta = getattr(event, "delta", "")
                    if delta:
                        parts.append(delta)
                        yield ModelStreamEvent(type="text_delta", delta=delta)
                elif event_type == "response.completed":
                    response = getattr(event, "response", None)
                    if response is not None:
                        yield ModelStreamEvent(
                            type="completed",
                            response=self._result(
                                response,
                                started_at=started_at,
                                text="".join(parts),
                            ),
                        )
        except APIError as exc:
            raise ModelProviderError() from exc
