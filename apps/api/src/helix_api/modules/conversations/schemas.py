from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from helix_api.modules.conversations.models import ConversationStatus, MessageRole


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=255)


class ConversationRead(BaseModel):
    id: UUID
    title: str
    status: ConversationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    model_name: str | None = None
    provider_response_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatTurnResponse(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead
