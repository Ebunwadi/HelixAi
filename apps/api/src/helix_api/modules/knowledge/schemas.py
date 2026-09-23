from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from helix_api.modules.ai.schemas import ModelMetadata
from helix_api.modules.knowledge.models import DocumentStatus


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class KnowledgeBaseRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    filename: str
    content_type: str | None
    status: DocumentStatus
    error_message: str | None
    chunk_count: int
    created_at: datetime
    indexed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    number: int
    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    score: float
    excerpt: str


class KnowledgeSearchResponse(BaseModel):
    query: str
    citations: list[Citation]


class RagAnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10_000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class RagAnswerResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model: ModelMetadata | None = None
