import json

import pytest

from helix_api.ai.mock_gateway import MockModelGateway
from helix_api.ai.types import ModelMessage


@pytest.mark.asyncio
async def test_mock_gateway_generates_text_and_usage() -> None:
    gateway = MockModelGateway()

    response = await gateway.generate(
        messages=[
            ModelMessage(role="system", content="Be concise."),
            ModelMessage(role="user", content="Investigate Acme."),
        ]
    )

    assert "Investigate Acme." in response.text
    assert response.model == "helix-mock-v1"
    assert response.usage.input_tokens is not None
    assert response.usage.output_tokens is not None


@pytest.mark.asyncio
async def test_mock_gateway_structured_output_is_json() -> None:
    gateway = MockModelGateway()

    response = await gateway.generate_structured(
        messages=[ModelMessage(role="user", content="Investigate Acme SSO from yesterday.")],
        schema_name="investigation_intent",
        schema={},
    )

    payload = json.loads(response.text)
    assert payload["customer_name"] == "Acme"
    assert payload["issue_type"] == "authentication"
    assert payload["time_reference"] == "yesterday"


@pytest.mark.asyncio
async def test_mock_gateway_stream_emits_deltas_and_completion() -> None:
    gateway = MockModelGateway()
    event_types: list[str] = []
    text = ""

    async for event in gateway.stream(messages=[ModelMessage(role="user", content="Hello")]):
        event_types.append(event.type)
        if event.delta:
            text += event.delta

    assert "Hello" in text
    assert event_types[-1] == "completed"
