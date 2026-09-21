from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.modules.conversations.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, tenant_id: UUID, created_by: UUID, title: str) -> Conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            created_by=created_by,
            title=title,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def list_for_user(self, *, tenant_id: UUID, user_id: UUID) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.created_by == user_id,
            )
            .order_by(Conversation.created_at.desc())
        )
        return list(result.scalars().all())
