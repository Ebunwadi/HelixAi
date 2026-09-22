from uuid import UUID

from helix_api.ai.prompts import CHAT_SYSTEM_PROMPT
from helix_api.ai.types import ModelGateway, ModelMessage, ModelResponse
from helix_api.core.config import get_settings
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.conversations.message_repository import MessageRepository
from helix_api.modules.conversations.models import Message, MessageRole
from helix_api.modules.conversations.repository import ConversationRepository
from helix_api.modules.conversations.service import ConversationService


class ConversationChatService:
    """Coordinates conversation persistence and model calls."""

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        messages: MessageRepository,
        gateway: ModelGateway,
    ) -> None:
        self.conversations = conversations
        self.messages = messages
        self.gateway = gateway

    async def history(
        self,
        *,
        context: CurrentContext,
        conversation_id: UUID,
    ) -> list[Message]:
        # Check ownership before reading messages. The conversation ID supplied by
        # the browser is never enough on its own to grant access.
        await ConversationService(self.conversations).get_owned(
            context=context,
            conversation_id=conversation_id,
        )

        return await self.messages.list_for_conversation(
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
        )

    async def prepare_turn(
        self,
        *,
        context: CurrentContext,
        conversation_id: UUID,
        content: str,
    ) -> tuple[Message, list[ModelMessage]]:
        # Reuse the same tenant/user ownership rule used by ordinary conversation
        # reads before allowing any text to reach the model.
        await ConversationService(self.conversations).get_owned(
            context=context,
            conversation_id=conversation_id,
        )

        settings = get_settings()

        # Load only recent history so every request does not grow forever as a
        # conversation becomes longer.
        history = await self.messages.list_for_conversation(
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            limit=settings.helix_model_history_limit,
        )

        # Persist the user's message in our own database before generating the
        # assistant response.
        user_message = await self.messages.create(
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

        # Model context is constructed explicitly: system instructions first,
        # then recent history, followed by the newest user message.
        model_messages = [ModelMessage(role="system", content=CHAT_SYSTEM_PROMPT)]
        model_messages.extend(
            ModelMessage(role=message.role.value, content=message.content) for message in history
        )
        model_messages.append(ModelMessage(role="user", content=content))

        return user_message, model_messages

    async def persist_assistant(
        self,
        *,
        context: CurrentContext,
        conversation_id: UUID,
        response: ModelResponse,
    ) -> Message:
        # Store observability metadata alongside the text so later sprints can
        # compare model behaviour, latency and token usage.
        return await self.messages.create(
            tenant_id=context.tenant_id,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response.text,
            model_name=response.model,
            provider_response_id=response.response_id,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=response.latency_ms,
        )

    async def complete_turn(
        self,
        *,
        context: CurrentContext,
        conversation_id: UUID,
        content: str,
    ) -> tuple[Message, Message]:
        user_message, model_messages = await self.prepare_turn(
            context=context,
            conversation_id=conversation_id,
            content=content,
        )

        # This service calls the provider-independent gateway, not Azure directly.
        response = await self.gateway.generate(messages=model_messages)

        assistant_message = await self.persist_assistant(
            context=context,
            conversation_id=conversation_id,
            response=response,
        )
        return user_message, assistant_message
