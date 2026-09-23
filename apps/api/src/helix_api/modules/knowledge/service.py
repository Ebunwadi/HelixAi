from uuid import UUID

from helix_api.ai.prompts import RAG_SYSTEM_PROMPT
from helix_api.ai.types import ModelGateway, ModelMessage
from helix_api.core.config import get_settings
from helix_api.core.errors import AppError, NotFoundError, RagProviderError
from helix_api.modules.ai.schemas import ModelMetadata
from helix_api.modules.auth.schemas import CurrentContext
from helix_api.modules.knowledge.models import Document, KnowledgeBase
from helix_api.modules.knowledge.repository import KnowledgeRepository
from helix_api.modules.knowledge.schemas import (
    Citation,
    KnowledgeSearchResponse,
    RagAnswerResponse,
)
from helix_api.rag.chunking import chunk_text
from helix_api.rag.extraction import extract_text
from helix_api.rag.types import (
    DocumentStorage,
    EmbeddingGateway,
    IndexedChunk,
    SearchHit,
    SearchIndex,
)


class KnowledgeService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    async def create(
        self,
        *,
        context: CurrentContext,
        name: str,
        description: str | None,
    ) -> KnowledgeBase:
        return await self.repository.create_knowledge_base(
            tenant_id=context.tenant_id,
            name=name,
            description=description,
        )

    async def list(self, context: CurrentContext) -> list[KnowledgeBase]:
        return await self.repository.list_knowledge_bases(tenant_id=context.tenant_id)

    async def get_owned(
        self,
        *,
        context: CurrentContext,
        knowledge_base_id: UUID,
    ) -> KnowledgeBase:
        knowledge_base = await self.repository.get_knowledge_base(
            tenant_id=context.tenant_id,
            knowledge_base_id=knowledge_base_id,
        )
        if knowledge_base is None:
            raise NotFoundError("Knowledge base not found")
        return knowledge_base


