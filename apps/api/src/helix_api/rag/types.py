from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TextChunk:
    """A deterministic piece of extracted document text."""

    index: int
    text: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class IndexedChunk:
    """Chunk shape written to either the local or Azure search index."""

    chunk_id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class SearchHit:
    """Provider-independent retrieval result returned to RAG services."""

    chunk_id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    score: float


class EmbeddingGateway(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class DocumentStorage(Protocol):
    async def save(
        self,
        *,
        tenant_id: UUID,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> str: ...


class SearchIndex(Protocol):
    async def index_chunks(self, chunks: list[IndexedChunk]) -> None: ...

    async def search(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        query_embedding: list[float],
        top_k: int,
    ) -> list[SearchHit]: ...
