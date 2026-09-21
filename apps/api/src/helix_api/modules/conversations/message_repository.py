from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.modules.conversations.models import Message, MessageRole


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        model_name: str | None = None,
        provider_response_id: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: int | None = None,
    ) -> Message:
        message = Message(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_name=model_name,
            provider_response_id=provider_response_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_for_conversation(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.tenant_id == tenant_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at.desc())
        )
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return list(reversed(result.scalars().all()))