class KnowledgeIngestionService:
    """Synchronous baseline ingestion pipeline for small Sprint 4 documents."""

    def __init__(
        self,
        *,
        repository: KnowledgeRepository,
        storage: DocumentStorage,
        embeddings: EmbeddingGateway,
        search_index: SearchIndex,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.embeddings = embeddings
        self.search_index = search_index

    async def ingest(
        self,
        *,
        context: CurrentContext,
        knowledge_base_id: UUID,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> Document:
        settings = get_settings()

        if len(content) > settings.helix_document_max_bytes:
            raise AppError(
                status_code=413,
                code="DOCUMENT_TOO_LARGE",
                message=(
                    f"Document exceeds the Sprint 4 limit of "
                    f"{settings.helix_document_max_bytes} bytes"
                ),
            )

        await KnowledgeService(self.repository).get_owned(
            context=context,
            knowledge_base_id=knowledge_base_id,
        )

        document = await self.repository.create_document(
            tenant_id=context.tenant_id,
            knowledge_base_id=knowledge_base_id,
            uploaded_by=context.user_id,
            filename=filename,
            content_type=content_type,
        )

        try:
            # Original bytes are stored independently from the search index. Search
            # is derived data and can therefore be rebuilt from owned documents.
            storage_path = await self.storage.save(
                tenant_id=context.tenant_id,
                document_id=document.id,
                filename=filename,
                content=content,
            )

            extracted = extract_text(filename=filename, content=content)
            text_chunks = chunk_text(
                extracted,
                chunk_size=settings.helix_chunk_size,
                overlap=settings.helix_chunk_overlap,
            )
            if not text_chunks:
                raise AppError(
                    status_code=422,
                    code="DOCUMENT_EMPTY",
                    message="The document did not produce any indexable chunks",
                )

            vectors = await self.embeddings.embed([chunk.text for chunk in text_chunks])
            if len(vectors) != len(text_chunks):
                raise RagProviderError("Embedding provider returned the wrong number of vectors")

            database_chunks = await self.repository.add_chunks(
                tenant_id=context.tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=document.id,
                contents=[chunk.text for chunk in text_chunks],
            )

            indexed_chunks = [
                IndexedChunk(
                    chunk_id=db_chunk.id,
                    tenant_id=context.tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    document_id=document.id,
                    filename=filename,
                    chunk_index=db_chunk.chunk_index,
                    content=db_chunk.content,
                    embedding=vector,
                )
                for db_chunk, vector in zip(database_chunks, vectors, strict=True)
            ]
            await self.search_index.index_chunks(indexed_chunks)

            await self.repository.mark_indexed(
                document=document,
                storage_path=storage_path,
                chunk_count=len(database_chunks),
            )
            return document

        except AppError as exc:
            # Persist a visible failed status before re-raising. Later sprints can
            # move ingestion to background workers with retry/outbox semantics.
            await self.repository.mark_failed(document=document, message=exc.message)
            await self.repository.session.commit()
            raise
        except Exception as exc:
            await self.repository.mark_failed(document=document, message=str(exc))
            await self.repository.session.commit()
            raise RagProviderError("Document ingestion failed") from exc


class KnowledgeRetrievalService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepository,
        embeddings: EmbeddingGateway,
        search_index: SearchIndex,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self.search_index = search_index

    async def retrieve(
        self,
        *,
        context: CurrentContext,
        knowledge_base_id: UUID,
        query: str,
        top_k: int | None,
    ) -> tuple[list[SearchHit], list[Citation]]:
        await KnowledgeService(self.repository).get_owned(
            context=context,
            knowledge_base_id=knowledge_base_id,
        )

        settings = get_settings()
        query_vector = (await self.embeddings.embed([query]))[0]
        hits = await self.search_index.search(
            tenant_id=context.tenant_id,
            knowledge_base_id=knowledge_base_id,
            query_embedding=query_vector,
            top_k=top_k or settings.helix_rag_top_k,
        )

        citations = [
            Citation(
                number=index,
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                filename=hit.filename,
                chunk_index=hit.chunk_index,
                score=hit.score,
                excerpt=hit.content[:500],
            )
            for index, hit in enumerate(hits, start=1)
        ]
        return hits, citations

    async def search(
        self,
        *,
        context: CurrentContext,
        knowledge_base_id: UUID,
        query: str,
        top_k: int | None,
    ) -> KnowledgeSearchResponse:
        _, citations = await self.retrieve(
            context=context,
            knowledge_base_id=knowledge_base_id,
            query=query,
            top_k=top_k,
        )
        return KnowledgeSearchResponse(query=query, citations=citations)


class RagAnswerService:
    """Explicit retrieve-then-generate flow; no agent framework is involved."""

    def __init__(
        self,
        *,
        retrieval: KnowledgeRetrievalService,
        model: ModelGateway,
    ) -> None:
        self.retrieval = retrieval
        self.model = model

    async def answer(
        self,
        *,
        context: CurrentContext,
        knowledge_base_id: UUID,
        question: str,
        top_k: int | None,
    ) -> RagAnswerResponse:
        hits, citations = await self.retrieval.retrieve(
            context=context,
            knowledge_base_id=knowledge_base_id,
            query=question,
            top_k=top_k,
        )

        if not hits:
            return RagAnswerResponse(
                answer="The available knowledge base does not contain relevant evidence.",
                citations=[],
                model=None,
            )

        source_blocks = "\n\n".join(
            f"[{index}] {hit.filename} (chunk {hit.chunk_index})\n{hit.content}"
            for index, hit in enumerate(hits, start=1)
        )
        user_prompt = f"Question:\n{question}\n\nSources:\n{source_blocks}"

        response = await self.model.generate(
            messages=[
                ModelMessage(role="system", content=RAG_SYSTEM_PROMPT),
                ModelMessage(role="user", content=user_prompt),
            ]
        )

        return RagAnswerResponse(
            answer=response.text,
            citations=citations,
            model=ModelMetadata(
                model=response.model,
                response_id=response.response_id,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                latency_ms=response.latency_ms,
            ),
        )
