import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from helix_api.ai.factory import get_model_gateway
from helix_api.core.errors import AppError
from helix_api.db.session import get_session_factory
from helix_api.modules.auth.dependencies import CurrentContextDependency, SessionDependency
from helix_api.modules.conversations.chat_service import ConversationChatService
from helix_api.modules.conversations.message_repository import MessageRepository
from helix_api.modules.conversations.repository import ConversationRepository
from helix_api.modules.conversations.schemas import (
    ChatTurnResponse,
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
)
from helix_api.modules.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _sse(event: str, data: object) -> str:
    """Encode one Server-Sent Event frame for the browser."""
    return f"event: {event}\ndata: {json.dumps(jsonable_encoder(data))}\n\n"


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> ConversationRead:
    conversation = await ConversationService(ConversationRepository(session)).create(
        context=context,
        title=body.title,
    )
    return ConversationRead.model_validate(conversation)


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    context: CurrentContextDependency,
    session: SessionDependency,
) -> list[ConversationRead]:
    conversations = await ConversationService(ConversationRepository(session)).list(context)
    return [ConversationRead.model_validate(item) for item in conversations]


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: UUID,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> list[MessageRead]:
    # Message history is tenant/user protected through the conversation ownership check.
    await ConversationService(ConversationRepository(session)).get_owned(
        context=context,
        conversation_id=conversation_id,
    )

    messages = await MessageRepository(session).list_for_conversation(
        tenant_id=context.tenant_id,
        conversation_id=conversation_id,
    )
    return [MessageRead.model_validate(item) for item in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    conversation_id: UUID,
    body: MessageCreate,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> ChatTurnResponse:
    # Non-streaming path: wait for the complete model response, persist it, then
    # return both messages as a normal JSON response.
    service = ConversationChatService(
        conversations=ConversationRepository(session),
        messages=MessageRepository(session),
        gateway=get_model_gateway(),
    )

    user_message, assistant_message = await service.complete_turn(
        context=context,
        conversation_id=conversation_id,
        content=body.content,
    )

    return ChatTurnResponse(
        user_message=MessageRead.model_validate(user_message),
        assistant_message=MessageRead.model_validate(assistant_message),
    )


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: UUID,
    body: MessageCreate,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> StreamingResponse:
    gateway = get_model_gateway()
    service = ConversationChatService(
        conversations=ConversationRepository(session),
        messages=MessageRepository(session),
        gateway=gateway,
    )

    user_message, model_messages = await service.prepare_turn(
        context=context,
        conversation_id=conversation_id,
        content=body.content,
    )

    # Commit before the long-lived stream begins. Holding a database transaction
    # open while waiting for an LLM would waste a connection and increase lock time.
    await session.commit()

    async def events() -> AsyncIterator[str]:
        # Tell the browser immediately that the user's message is persisted.
        yield _sse("message.created", MessageRead.model_validate(user_message))

        try:
            async for model_event in gateway.stream(messages=model_messages):
                if model_event.type == "text_delta" and model_event.delta:
                    # Small text chunks are forwarded as they arrive from the model.
                    yield _sse("token.delta", {"delta": model_event.delta})

                elif model_event.type == "completed" and model_event.response:
                    # The original request-scoped DB session has already been
                    # committed, so use a fresh short-lived session to persist the
                    # completed assistant message.
                    factory = get_session_factory()
                    async with factory() as write_session:
                        write_service = ConversationChatService(
                            conversations=ConversationRepository(write_session),
                            messages=MessageRepository(write_session),
                            gateway=gateway,
                        )
                        assistant = await write_service.persist_assistant(
                            context=context,
                            conversation_id=conversation_id,
                            response=model_event.response,
                        )
                        await write_session.commit()

                    yield _sse("message.completed", MessageRead.model_validate(assistant))

        except AppError as exc:
            # Once streaming has started we cannot replace the HTTP status code,
            # so application errors are represented as SSE error events.
            yield _sse("error", {"code": exc.code, "message": exc.message})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Ask reverse proxies such as Nginx not to buffer incremental events.
            "X-Accel-Buffering": "no",
        },
    )
