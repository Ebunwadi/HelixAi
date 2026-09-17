from fastapi import APIRouter, status

from helix_api.modules.auth.dependencies import CurrentContextDependency, SessionDependency
from helix_api.modules.conversations.repository import ConversationRepository
from helix_api.modules.conversations.schemas import ConversationCreate, ConversationRead
from helix_api.modules.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


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
