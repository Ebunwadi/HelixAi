from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.db.session import get_session
from helix_api.modules.auth.dependencies import get_current_context
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.conversations.repository import ConversationRepository
from helix_api.modules.conversations.schemas import ConversationCreate, ConversationRead
from helix_api.modules.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    context: CurrentContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> ConversationRead:
    conversation = await ConversationService(ConversationRepository(session)).create(
        context=context,
        title=body.title,
    )
    return ConversationRead.model_validate(conversation)


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    context: CurrentContext = Depends(get_current_context),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationRead]:
    conversations = await ConversationService(ConversationRepository(session)).list(context)
    return [ConversationRead.model_validate(item) for item in conversations]
