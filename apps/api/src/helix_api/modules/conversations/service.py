from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.conversations.models import Conversation
from helix_api.modules.conversations.repository import ConversationRepository


class ConversationService:
    def __init__(self, repository: ConversationRepository) -> None:
        self.repository = repository

    async def create(
        self,
        *,
        context: CurrentContext,
        title: str,
    ) -> Conversation:
        return await self.repository.create(
            tenant_id=context.tenant_id,
            created_by=context.user_id,
            title=title,
        )

    async def list(self, context: CurrentContext) -> list[Conversation]:
        return await self.repository.list_for_user(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
