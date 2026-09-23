from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from helix_api.ai.factory import get_model_gateway
from helix_api.modules.auth.dependencies import CurrentContextDependency, SessionDependency
from helix_api.modules.knowledge.repository import KnowledgeRepository
from helix_api.modules.knowledge.schemas import (
    DocumentRead,
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    RagAnswerRequest,
    RagAnswerResponse,
)
from helix_api.modules.knowledge.service import (
    KnowledgeIngestionService,
    KnowledgeRetrievalService,
    KnowledgeService,
    RagAnswerService,
)
from helix_api.rag.factory import (
    get_document_storage,
    get_embedding_gateway,
    get_search_index,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge"])


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> KnowledgeBaseRead:
    knowledge_base = await KnowledgeService(KnowledgeRepository(session)).create(
        context=context,
        name=body.name,
        description=body.description,
    )
    return KnowledgeBaseRead.model_validate(knowledge_base)


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(
    context: CurrentContextDependency,
    session: SessionDependency,
) -> list[KnowledgeBaseRead]:
    items = await KnowledgeService(KnowledgeRepository(session)).list(context)
    return [KnowledgeBaseRead.model_validate(item) for item in items]


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: UUID,
    context: CurrentContextDependency,
    session: SessionDependency,
    file: UploadFile = File(...),
) -> DocumentRead:
    content = await file.read()

    document = await KnowledgeIngestionService(
        repository=KnowledgeRepository(session),
        storage=get_document_storage(),
        embeddings=get_embedding_gateway(),
        search_index=get_search_index(),
    ).ingest(
        context=context,
        knowledge_base_id=knowledge_base_id,
        filename=file.filename or "document",
        content_type=file.content_type,
        content=content,
    )
    return DocumentRead.model_validate(document)


@router.get("/{knowledge_base_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    knowledge_base_id: UUID,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> list[DocumentRead]:
    repository = KnowledgeRepository(session)
    await KnowledgeService(repository).get_owned(
        context=context,
        knowledge_base_id=knowledge_base_id,
    )
    documents = await repository.list_documents(
        tenant_id=context.tenant_id,
        knowledge_base_id=knowledge_base_id,
    )
    return [DocumentRead.model_validate(item) for item in documents]


def _retrieval_service(session: SessionDependency) -> KnowledgeRetrievalService:
    return KnowledgeRetrievalService(
        repository=KnowledgeRepository(session),
        embeddings=get_embedding_gateway(),
        search_index=get_search_index(),
    )


@router.post("/{knowledge_base_id}/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    knowledge_base_id: UUID,
    body: KnowledgeSearchRequest,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> KnowledgeSearchResponse:
    return await _retrieval_service(session).search(
        context=context,
        knowledge_base_id=knowledge_base_id,
        query=body.query,
        top_k=body.top_k,
    )


@router.post("/{knowledge_base_id}/answer", response_model=RagAnswerResponse)
async def answer_from_knowledge(
    knowledge_base_id: UUID,
    body: RagAnswerRequest,
    context: CurrentContextDependency,
    session: SessionDependency,
) -> RagAnswerResponse:
    return await RagAnswerService(
        retrieval=_retrieval_service(session),
        model=get_model_gateway(),
    ).answer(
        context=context,
        knowledge_base_id=knowledge_base_id,
        question=body.question,
        top_k=body.top_k,
    )
