from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from helix_api.modules.conversations.models import ConversationStatus


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=255)


class ConversationRead(BaseModel):
    id: UUID
    title: str
    status: ConversationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
