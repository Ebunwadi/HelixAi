from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol

# These are the message roles our own application understands. Keeping them in
# HelixAI types prevents provider-specific SDK objects leaking into business code.
ModelRole = Literal["system", "developer", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class ModelMessage:
    """Provider-independent representation of one message sent to a model."""

    role: ModelRole
    content: str


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Token counts returned by the provider, when available."""

    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Normalized model response used by the rest of HelixAI."""

    text: str
    model: str
    response_id: str | None
    usage: ModelUsage
    latency_ms: int


@dataclass(frozen=True, slots=True)
class ModelStreamEvent:
    """Small event contract used while a model response is streaming."""

    type: Literal["text_delta", "completed"]
    delta: str | None = None
    response: ModelResponse | None = None


class ModelGateway(Protocol):
    """Interface all model providers must satisfy.

    Application services depend on this protocol instead of importing Azure/OpenAI
    SDK types directly. That makes local mocking and future provider swaps simple.
    """

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
