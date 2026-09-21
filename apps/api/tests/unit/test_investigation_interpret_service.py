import pytest

from helix_api.ai.mock_gateway import MockModelGateway
from helix_api.modules.ai.service import InvestigationInterpretService


@pytest.mark.asyncio
async def test_interpretation_returns_typed_intent_and_metadata() -> None:
    result = await InvestigationInterpretService(MockModelGateway()).interpret(
        "Investigate Acme's SSO issue from yesterday."
    )

    assert result.intent.customer_name == "Acme"
    assert result.intent.issue_type == "authentication"
    assert result.intent.time_reference == "yesterday"
    assert result.model.model == "helix-mock-v1"
