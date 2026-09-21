import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from helix_api.db.session import get_session_factory
from helix_api.main import app
from helix_api.modules.conversations.models import Conversation, Message
from helix_api.modules.tenants.models import Membership, MembershipRole, MembershipStatus, Tenant
from helix_api.modules.users.models import User

pytestmark = pytest.mark.skipif(
    os.getenv("HELIX_RUN_DB_TESTS") != "1",
    reason="Database integration tests require HELIX_RUN_DB_TESTS=1",
)


@pytest.mark.asyncio
async def test_chat_turn_structured_output_and_streaming_use_mock_provider() -> None:
    factory = get_session_factory()
    tenant_id = uuid4()
    user_id = uuid4()
    conversation_id = uuid4()
    subject = f"chat-{uuid4()}"

    async with factory() as session:
        session.add_all(
            [
                Tenant(id=tenant_id, name="Chat Tenant", slug=f"chat-{uuid4()}"),
                User(id=user_id, external_identity_id=subject, email="chat@example.com"),
            ]
        )
        await session.flush()
        session.add(
            Membership(
                tenant_id=tenant_id,
                user_id=user_id,
                role=MembershipRole.OPERATOR,
                status=MembershipStatus.ACTIVE,
            )
        )
        session.add(
            Conversation(
                id=conversation_id,
                tenant_id=tenant_id,
                created_by=user_id,
                title="Sprint 3 chat",
            )
        )
        await session.commit()

    headers = {
        "X-Helix-Subject": subject,
        "X-Helix-Tenant-Id": str(tenant_id),
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
            json={"content": "Investigate Acme's SSO issue."},
        )
        assert chat.status_code == 201
        chat_body = chat.json()
        assert chat_body["user_message"]["role"] == "user"
        assert chat_body["assistant_message"]["role"] == "assistant"
        assert chat_body["assistant_message"]["model_name"] == "helix-mock-v1"
        assert chat_body["assistant_message"]["input_tokens"] > 0

        structured = await client.post(
            "/api/v1/ai/interpret-investigation",
            headers=headers,
            json={"text": "Investigate Acme's SSO issue from yesterday."},
        )
        assert structured.status_code == 200
        assert structured.json()["intent"]["customer_name"] == "Acme"
        assert structured.json()["intent"]["time_reference"] == "yesterday"

        stream = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages/stream",
            headers=headers,
            json={"content": "Give me the next step."},
        )
        assert stream.status_code == 200
        assert stream.headers["content-type"].startswith("text/event-stream")
        assert "event: token.delta" in stream.text
        assert "event: message.completed" in stream.text

        history = await client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
        )
        assert history.status_code == 200
        assert len(history.json()) == 4

    async with factory() as session:
        await session.execute(delete(Message).where(Message.conversation_id == conversation_id))
        await session.execute(delete(Conversation).where(Conversation.id == conversation_id))
        await session.execute(delete(Membership).where(Membership.user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()
