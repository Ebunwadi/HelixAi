import asyncio
import json
import math
from pathlib import Path
from uuid import UUID

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex as AzureSearchIndexDefinition,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from helix_api.core.errors import RagProviderError
from helix_api.rag.types import IndexedChunk, SearchHit


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0

    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_size = math.sqrt(sum(value * value for value in left))
    right_size = math.sqrt(sum(value * value for value in right))

    if left_size == 0 or right_size == 0:
        return 0.0
    return numerator / (left_size * right_size)


class LocalSearchIndex:
    """Small persistent derived index used only for local development and CI."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = asyncio.Lock()

    def _read(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, rows: list[dict[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows), encoding="utf-8")

    async def index_chunks(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return

        document_ids = {str(chunk.document_id) for chunk in chunks}

        async with self._lock:
            rows = await asyncio.to_thread(self._read)

            # Re-indexing the same document replaces its old derived entries.
            rows = [
                row for row in rows if str(row.get("document_id")) not in document_ids
            ]
            rows.extend(
                {
                    "chunk_id": str(chunk.chunk_id),
                    "tenant_id": str(chunk.tenant_id),
                    "knowledge_base_id": str(chunk.knowledge_base_id),
                    "document_id": str(chunk.document_id),
                    "filename": chunk.filename,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                }
                for chunk in chunks
            )
            await asyncio.to_thread(self._write, rows)

    async def search(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        query_embedding: list[float],
        top_k: int,
    ) -> list[SearchHit]:
        async with self._lock:
            rows = await asyncio.to_thread(self._read)

        candidates: list[SearchHit] = []
        for row in rows:
            if row.get("tenant_id") != str(tenant_id):
                continue
            if row.get("knowledge_base_id") != str(knowledge_base_id):
                continue

            embedding = [float(value) for value in row["embedding"]]  # type: ignore[index]
            candidates.append(
                SearchHit(
                    chunk_id=UUID(str(row["chunk_id"])),
                    document_id=UUID(str(row["document_id"])),
                    filename=str(row["filename"]),
                    chunk_index=int(row["chunk_index"]),  # type: ignore[arg-type]
                    content=str(row["content"]),
                    score=_cosine(query_embedding, embedding),
                )
            )

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:top_k]


class AzureAISearchIndex:
    """Vector index adapter for Azure AI Search."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        index_name: str,
        dimensions: int,
    ) -> None:
        self.endpoint = endpoint
        self.credential = AzureKeyCredential(api_key)
        self.index_name = index_name
        self.dimensions = dimensions
        self._index_ready = False
        self._index_lock = asyncio.Lock()

    def _definition(self) -> AzureSearchIndexDefinition:
        fields = [
            SearchField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SearchField(
                name="tenant_id",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchField(
                name="knowledge_base_id",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchField(
                name="document_id",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchField(
                name="filename",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
            ),
            SearchField(
                name="chunk_index",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True,
            ),
            SearchField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self.dimensions,
                vector_search_profile_name="helix-vector-profile",
            ),
        ]

        return AzureSearchIndexDefinition(
            name=self.index_name,
            fields=fields,
            vector_search=VectorSearch(
                algorithms=[HnswAlgorithmConfiguration(name="helix-hnsw")],
                profiles=[
                    VectorSearchProfile(
                        name="helix-vector-profile",
                        algorithm_configuration_name="helix-hnsw",
                    )
                ],
            ),
        )

    async def _ensure_index(self) -> None:
        if self._index_ready:
            return

        async with self._index_lock:
            if self._index_ready:
                return

            # Index administration uses the synchronous management client only
            # during initial setup, so run it off the event loop.
            def create() -> None:
                client = SearchIndexClient(
                    endpoint=self.endpoint,
                    credential=self.credential,
                )
                client.create_or_update_index(self._definition())

            try:
                await asyncio.to_thread(create)
            except Exception as exc:
                raise RagProviderError("Azure AI Search index setup failed") from exc

            self._index_ready = True

    async def index_chunks(self, chunks: list[IndexedChunk]) -> None:
        if not chunks:
            return

        await self._ensure_index()
        documents = [
            {
                "id": str(chunk.chunk_id),
                "tenant_id": str(chunk.tenant_id),
                "knowledge_base_id": str(chunk.knowledge_base_id),
                "document_id": str(chunk.document_id),
                "filename": chunk.filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "content_vector": chunk.embedding,
            }
            for chunk in chunks
        ]

        try:
            async with SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=self.credential,
            ) as client:
                results = await client.upload_documents(documents=documents)
        except Exception as exc:
            raise RagProviderError("Azure AI Search indexing failed") from exc

        if not all(result.succeeded for result in results):
            raise RagProviderError("One or more chunks failed to index in Azure AI Search")

    async def search(
        self,
        *,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        query_embedding: list[float],
        top_k: int,
    ) -> list[SearchHit]:
        await self._ensure_index()

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="content_vector",
        )
        tenant_filter = (
            f"tenant_id eq '{tenant_id}' and "
            f"knowledge_base_id eq '{knowledge_base_id}'"
        )

        hits: list[SearchHit] = []
        try:
            async with SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=self.credential,
            ) as client:
                results = await client.search(
                    search_text=None,
                    vector_queries=[vector_query],
                    filter=tenant_filter,
                    top=top_k,
                    select=[
                        "id",
                        "document_id",
                        "filename",
                        "chunk_index",
                        "content",
                    ],
                )

                async for result in results:
                    hits.append(
                        SearchHit(
                            chunk_id=UUID(result["id"]),
                            document_id=UUID(result["document_id"]),
                            filename=result["filename"],
                            chunk_index=int(result["chunk_index"]),
                            content=result["content"],
                            score=float(result.get("@search.score", 0.0)),
                        )
                    )
        except Exception as exc:
            raise RagProviderError("Azure AI Search query failed") from exc

        return hits
