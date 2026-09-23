from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helix_api.modules.knowledge.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    KnowledgeBase,
)


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_knowledge_base(
        self,
        *,
        tenant_id: UUID,
        name: str,
        description: str | None,
    ) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(
            tenant_id=tenant_id,
            name=name,
            description=description,
        )
        self.session.add(knowledge_base)
        await self.session.flush()
        await self.session.refresh(knowledge_base)
        return knowledge_base

    async def list_knowledge_bases(self, *, tenant_id: UUID) -> list[KnowledgeBase]:
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == tenant_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_knowledge_base(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> KnowledgeBase | None:
        result = await self.session.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_document(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        uploaded_by: UUID,
        filename: str,
        content_type: str | None,
    ) -> Document:
        document = Document(
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            uploaded_by=uploaded_by,
            filename=filename,
            content_type=content_type,
            status=DocumentStatus.PROCESSING,
        )
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def add_chunks(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        document_id: UUID,
        contents: list[str],
    ) -> list[DocumentChunk]:
        chunks = [
            DocumentChunk(
                tenant_id=tenant_id,
                knowledge_base_id=knowledge_base_id,
                document_id=document_id,
                chunk_index=index,
                content=content,
            )
            for index, content in enumerate(contents)
        ]
        self.session.add_all(chunks)
        await self.session.flush()
        return chunks

    async def mark_indexed(
        self,
        *,
        document: Document,
        storage_path: str,
        chunk_count: int,
    ) -> None:
        document.storage_path = storage_path
        document.chunk_count = chunk_count
        document.status = DocumentStatus.INDEXED
        document.error_message = None
        document.indexed_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_failed(self, *, document: Document, message: str) -> None:
        document.status = DocumentStatus.FAILED
        document.error_message = message[:2000]
        await self.session.flush()

    async def list_documents(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(
                Document.tenant_id == tenant_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())
