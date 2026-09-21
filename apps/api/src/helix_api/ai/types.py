from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol

ModelRole = Literal["system", "developer", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: ModelRole
    content: str


@dataclass(frozen=True, slots=True)
class ModelUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    model: str
    response_id: str | None
    usage: ModelUsage
    latency_ms: int


@dataclass(frozen=True, slots=True)
class ModelStreamEvent:
    type: Literal["text_delta", "completed"]
    delta: str | None = None
    response: ModelResponse | None = None


class ModelGateway(Protocol):
    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> ModelResponse: ...

    async def generate_structured(
        self,
        *,
        messages: list[ModelMessage],
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> ModelResponse: ...

    def stream(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[ModelStreamEvent]: ...
