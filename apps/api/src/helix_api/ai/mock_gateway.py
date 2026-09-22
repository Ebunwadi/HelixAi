import json
from collections.abc import AsyncIterator
from typing import Any

from helix_api.ai.types import (
    ModelMessage,
    ModelResponse,
    ModelStreamEvent,
    ModelUsage,
)


class MockModelGateway:
    """Deterministic local provider used when Azure credentials are not configured."""

    model_name = "helix-mock-v1"

    @staticmethod
    def _last_user_text(messages: list[ModelMessage]) -> str:
        # Looking from the end mirrors a normal chat turn: the newest user
        # message is the input the mock provider should respond to.
        return next(
            (message.content for message in reversed(messages) if message.role == "user"),
            "",
        )

    @staticmethod
    def _estimated_tokens(text: str) -> int:
        # This is intentionally only a rough testing estimate. Real Azure calls
        # use token usage reported by the model provider.
        return max(1, len(text) // 4)

    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> ModelResponse:
        user_text = self._last_user_text(messages)

        # A deterministic response lets tests assert exact behaviour without
        # depending on network access or the variability of a real LLM.
        text = f"Mock model response — no Azure model call was made. You asked: {user_text}"

        return ModelResponse(
            text=text,
            model=self.model_name,
            response_id="mock-response",
            usage=ModelUsage(
                input_tokens=self._estimated_tokens(" ".join(item.content for item in messages)),
                output_tokens=self._estimated_tokens(text),
            ),
            latency_ms=1,
        )

    async def generate_structured(
        self,
        *,
        messages: list[ModelMessage],
        schema_name: str,
        schema: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> ModelResponse:
        user_text = self._last_user_text(messages)
        lower = user_text.lower()

        # The mock imitates the shape of structured model output; it is not
        # intended to imitate real language understanding.
        customer_name = "Acme" if "acme" in lower else None
        issue_type = (
            "authentication"
            if any(term in lower for term in ("sso", "login", "authentication", "saml"))
            else "general"
        )
        time_reference = "yesterday" if "yesterday" in lower else None

        payload = {
            "customer_name": customer_name,
            "issue_type": issue_type,
            "time_reference": time_reference,
            "requested_actions": ["investigate"],
            "summary": user_text,
        }
        text = json.dumps(payload)

        return ModelResponse(
            text=text,
            model=self.model_name,
            response_id=f"mock-{schema_name}",
            usage=ModelUsage(
                input_tokens=self._estimated_tokens(" ".join(item.content for item in messages)),
                output_tokens=self._estimated_tokens(text),
            ),
            latency_ms=1,
        )

    async def stream(
        self,
        *,
        messages: list[ModelMessage],
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[ModelStreamEvent]:
        response = await self.generate(messages=messages, max_output_tokens=max_output_tokens)

        # Split the deterministic response into word-sized chunks so the frontend
        # exercises the same streaming path used with Azure.
        words = response.text.split(" ")
        for index, word in enumerate(words):
            suffix = "" if index == len(words) - 1 else " "
            yield ModelStreamEvent(type="text_delta", delta=f"{word}{suffix}")

        yield ModelStreamEvent(type="completed", response=response)
